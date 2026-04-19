"""
ingest_us.py — Idempotent US HTS knowledge-graph ingestion pipeline for TradeMate.

Execution order (memory-first — no Neo4j writes until everything is ready):
  1. Parse ALL CSV files in data/US-HTS/ → build nodes_list + relationships_list
  2. Generate ALL OpenAI embeddings in memory
  3. Create Neo4j constraint (idempotent)
  4. Batch-write nodes  (UNWIND, 1 000 rows/tx)
  5. Batch-write relationships (UNWIND, 1 000 rows/tx)

Run:
    cd knowledge_graph
    python ingest_us.py
"""

import glob
import hashlib
import logging
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm

from db_utils import get_driver, get_embeddings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HTS_DIR = Path(__file__).parent / "data/US-HTS"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMBED_BATCH = 50    # rows per OpenAI API call
NEO4J_BATCH = 1000   # rows per Neo4j UNWIND transaction

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean(val: Any) -> str | None:
    """Return None for NaN / blank / sentinel values; strip whitespace otherwise."""
    if val is None:
        return None
    if isinstance(val, float):
        return None if math.isnan(val) else str(val).strip()
    s = str(val).strip()
    return None if s in ("", "nan", "NaN", "None", "#NAME?", "N/A") else s


def normalize_hts(raw: Any) -> str | None:
    """
    Return a clean HTS string or None.

    Handles two common CSV artefacts:
      • Pandas read the code as a float  → "101.0"   should be "0101"
      • Leading zero was stripped in CSV → "101.21"  should be "0101.21"

    HTS codes always begin with a 4-digit chapter code (0001-9999).
    If the first dot-segment is fewer than 4 characters we left-zero-pad it.
    """
    s = clean(raw)
    if s is None:
        return None

    # Strip trailing ".0" that appears when pandas reads an integer as float
    if s.endswith(".0") and s.count(".") == 1:
        s = s[:-2]

    parts = s.split(".")
    if len(parts[0]) < 4:
        parts[0] = parts[0].zfill(4)

    return ".".join(parts)


def make_uid(*parts: Any) -> str:
    """Stable SHA-256 uid — guarantees MERGE idempotency across reruns."""
    combined = "|".join(str(p) for p in parts if p is not None)
    return hashlib.sha256(combined.encode()).hexdigest()


