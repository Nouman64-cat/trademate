"""
ingest_pk.py — Idempotent knowledge-graph ingestion pipeline for TradeMate.
             Every node is created with an additional :PK label.

Run:
    cd knowledge_graph
    python ingest_pk.py

All leaf-node steps use UNWIND batching (500 rows per transaction) to minimise
network round-trips.  Re-running is safe — every write uses MERGE.

Checkpointer (crash-resume)
───────────────────────────
On startup each step queries the live DB for its node type's existing IDs and
builds an O(1) lookup set.  Any row whose UID / HS code is already present is
skipped before embeddings are generated or any DB writes are attempted.
"""

import hashlib
import logging
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm

from db_utils import create_constraints, get_driver, get_embeddings

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
# Try a sequence of likely locations; the first one that exists wins. The
# scrapper drops fresh CSVs under tipp_scrapping/data/data/PK-PCT/, so we
# fall through to that when no local copy exists under knowledge_graph/.
_CSV_CANDIDATES = [
    Path(__file__).parent / "data/PK-PCT",
    Path(__file__).parent.parent / "tipp_scrapping/data/PK-PCT",
]
CSV_DIR = next((p for p in _CSV_CANDIDATES if p.exists()), _CSV_CANDIDATES[0])

PCT_CSV        = CSV_DIR / "pct codes with hierarchy.csv"
TARIFFS_CSV    = CSV_DIR / "combined_tariffs.csv"
CESS_CSV       = CSV_DIR / "cess_collection.csv"
EXEMPTIONS_CSV = CSV_DIR / "exemption_concessions.csv"
ANTIDUMP_CSV   = CSV_DIR / "anti_dump_tariffs.csv"
PROCEDURES_CSV = CSV_DIR / "procedures.csv"
MEASURES_CSV   = CSV_DIR / "measures.csv"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMBED_BATCH   = 50   # rows sent to OpenAI per API call
NEO4J_BATCH   = 500  # rows sent to Neo4j per UNWIND transaction

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean(val: Any) -> Any:
    """Convert NaN / '#NAME?' / 'N/A' to None; strip whitespace from strings."""
    if val is None:
        return None
    if isinstance(val, float):
        return None if math.isnan(val) else val
    s = str(val).strip()
    return None if s in ("", "nan", "NaN", "None", "#NAME?", "N/A") else s


def make_uid(*parts: Any) -> str:
    """Stable SHA-256 uid from arbitrary parts — guarantees MERGE idempotency."""
    combined = "|".join(str(p) for p in parts if p is not None)
    return hashlib.sha256(combined.encode()).hexdigest()


def normalize_hs(code: Any) -> str | None:
    """Recover an HS Code value from a CSV cell, returning a 12-digit string.

    Handles three real corruption modes seen in the source CSVs:

    1. Plain digit strings, possibly missing the leading zero on a 1-digit
       chapter (`10121000000` → `010121000000`). Zero-pad to 12.
    2. Excel scientific notation (`1.2019E+11` for codes ≥ 10 trillion).
       The HS Code column wasn't formatted as text, so Excel coerced long
       integers into floats. Parse the float, cast back to int, zero-pad.
       IEEE 754 doubles keep ~15 sig digits, so 12-digit codes round-trip;
       any digits beyond ~13 may have been silently truncated upstream and
       are unrecoverable from this representation alone.
    3. NaN/empty/error markers like `#NAME?` — return None.
    """
    s = clean(code)
    if s is None:
        return None
    # Scientific notation must be parsed as a float; stripping non-digits
    # would glue the mantissa onto the exponent and produce garbage.
    if "E" in s.upper():
        try:
            return str(int(float(s))).zfill(12)
        except (ValueError, OverflowError):
            pass
    digits = "".join(c for c in s if c.isdigit())
    return digits.zfill(12) if digits else None


def load_csv(path: Path, **kwargs) -> pd.DataFrame:
    """Load CSV trying UTF-8 then Windows-1252 (common for Excel exports)."""
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(path, dtype=str, encoding=enc, **kwargs)
            df.columns = [c.strip() for c in df.columns]
            df = df.loc[:, ~df.columns.str.fullmatch(r"Unnamed.*")]
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode {path.name} with utf-8 / cp1252 / latin-1")