def load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV trying UTF-8 → cp1252 → latin-1 (handles Excel exports)."""
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(path, dtype=str, encoding=enc)
            df.columns = [c.strip() for c in df.columns]
            # Drop unnamed columns (artefact of Excel exports)
            df = df.loc[:, ~df.columns.str.fullmatch(r"Unnamed.*")]
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode {path.name} with utf-8 / cp1252 / latin-1")


# ---------------------------------------------------------------------------
# Step 1 — Parse all CSVs into memory
# ---------------------------------------------------------------------------

def parse_all_csvs() -> tuple[list[dict], list[dict]]:
    """
    Read every CSV in HTS_DIR sequentially and build:
      • nodes_list        – one dict per HTS row
      • relationships_list – one dict per parent→child edge

    The indent-based stack is reset at each file boundary because every file
    is an independent chapter that starts at indent 0.
    """
    csv_files = sorted(glob.glob(str(HTS_DIR / "*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {HTS_DIR}")

    logger.info("Found %d CSV files in %s", len(csv_files), HTS_DIR)

    nodes_list: list[dict] = []
    relationships_list: list[dict] = []

    for csv_path in tqdm(csv_files, desc="  Parsing CSV files", unit="file"):
        df = load_csv(Path(csv_path))

        # Gracefully handle missing expected columns
        for col in ("HTS Number", "Indent", "Description", "Unit of Quantity",
                    "General Rate of Duty", "Special Rate of Duty",
                    "Column 2 Rate of Duty"):
            if col not in df.columns:
                df[col] = None

        # Per-file state: reset at each chapter boundary
        # stack[indent]      → uid of most recent node at that depth
        # path_descs[indent] → description of most recent node at that depth
        stack: dict[int, str] = {}
        path_descs: dict[int, str] = {}

        for _, row in df.iterrows():
            # -- Indent -------------------------------------------------------
            raw_indent = clean(row.get("Indent"))
            try:
                indent = int(float(raw_indent)) if raw_indent is not None else 0
            except (ValueError, TypeError):
                indent = 0

            # -- Description --------------------------------------------------
            description = clean(row.get("Description")) or ""

            # -- HTS code (normalize to guard against stripped leading zeros) -
            hts_code = normalize_hts(row.get("HTS Number"))

            # -- Parent uid ---------------------------------------------------
            parent_uid: str | None = stack.get(indent - 1) if indent > 0 else None

            # -- Deterministic uid --------------------------------------------
            if hts_code:
                uid = make_uid("US", hts_code)
            else:
                uid = make_uid("US", str(parent_uid) if parent_uid else "ROOT", description)

            # -- Full path description (ancestors → self) ---------------------
            path_descs[indent] = description
            # Prune stale deeper entries
            for k in list(path_descs.keys()):
                if k > indent:
                    del path_descs[k]
            full_path = ": ".join(
                path_descs[i] for i in range(indent + 1) if i in path_descs
            )

            # -- Update stack -------------------------------------------------
            stack[indent] = uid
            for k in list(stack.keys()):
                if k > indent:
                    del stack[k]

            # -- Collect node -------------------------------------------------
            nodes_list.append({
                "uid":                  uid,
                "hts_code":             hts_code,
                "indent":               indent,
                "description":          description,
                "full_path_description": full_path,
                "unit":                 clean(row.get("Unit of Quantity")),
                "general_rate":         clean(row.get("General Rate of Duty")),
                "special_rate":         clean(row.get("Special Rate of Duty")),
                "column_2_rate":        clean(row.get("Column 2 Rate of Duty")),
                "embedding":            None,  # filled in Step 2
            })

            # -- Collect relationship ------------------------------------------
            if parent_uid is not None:
                relationships_list.append({
                    "parent_uid": parent_uid,
                    "child_uid":  uid,
                })

    logger.info(
        "  Parsed %d nodes and %d relationships from %d files (before dedup).",
        len(nodes_list), len(relationships_list), len(csv_files),
    )

    # Deduplicate nodes by uid — the source files overlap on some chapters.
    # Last occurrence wins (all fields are identical for true duplicates).
    seen_uids: dict[str, dict] = {}
    for node in nodes_list:
        seen_uids[node["uid"]] = node
    nodes_list = list(seen_uids.values())

    # Deduplicate relationships by (parent_uid, child_uid) pair.
    seen_rels: set[tuple[str, str]] = set()
    unique_rels: list[dict] = []
    for rel in relationships_list:
        key = (rel["parent_uid"], rel["child_uid"])
        if key not in seen_rels:
            seen_rels.add(key)
            unique_rels.append(rel)
    relationships_list = unique_rels

    logger.info(
        "  After dedup: %d unique nodes, %d unique relationships.",
        len(nodes_list), len(relationships_list),
    )
    return nodes_list, relationships_list


# ---------------------------------------------------------------------------
# Step 2 — Generate embeddings (entirely in memory)
# ---------------------------------------------------------------------------

def generate_embeddings(nodes_list: list[dict], embeddings_model) -> None:
    """
    Compute text-embedding-3-small vectors for every node and store them
    back in-place under nodes_list[i]["embedding"].
    """
    texts = [n["full_path_description"] or n["description"] or "" for n in nodes_list]
    total = len(texts)
    logger.info("  Generating embeddings for %d nodes (batch=%d) …", total, EMBED_BATCH)

    all_embeddings: list[list[float]] = []
    for start in tqdm(range(0, total, EMBED_BATCH), desc="  Embedding batches", unit="batch"):
        batch_texts = texts[start: start + EMBED_BATCH]
        all_embeddings.extend(embeddings_model.embed_documents(batch_texts))

    for node, emb in zip(nodes_list, all_embeddings):
        node["embedding"] = emb

    logger.info("  Embeddings complete.")


# ---------------------------------------------------------------------------
# Step 3 — Neo4j: constraint + node insertion
# ---------------------------------------------------------------------------

_US_CONSTRAINT = "CREATE CONSTRAINT ON (n:US) ASSERT n.uid IS UNIQUE;"

_NODE_CYPHER = """
UNWIND $batch AS row
MERGE (n:HSCode:US {uid: row.uid})
ON CREATE SET n.hts_code             = row.hts_code,
              n.indent               = row.indent,
              n.description          = row.description,
              n.full_path_description = row.full_path_description,
              n.unit                 = row.unit,
              n.general_rate         = row.general_rate,
              n.special_rate         = row.special_rate,
              n.column_2_rate        = row.column_2_rate,
              n.embedding            = row.embedding