def run_batched(session, cypher: str, rows: list[dict], desc: str) -> None:
    """Send rows to Neo4j/Memgraph in chunks of NEO4J_BATCH using UNWIND.

    Retries each batch on:
    - TransientError / ServiceUnavailable: optimistic-concurrency or network
      hiccups (e.g. the chat agent reading these nodes during ingest).
    - ClientError "unique constraint violation": when a previous transaction
      partially committed before being rolled back by a concurrent conflict,
      the retry sees its own earlier writes as duplicates. Our UIDs are
      deterministic (SHA-256 of stable fields), so a duplicate is by definition
      identical content — safe to treat as already-done.

    On unique-constraint conflicts we re-issue the batch with smaller chunks
    so a single offending row can't drag down the rest. After the retry budget
    is exhausted, the original error propagates so the run fails loudly rather
    than silently dropping data.
    """
    import time
    from neo4j.exceptions import TransientError, ServiceUnavailable, ClientError

    def _is_dup_constraint(exc: Exception) -> bool:
        msg = str(exc).lower()
        return "unique constraint" in msg or "already exists" in msg

    def _send(batch: list[dict], depth: int = 0) -> None:
        delay = 1.0
        for attempt in range(6):
            try:
                session.run(cypher, batch=batch)
                return
            except (TransientError, ServiceUnavailable) as exc:
                if attempt == 5:
                    logger.error("  Batch (size=%d) failed after 6 attempts: %s",
                                 len(batch), exc)
                    raise
                logger.warning("  Batch (size=%d) transient error (attempt %d/6): %s — retrying in %.1fs",
                               len(batch), attempt + 1, exc, delay)
                time.sleep(delay)
                delay = min(delay * 2, 30)
            except ClientError as exc:
                if not _is_dup_constraint(exc):
                    raise
                # Unique-constraint violation — most rows are fine, one is a
                # dup. Halve the batch and retry both halves so the conflict
                # is isolated. At depth 5 (size ≈ batch/32) give up: the dup
                # row is by definition identical content from a partial
                # earlier commit, so swallowing it is safe.
                if len(batch) <= 1 or depth >= 5:
                    logger.warning("  Skipping duplicate row(s) (size=%d, depth=%d): %s",
                                   len(batch), depth, str(exc)[:120])
                    return
                mid = len(batch) // 2
                _send(batch[:mid], depth + 1)
                _send(batch[mid:], depth + 1)
                return

    total = len(rows)
    for start in tqdm(range(0, total, NEO4J_BATCH), desc=f"  {desc}", unit="batch"):
        _send(rows[start : start + NEO4J_BATCH])


# ---------------------------------------------------------------------------
# Checkpointer
# ---------------------------------------------------------------------------

def load_checkpoint(driver, label: str, id_field: str) -> set[str]:
    """
    Query the DB and return the set of all existing ``id_field`` values for
    nodes with the given label.  Returns an empty set on any error so the
    pipeline degrades to a full re-run rather than crashing.
    """
    try:
        with driver.session() as session:
            result = session.run(
                f"MATCH (n:{label}) WHERE n.{id_field} IS NOT NULL "
                f"RETURN n.{id_field} AS id"
            )
            ids: set[str] = {record["id"] for record in result}
        logger.info(
            "  Checkpointer [%s.%s]: %d existing record(s) found in DB.",
            label, id_field, len(ids),
        )
        return ids
    except Exception as exc:
        logger.warning(
            "  Checkpointer query failed for [%s.%s] — proceeding without "
            "checkpoint (full re-run). Error: %s",
            label, id_field, exc,
        )
        return set()


# ---------------------------------------------------------------------------
# Step 1 – Hierarchy + embeddings
# ---------------------------------------------------------------------------

def _build_embedding_text(row: pd.Series) -> str:
    parts = [
        f"Chapter: {clean(row.get('Chapter')) or ''}",
        f"Sub-chapter: {clean(row.get('Sub Chapter')) or ''}",
        f"Heading: {clean(row.get('Heading')) or ''}",
        f"Sub-heading: {clean(row.get('Sub Heading')) or ''}",
        f"HS Code: {clean(row.get('Description')) or ''}",
        f"Full Code: {clean(row.get('HS Code')) or ''}",
    ]
    return "\n".join(parts)


_HIERARCHY_CYPHER = """
UNWIND $batch AS row
MERGE (ch:Chapter:PK {code: row.chapter_code})
  ON CREATE SET ch.description = row.chapter_desc
  ON MATCH  SET ch.description = row.chapter_desc

MERGE (sc:SubChapter:PK {code: row.subchapter_code})
  ON CREATE SET sc.description = row.subchapter_desc
  ON MATCH  SET sc.description = row.subchapter_desc

MERGE (hd:Heading:PK {code: row.heading_code})
  ON CREATE SET hd.description = row.heading_desc
  ON MATCH  SET hd.description = row.heading_desc

MERGE (sh:SubHeading:PK {code: row.subheading_code})
  ON CREATE SET sh.description = row.subheading_desc
  ON MATCH  SET sh.description = row.subheading_desc

MERGE (hs:HSCode:PK {code: row.hs_code})
  ON CREATE SET hs.description = row.hs_desc,
                hs.full_label  = row.full_label,
                hs.embedding   = row.embedding
  ON MATCH  SET hs.description = row.hs_desc,
                hs.full_label  = row.full_label,
                hs.embedding   = row.embedding

MERGE (ch)-[:HAS_SUBCHAPTER]->(sc)
MERGE (sc)-[:HAS_HEADING]->(hd)
MERGE (hd)-[:HAS_SUBHEADING]->(sh)
MERGE (sh)-[:HAS_HSCODE]->(hs)
"""