ON MATCH  SET n.hts_code             = row.hts_code,
              n.description          = row.description,
              n.full_path_description = row.full_path_description,
              n.unit                 = row.unit,
              n.general_rate         = row.general_rate,
              n.special_rate         = row.special_rate,
              n.column_2_rate        = row.column_2_rate,
              n.embedding            = row.embedding
"""

_REL_CYPHER = """
UNWIND $batch AS row
MATCH (p:HSCode:US {uid: row.parent_uid})
MATCH (c:HSCode:US {uid: row.child_uid})
MERGE (p)-[:HAS_CHILD]->(c)
"""


def create_us_constraints(driver) -> None:
    """Create the US-specific uniqueness constraint (idempotent)."""
    with driver.session() as session:
        try:
            session.run(_US_CONSTRAINT)
        except Exception as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"Constraint issue: {e}")
    logger.info("  US constraint verified / created.")


def insert_nodes(driver, nodes_list: list[dict]) -> None:
    total = len(nodes_list)
    logger.info("  Writing %d nodes to Neo4j (batch=%d) …", total, NEO4J_BATCH)
    with driver.session() as session:
        for start in tqdm(range(0, total, NEO4J_BATCH), desc="  Node batches", unit="batch"):
            session.run(_NODE_CYPHER, batch=nodes_list[start: start + NEO4J_BATCH])
    logger.info("  Node insertion complete.")


def insert_relationships(driver, relationships_list: list[dict]) -> None:
    total = len(relationships_list)
    logger.info("  Writing %d relationships to Neo4j (batch=%d) …", total, NEO4J_BATCH)
    with driver.session() as session:
        for start in tqdm(range(0, total, NEO4J_BATCH), desc="  Relationship batches", unit="batch"):
            session.run(_REL_CYPHER, batch=relationships_list[start: start + NEO4J_BATCH])
    logger.info("  Relationship insertion complete.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("╔══════════════════════════════════════════════════════╗")
    logger.info("║  TradeMate Knowledge Graph — US HTS Ingestion        ║")
    logger.info("╚══════════════════════════════════════════════════════╝")

    # ── Phase 1: Parse (no network calls) ───────────────────────────────────
    logger.info("=== PHASE 1: Parsing CSV files ===")
    nodes_list, relationships_list = parse_all_csvs()

    # ── Phase 2: Embed (OpenAI only — no Neo4j yet) ─────────────────────────
    logger.info("=== PHASE 2: Generating embeddings ===")
    embeddings_model = get_embeddings()
    generate_embeddings(nodes_list, embeddings_model)

    # ── Phase 3-5: Neo4j writes (only after all data is ready in memory) ────
    logger.info("=== PHASE 3: Writing to Neo4j ===")
    driver = get_driver()
    try:
        create_us_constraints(driver)
        insert_nodes(driver, nodes_list)
        insert_relationships(driver, relationships_list)
    finally:
        driver.close()
        logger.info("Neo4j driver closed.")

    logger.info("╔══════════════════════════════════════════════════════╗")
    logger.info("║  US HTS ingestion complete!                          ║")
    logger.info("╚══════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