def ingest_hierarchy(driver, embeddings_model) -> None:
    logger.info("═══ STEP 1: Ingesting PCT hierarchy + embeddings ═══")
    df = load_csv(PCT_CSV)
    logger.info("  Loaded %d rows from %s", len(df), PCT_CSV.name)

    # ── Checkpointer ────────────────────────────────────────────────────────
    existing_codes = load_checkpoint(driver, "HSCode:PK", "code")

    # Build a filtered list of (row, hs_code) for new entries only.
    # We must filter before building embedding texts so OpenAI is never called
    # for rows that are already in the DB.
    new_items: list[tuple[pd.Series, str]] = []
    skipped_ckpt = 0
    skipped_no_code = 0

    for _, row in df.iterrows():
        raw = str(row.get("HS Code") or "").strip()
        if not raw:
            skipped_no_code += 1
            continue
        # Skip non-leaf rows (chapter/heading/sub-heading level codes).
        # Only 12-digit codes are leaf HS codes; shorter codes are hierarchy
        # labels that must not become HSCode nodes.
        raw_digits = "".join(c for c in raw if c.isdigit())
        is_scientific = "E" in raw.upper() and "." in raw
        if not is_scientific and len(raw_digits) != 12:
            skipped_no_code += 1
            continue
        hs_code = normalize_hs(raw)
        if not hs_code:
            skipped_no_code += 1
            continue
        if hs_code in existing_codes:
            skipped_ckpt += 1
            continue
        new_items.append((row, hs_code))

    logger.info(
        "  Checkpointer: %d already in DB (skipped), %d missing HS code, "
        "%d new rows to embed and write.",
        skipped_ckpt, skipped_no_code, len(new_items),
    )

    if not new_items:
        logger.info("  All hierarchy rows already ingested — skipping step.")
        return

    # ── Embeddings (only for new rows) ──────────────────────────────────────
    texts = [_build_embedding_text(row) for row, _ in new_items]
    logger.info("  Generating embeddings for %d new rows (batch=%d) …", len(texts), EMBED_BATCH)

    all_embeddings: list[list[float]] = []
    for start in tqdm(range(0, len(texts), EMBED_BATCH), desc="  Embedding batches"):
        all_embeddings.extend(
            embeddings_model.embed_documents(texts[start : start + EMBED_BATCH])
        )

    # ── Build DB rows ────────────────────────────────────────────────────────
    rows: list[dict] = []
    for (row, hs_code), emb in zip(new_items, all_embeddings):
        rows.append({
            "chapter_code":    hs_code[:2],
            "chapter_desc":    clean(row.get("Chapter"))     or "",
            "subchapter_code": hs_code[:4],
            "subchapter_desc": clean(row.get("Sub Chapter")) or "",
            "heading_code":    hs_code[:6],
            "heading_desc":    clean(row.get("Heading"))     or "",
            "subheading_code": hs_code[:8],
            "subheading_desc": clean(row.get("Sub Heading")) or "",
            "hs_code":         hs_code,
            "hs_desc":         clean(row.get("Description")) or "",
            "full_label":      hs_code,
            "embedding":       emb,
        })

    logger.info("  Writing %d hierarchy rows to Neo4j (batch=%d) …", len(rows), NEO4J_BATCH)
    with driver.session() as session:
        run_batched(session, _HIERARCHY_CYPHER, rows, "Hierarchy batches")

    logger.info("  Hierarchy ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2a – Tariffs  (expand multi-duty rows before batching)
# ---------------------------------------------------------------------------

DUTY_TYPES = {
    "CD":       "Customs Duty",
    "RD":       "Regulatory Duty",
    "ACD":      "Additional Customs Duty",
    "FED":      "Federal Excise Duty",
    "ST (VAT)": "Sales Tax / VAT",
    "IT":       "Income Tax",
    "DS":       "Development Surcharge",
    "EOC":      "Export Obligatory Contribution",
    "ERD":      "Export Regulatory Duty",
}

# Three Cypher templates, one per hierarchy level a tariff can attach to.
# Excel rounded long HS codes into scientific notation (1.2019E+11) and lost
# the trailing digits; after recovery many of those land at SubHeading
# (8-digit) or Heading (6-digit) precision rather than the 12-digit leaf.
# The lookup query in agent/bot.py walks down from leaf to ancestor, so a
# Tariff attached at SubHeading is inherited by every HSCode under it.
#
# SubHeading/Heading codes in the hierarchy may include separators (`1201.90`
# in some sources), so we strip non-digits at compare time before equality.

_TARIFF_HSCODE_CYPHER = """
UNWIND $batch AS row
OPTIONAL MATCH (n:HSCode:PK {code: row.match_value})
WITH row, n WHERE n IS NOT NULL
MERGE (t:Tariff:PK {uid: row.uid})
  ON CREATE SET t.hs_code        = row.hs_code,
                t.duty_type      = row.duty_type,
                t.duty_name      = row.duty_name,
                t.rate           = row.rate,
                t.valid_from     = row.valid_from,
                t.valid_to       = row.valid_to,
                t.attached_level = row.attached_level
  ON MATCH  SET t.rate           = row.rate,
                t.valid_from     = row.valid_from,
                t.valid_to       = row.valid_to,
                t.attached_level = row.attached_level
MERGE (n)-[:HAS_TARIFF]->(t)
"""

_TARIFF_SUBHEADING_CYPHER = """
UNWIND $batch AS row
OPTIONAL MATCH (n:SubHeading:PK)
  WHERE replace(replace(replace(toString(n.code), '.', ''), '-', ''), ' ', '') = row.match_value
WITH row, n WHERE n IS NOT NULL
MERGE (t:Tariff:PK {uid: row.uid})
  ON CREATE SET t.hs_code        = row.hs_code,
                t.duty_type      = row.duty_type,
                t.duty_name      = row.duty_name,
                t.rate           = row.rate,
                t.valid_from     = row.valid_from,
                t.valid_to       = row.valid_to,
                t.attached_level = row.attached_level
  ON MATCH  SET t.rate           = row.rate,
                t.valid_from     = row.valid_from,
                t.valid_to       = row.valid_to,
                t.attached_level = row.attached_level
MERGE (n)-[:HAS_TARIFF]->(t)
"""

_TARIFF_HEADING_CYPHER = """
UNWIND $batch AS row
OPTIONAL MATCH (n:Heading:PK)
  WHERE replace(replace(replace(toString(n.code), '.', ''), '-', ''), ' ', '') = row.match_value
WITH row, n WHERE n IS NOT NULL
MERGE (t:Tariff:PK {uid: row.uid})
  ON CREATE SET t.hs_code        = row.hs_code,
                t.duty_type      = row.duty_type,
                t.duty_name      = row.duty_name,
                t.rate           = row.rate,
                t.valid_from     = row.valid_from,
                t.valid_to       = row.valid_to,
                t.attached_level = row.attached_level
  ON MATCH  SET t.rate           = row.rate,
                t.valid_from     = row.valid_from,
                t.valid_to       = row.valid_to,
                t.attached_level = row.attached_level
MERGE (n)-[:HAS_TARIFF]->(t)
"""


def _classify_tariff_target(hier_codes: dict, recovered: str) -> tuple[str, str, str] | None:
    """Pick the most-specific node level that exists in the hierarchy for a
    recovered 12-digit code. Returns (attached_level, match_value, hs_code_for_node)
    or None if no level matches.

    Recovery may have rounded trailing digits off (Excel sci-notation precision
    loss), so we check leaf → 8-digit subheading → 6-digit heading in that order
    and attach to the most-specific node that actually exists.
    """
    if recovered in hier_codes["hsc"]:
        return ("HSCode", recovered, recovered)
    if recovered[:8] in hier_codes["sh"]:
        return ("SubHeading", recovered[:8], recovered)
    if recovered[:6] in hier_codes["hd"]:
        return ("Heading", recovered[:6], recovered)
    return None


def _load_hierarchy_codes(driver) -> dict:
    """Pull the HSCode/SubHeading/Heading code sets currently in the graph so
    we can classify each tariff row against what actually exists."""
    out = {"hsc": set(), "sh": set(), "hd": set()}
    with driver.session() as session:
        for label, key in (("HSCode:PK", "hsc"),
                           ("SubHeading:PK", "sh"),
                           ("Heading:PK", "hd")):
            result = session.run(
                f"MATCH (n:{label}) WHERE n.code IS NOT NULL "
                f"RETURN replace(replace(replace(toString(n.code), '.', ''), '-', ''), ' ', '') AS c"
            )
            out[key] = {rec["c"] for rec in result if rec["c"]}
    logger.info(
        "  Hierarchy snapshot: %d HSCode, %d SubHeading, %d Heading nodes.",
        len(out["hsc"]), len(out["sh"]), len(out["hd"]),
    )
    return out


def ingest_tariffs(driver) -> None:
    logger.info("═══ STEP 2a: Ingesting Tariffs ═══")
    df = load_csv(TARIFFS_CSV)
    logger.info("  Loaded %d rows from %s", len(df), TARIFFS_CSV.name)

    existing_uids = load_checkpoint(driver, "Tariff:PK", "uid")
    hier_codes = _load_hierarchy_codes(driver)
    if not hier_codes["hsc"]:
        logger.warning(
            "  Hierarchy is empty — run ingest_hierarchy first; tariff "
            "attachment will be 0/0 until hierarchy nodes exist."
        )

    # Bucket each duty row by the most-specific level it can attach to.
    hsc_rows: list[dict] = []
    sh_rows:  list[dict] = []
    hd_rows:  list[dict] = []
    skipped_ckpt    = 0
    skipped_no_code = 0
    skipped_no_match = 0

    for _, row in df.iterrows():
        recovered = normalize_hs(row.get("HS Code"))
        if not recovered:
            skipped_no_code += 1
            continue

        target = _classify_tariff_target(hier_codes, recovered)
        if target is None:
            skipped_no_match += 1
            continue
        attached_level, match_value, hs_code_for_node = target
        bucket = {"HSCode": hsc_rows, "SubHeading": sh_rows, "Heading": hd_rows}[attached_level]

        for prefix, duty_name in DUTY_TYPES.items():
            rate = clean(row.get(f"{prefix}_Rate"))
            if rate is None:
                continue
            valid_from = clean(row.get(f"{prefix}_ValidFrom"))
            uid = make_uid(hs_code_for_node, prefix, rate, valid_from, attached_level)
            if uid in existing_uids:
                skipped_ckpt += 1
                continue
            bucket.append({
                "uid":            uid,
                "hs_code":        hs_code_for_node,
                "match_value":    match_value,
                "attached_level": attached_level,
                "duty_type":      prefix,
                "duty_name":      duty_name,
                "rate":           rate,
                "valid_from":     valid_from,
                "valid_to":       clean(row.get(f"{prefix}_ValidTo")),
            })

    total_new = len(hsc_rows) + len(sh_rows) + len(hd_rows)
    logger.info(
        "  Tariff plan: %d→HSCode, %d→SubHeading, %d→Heading "
        "(checkpointer skipped %d already-present, %d rows missing HS code, "
        "%d rows had no matching node at any level).",
        len(hsc_rows), len(sh_rows), len(hd_rows),
        skipped_ckpt, skipped_no_code, skipped_no_match,
    )
    if skipped_no_match:
        logger.warning(
            "━━━ [INGEST → PK] %d tariff rows had a recovered HS code that "
            "doesn't appear in the hierarchy as HSCode/SubHeading/Heading. "
            "These rows are dropped. Likely cause: scientific-notation "
            "precision loss truncated the code beyond what we can match.",
            skipped_no_match,
        )

    if not total_new:
        logger.info("  All tariff records already ingested — skipping step.")
        return

    with driver.session() as session:
        if hsc_rows:
            run_batched(session, _TARIFF_HSCODE_CYPHER, hsc_rows, "HSCode-level tariffs")
        if sh_rows:
            run_batched(session, _TARIFF_SUBHEADING_CYPHER, sh_rows, "SubHeading-level tariffs")
        if hd_rows:
            run_batched(session, _TARIFF_HEADING_CYPHER, hd_rows, "Heading-level tariffs")

    logger.info("  Tariffs ingestion complete: %d Tariff nodes created.", total_new)


# ---------------------------------------------------------------------------
# Step 2b – Cess Collection
# ---------------------------------------------------------------------------

_CESS_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode:PK {code: row.hs_code})
MERGE (c:Cess:PK {uid: row.uid})
  ON CREATE SET c.hs_code          = row.hs_code,
                c.province         = row.province,
                c.cess_description = row.cess_description,
                c.import_rate      = row.import_rate,
                c.export_rate      = row.export_rate,
                c.forward_transit  = row.forward_transit,
                c.reverse_transit  = row.reverse_transit
  ON MATCH  SET c.import_rate      = row.import_rate,
                c.export_rate      = row.export_rate,
                c.forward_transit  = row.forward_transit,
                c.reverse_transit  = row.reverse_transit
MERGE (hs)-[:HAS_CESS]->(c)
"""


def ingest_cess(driver) -> None:
    logger.info("═══ STEP 2b: Ingesting Cess Collection ═══")
    df = load_csv(CESS_CSV)
    logger.info("  Loaded %d rows from %s", len(df), CESS_CSV.name)

    existing_uids = load_checkpoint(driver, "Cess:PK", "uid")

    rows: list[dict] = []
    skipped_ckpt = 0
    skipped_no_code = 0

    for _, row in df.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped_no_code += 1
            continue
        province  = clean(row.get("Province"))
        cess_desc = clean(row.get("Cess Description"))
        uid = make_uid(hs_code, province, cess_desc)
        if uid in existing_uids:
            skipped_ckpt += 1
            continue
        rows.append({
            "uid":              uid,
            "hs_code":          hs_code,
            "province":         province,
            "cess_description": cess_desc,
            "import_rate":      clean(row.get("Import")),
            "export_rate":      clean(row.get("Export")),
            "forward_transit":  clean(row.get("Forward Transit")),
            "reverse_transit":  clean(row.get("Reverse Transit")),
        })

    logger.info(
        "  Checkpointer: %d already in DB (skipped), %d new Cess records "
        "(skipped %d rows with no HS code).",
        skipped_ckpt, len(rows), skipped_no_code,
    )

    if not rows:
        logger.info("  All cess records already ingested — skipping step.")
        return

    with driver.session() as session:
        run_batched(session, _CESS_CYPHER, rows, "Cess batches")
    logger.info("  Cess ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2c – Exemptions / Concessions
# ---------------------------------------------------------------------------

_EXEMPTION_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode:PK {code: row.hs_code})
MERGE (e:Exemption:PK {uid: row.uid})
  ON CREATE SET e.hs_code        = row.hs_code,
                e.exemption_type = row.exemption_type,
                e.exemption_desc = row.exemption_desc,
                e.reference      = row.reference,
                e.activity       = row.activity,
                e.rate           = row.rate,
                e.unit           = row.unit,
                e.valid_from     = row.valid_from,
                e.valid_to       = row.valid_to
  ON MATCH  SET e.exemption_desc = row.exemption_desc,
                e.rate           = row.rate,
                e.valid_from     = row.valid_from,
                e.valid_to       = row.valid_to
MERGE (hs)-[:HAS_EXEMPTION]->(e)
"""


def ingest_exemptions(driver) -> None:
    logger.info("═══ STEP 2c: Ingesting Exemptions / Concessions ═══")
    df = load_csv(EXEMPTIONS_CSV)
    logger.info("  Loaded %d rows from %s", len(df), EXEMPTIONS_CSV.name)

    existing_uids = load_checkpoint(driver, "Exemption:PK", "uid")

    rows: list[dict] = []
    skipped_ckpt = 0
    skipped_no_code = 0

    for _, row in df.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped_no_code += 1
            continue
        exemption_type = clean(row.get("Exemption/Concession"))
        activity       = clean(row.get("Activity"))
        rate           = clean(row.get("Rate"))
        uid = make_uid(hs_code, exemption_type, activity, rate)
        if uid in existing_uids:
            skipped_ckpt += 1
            continue
        rows.append({
            "uid":             uid,
            "hs_code":         hs_code,
            "exemption_type":  exemption_type,
            "exemption_desc":  clean(row.get("Exemption Description")),
            "reference":       clean(row.get("Reference")),
            "activity":        activity,
            "rate":            rate,
            "unit":            clean(row.get("Unit")),
            "valid_from":      clean(row.get("Valid From")),
            "valid_to":        clean(row.get("Valid To")),
        })

    logger.info(
        "  Checkpointer: %d already in DB (skipped), %d new Exemption records "
        "(skipped %d rows with no HS code).",
        skipped_ckpt, len(rows), skipped_no_code,
    )

    if not rows:
        logger.info("  All exemption records already ingested — skipping step.")
        return

    with driver.session() as session:
        run_batched(session, _EXEMPTION_CYPHER, rows, "Exemption batches")
    logger.info("  Exemptions ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2d – Anti-Dumping Duties
# ---------------------------------------------------------------------------

_ANTIDUMP_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode:PK {code: row.hs_code})
MERGE (a:AntiDumpingDuty:PK {uid: row.uid})
  ON CREATE SET a.hs_code    = row.hs_code,
                a.exporter   = row.exporter,
                a.rate       = row.rate,
                a.valid_from = row.valid_from,
                a.valid_to   = row.valid_to
  ON MATCH  SET a.exporter   = row.exporter,
                a.rate       = row.rate,
                a.valid_from = row.valid_from,
                a.valid_to   = row.valid_to
MERGE (hs)-[:HAS_ANTI_DUMPING]->(a)
"""


def ingest_antidump(driver) -> None:
    logger.info("═══ STEP 2d: Ingesting Anti-Dumping Duties ═══")

    raw = load_csv(ANTIDUMP_CSV)
    cols = list(raw.columns)
    desc_idx = [i for i, c in enumerate(cols) if c == "Description"]
    if len(desc_idx) >= 2:
        cols[desc_idx[0]] = "item_description"
        cols[desc_idx[1]] = "exporter"
    raw.columns = cols

    logger.info("  Loaded %d rows from %s", len(raw), ANTIDUMP_CSV.name)

    existing_uids = load_checkpoint(driver, "AntiDumpingDuty:PK", "uid")

    rows: list[dict] = []
    skipped_ckpt = 0
    skipped_no_code = 0

    for _, row in raw.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped_no_code += 1
            continue
        exporter = clean(row.get("exporter"))
        rate     = clean(row.get("Rate"))
        uid = make_uid(hs_code, exporter, rate)
        if uid in existing_uids:
            skipped_ckpt += 1
            continue
        rows.append({
            "uid":        uid,
            "hs_code":    hs_code,
            "exporter":   exporter,
            "rate":       rate,
            "valid_from": clean(row.get("Valid From")),
            "valid_to":   clean(row.get("Valid To")),
        })

    logger.info(
        "  Checkpointer: %d already in DB (skipped), %d new Anti-dumping records "
        "(skipped %d rows with no HS code).",
        skipped_ckpt, len(rows), skipped_no_code,
    )

    if not rows:
        logger.info("  All anti-dumping records already ingested — skipping step.")
        return

    with driver.session() as session:
        run_batched(session, _ANTIDUMP_CYPHER, rows, "Anti-dump batches")
    logger.info("  Anti-dumping ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2e – Procedures
# ---------------------------------------------------------------------------

_PROCEDURE_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode:PK {code: row.hs_code})
MERGE (p:Procedure:PK {uid: row.uid})
  ON CREATE SET p.hs_code     = row.hs_code,
                p.name        = row.name,
                p.description = row.description,
                p.category    = row.category,
                p.url         = row.url
  ON MATCH  SET p.description = row.description,
                p.category    = row.category,
                p.url         = row.url
MERGE (hs)-[:REQUIRES_PROCEDURE]->(p)
"""


def ingest_procedures(driver) -> None:
    logger.info("═══ STEP 2e: Ingesting Procedures ═══")
    df = load_csv(PROCEDURES_CSV)
    logger.info("  Loaded %d rows from %s", len(df), PROCEDURES_CSV.name)

    existing_uids = load_checkpoint(driver, "Procedure:PK", "uid")

    rows: list[dict] = []
    skipped_ckpt = 0
    skipped_no_code = 0

    for _, row in df.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped_no_code += 1
            continue
        name     = clean(row.get("Name"))
        category = clean(row.get("Category"))
        uid = make_uid(hs_code, name, category)
        if uid in existing_uids:
            skipped_ckpt += 1
            continue
        rows.append({
            "uid":         uid,
            "hs_code":     hs_code,
            "name":        name,
            "description": clean(row.get("Procedure Description")),
            "category":    category,
            "url":         clean(row.get("Procedure URL")),
        })

    logger.info(
        "  Checkpointer: %d already in DB (skipped), %d new Procedure records "
        "(skipped %d rows with no HS code).",
        skipped_ckpt, len(rows), skipped_no_code,
    )

    if not rows:
        logger.info("  All procedure records already ingested — skipping step.")
        return

    with driver.session() as session:
        run_batched(session, _PROCEDURE_CYPHER, rows, "Procedure batches")
    logger.info("  Procedures ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2f – Measures
# ---------------------------------------------------------------------------

_MEASURE_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode:PK {code: row.hs_code})
MERGE (m:Measure:PK {uid: row.uid})
  ON CREATE SET m.hs_code     = row.hs_code,
                m.name        = row.name,
                m.type        = row.type,
                m.agency      = row.agency,
                m.description = row.description,
                m.comments    = row.comments,
                m.law         = row.law,
                m.validity    = row.validity,
                m.url         = row.url
  ON MATCH  SET m.description = row.description,
                m.comments    = row.comments,
                m.law         = row.law,
                m.validity    = row.validity,
                m.url         = row.url
MERGE (hs)-[:HAS_MEASURE]->(m)
"""


def ingest_measures(driver) -> None:
    logger.info("═══ STEP 2f: Ingesting Measures ═══")
    df = load_csv(MEASURES_CSV)
    logger.info("  Loaded %d rows from %s", len(df), MEASURES_CSV.name)

    existing_uids = load_checkpoint(driver, "Measure:PK", "uid")

    rows: list[dict] = []
    skipped_ckpt = 0
    skipped_no_code = 0

    for _, row in df.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped_no_code += 1
            continue
        name   = clean(row.get("Name"))
        m_type = clean(row.get("Type"))
        uid = make_uid(hs_code, name, m_type)
        if uid in existing_uids:
            skipped_ckpt += 1
            continue
        rows.append({
            "uid":         uid,
            "hs_code":     hs_code,
            "name":        name,
            "type":        m_type,
            "agency":      clean(row.get("Agency")),
            "description": clean(row.get("Measure Description")),
            "comments":    clean(row.get("Comments")),
            "law":         clean(row.get("Law")),
            "validity":    clean(row.get("Validity")),
            "url":         clean(row.get("Measure URL")),
        })

    logger.info(
        "  Checkpointer: %d already in DB (skipped), %d new Measure records "
        "(skipped %d rows with no HS code).",
        skipped_ckpt, len(rows), skipped_no_code,
    )

    if not rows:
        logger.info("  All measure records already ingested — skipping step.")
        return

    with driver.session() as session:
        run_batched(session, _MEASURE_CYPHER, rows, "Measure batches")
    logger.info("  Measures ingestion complete.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("╔══════════════════════════════════════════════════════╗")
    logger.info("║  TradeMate Knowledge Graph — Ingestion Pipeline (PK) ║")
    logger.info("╚══════════════════════════════════════════════════════╝")

    driver = get_driver()
    embeddings_model = get_embeddings()

    try:
        create_constraints(driver)
        ingest_hierarchy(driver, embeddings_model)
        ingest_tariffs(driver)
        ingest_cess(driver)
        ingest_exemptions(driver)
        ingest_antidump(driver)
        ingest_procedures(driver)
        ingest_measures(driver)
    finally:
        driver.close()
        logger.info("Neo4j driver closed.")

    logger.info("╔══════════════════════════════════════════════════════╗")
    logger.info("║  Ingestion complete!                                 ║")
    logger.info("╚══════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
