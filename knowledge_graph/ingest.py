"""
ingest.py — Idempotent knowledge-graph ingestion pipeline for TradeMate.

Run:
    cd knowledge_graph
    python ingest.py

All leaf-node steps use UNWIND batching (500 rows per transaction) to minimise
network round-trips to Neo4j Aura.  Re-running is safe — every write uses MERGE.
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
CSV_DIR = Path(__file__).parent / "data"

PCT_CSV        = CSV_DIR / "pct codes with hierarchy.csv"
TARIFFS_CSV    = CSV_DIR / "tariffs.csv"
CESS_CSV       = CSV_DIR / "cess_collection.csv"
EXEMPTIONS_CSV = CSV_DIR / "exemptions_concessions.csv"
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
    """Zero-pad HS Code to 12 digits (tariffs.csv strips the leading zero)."""
    s = clean(code)
    if s is None:
        return None
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
    """Send rows to Neo4j in chunks of NEO4J_BATCH using UNWIND."""
    total = len(rows)
    for start in tqdm(range(0, total, NEO4J_BATCH), desc=f"  {desc}", unit="batch"):
        batch = rows[start : start + NEO4J_BATCH]
        session.run(cypher, batch=batch)


# ---------------------------------------------------------------------------
# Step 1 – Hierarchy + embeddings
# ---------------------------------------------------------------------------

def _build_embedding_text(row: pd.Series) -> str:
    parts = [
        f"Chapter: {clean(row.get('Chapter Description')) or ''}",
        f"Sub-chapter: {clean(row.get('Sub Chapter Description')) or ''}",
        f"Heading: {clean(row.get('Heading Description')) or ''}",
        f"Sub-heading: {clean(row.get('Sub Heading Description')) or ''}",
        f"HS Code: {clean(row.get('Description')) or ''}",
        f"Full Code: {clean(row.get('HS Code')) or ''}",
    ]
    return "\n".join(parts)


_HIERARCHY_CYPHER = """
UNWIND $batch AS row
MERGE (ch:Chapter {code: row.chapter_code})
  ON CREATE SET ch.description = row.chapter_desc
  ON MATCH  SET ch.description = row.chapter_desc

MERGE (sc:SubChapter {code: row.subchapter_code})
  ON CREATE SET sc.description = row.subchapter_desc
  ON MATCH  SET sc.description = row.subchapter_desc

MERGE (hd:Heading {code: row.heading_code})
  ON CREATE SET hd.description = row.heading_desc
  ON MATCH  SET hd.description = row.heading_desc

MERGE (sh:SubHeading {code: row.subheading_code})
  ON CREATE SET sh.description = row.subheading_desc
  ON MATCH  SET sh.description = row.subheading_desc

MERGE (hs:HSCode {code: row.hs_code})
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

    texts = [_build_embedding_text(row) for _, row in df.iterrows()]

    logger.info("  Generating embeddings (batch=%d) …", EMBED_BATCH)
    all_embeddings: list[list[float]] = []
    for start in tqdm(range(0, len(texts), EMBED_BATCH), desc="  Embedding batches"):
        all_embeddings.extend(embeddings_model.embed_documents(texts[start : start + EMBED_BATCH]))

    # Build list of dicts for UNWIND
    rows: list[dict] = []
    for i, (_, row) in enumerate(df.iterrows()):
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            continue
        rows.append({
            "chapter_code":    clean(row.get("Chapter Code"))            or "UNKNOWN",
            "chapter_desc":    clean(row.get("Chapter Description"))     or "",
            "subchapter_code": clean(row.get("Sub Chapter Code"))        or "UNKNOWN",
            "subchapter_desc": clean(row.get("Sub Chapter Description")) or "",
            "heading_code":    clean(row.get("Heading Code"))            or "UNKNOWN",
            "heading_desc":    clean(row.get("Heading Description"))     or "",
            "subheading_code": clean(row.get("Sub Heading Code"))        or "UNKNOWN",
            "subheading_desc": clean(row.get("Sub Heading Description")) or "",
            "hs_code":         hs_code,
            "hs_desc":         clean(row.get("Description"))             or "",
            "full_label":      clean(row.get("Full Code"))               or "",
            "embedding":       all_embeddings[i],
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

_TARIFF_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode {code: row.hs_code})
MERGE (t:Tariff {uid: row.uid})
  ON CREATE SET t.hs_code    = row.hs_code,
                t.duty_type  = row.duty_type,
                t.duty_name  = row.duty_name,
                t.rate       = row.rate,
                t.valid_from = row.valid_from,
                t.valid_to   = row.valid_to
  ON MATCH  SET t.rate       = row.rate,
                t.valid_from = row.valid_from,
                t.valid_to   = row.valid_to
MERGE (hs)-[:HAS_TARIFF]->(t)
"""


def ingest_tariffs(driver) -> None:
    logger.info("═══ STEP 2a: Ingesting Tariffs ═══")
    df = load_csv(TARIFFS_CSV)
    logger.info("  Loaded %d rows from %s", len(df), TARIFFS_CSV.name)

    rows: list[dict] = []
    skipped = 0
    for _, row in df.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped += 1
            continue
        for prefix, duty_name in DUTY_TYPES.items():
            rate = clean(row.get(f"{prefix}_Rate"))
            if rate is None:
                continue
            valid_from = clean(row.get(f"{prefix}_ValidFrom"))
            rows.append({
                "uid":        make_uid(hs_code, prefix, rate, valid_from),
                "hs_code":    hs_code,
                "duty_type":  prefix,
                "duty_name":  duty_name,
                "rate":       rate,
                "valid_from": valid_from,
                "valid_to":   clean(row.get(f"{prefix}_ValidTo")),
            })

    logger.info("  Expanded to %d Tariff records (skipped %d rows with no HS code)", len(rows), skipped)
    with driver.session() as session:
        run_batched(session, _TARIFF_CYPHER, rows, "Tariff batches")
    logger.info("  Tariffs ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2b – Cess Collection
# ---------------------------------------------------------------------------

_CESS_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode {code: row.hs_code})
MERGE (c:Cess {uid: row.uid})
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

    rows: list[dict] = []
    skipped = 0
    for _, row in df.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped += 1
            continue
        province = clean(row.get("Province"))
        cess_desc = clean(row.get("Cess Description"))
        rows.append({
            "uid":              make_uid(hs_code, province, cess_desc),
            "hs_code":          hs_code,
            "province":         province,
            "cess_description": cess_desc,
            "import_rate":      clean(row.get("Import")),
            "export_rate":      clean(row.get("Export")),
            "forward_transit":  clean(row.get("Forward Transit")),
            "reverse_transit":  clean(row.get("Reverse Transit")),
        })

    logger.info("  %d Cess records (skipped %d)", len(rows), skipped)
    with driver.session() as session:
        run_batched(session, _CESS_CYPHER, rows, "Cess batches")
    logger.info("  Cess ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2c – Exemptions / Concessions
# ---------------------------------------------------------------------------

_EXEMPTION_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode {code: row.hs_code})
MERGE (e:Exemption {uid: row.uid})
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

    rows: list[dict] = []
    skipped = 0
    for _, row in df.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped += 1
            continue
        exemption_type = clean(row.get("Exemption/Concession"))
        activity       = clean(row.get("Activity"))
        rate           = clean(row.get("Rate"))
        rows.append({
            "uid":             make_uid(hs_code, exemption_type, activity, rate),
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

    logger.info("  %d Exemption records (skipped %d)", len(rows), skipped)
    with driver.session() as session:
        run_batched(session, _EXEMPTION_CYPHER, rows, "Exemption batches")
    logger.info("  Exemptions ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2d – Anti-Dumping Duties
# ---------------------------------------------------------------------------

_ANTIDUMP_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode {code: row.hs_code})
MERGE (a:AntiDumpingDuty {uid: row.uid})
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

    # antidump CSV has two columns both named "Description" — rename them
    raw = load_csv(ANTIDUMP_CSV)
    cols = list(raw.columns)
    desc_idx = [i for i, c in enumerate(cols) if c == "Description"]
    if len(desc_idx) >= 2:
        cols[desc_idx[0]] = "item_description"
        cols[desc_idx[1]] = "exporter"
    raw.columns = cols

    logger.info("  Loaded %d rows from %s", len(raw), ANTIDUMP_CSV.name)

    rows: list[dict] = []
    skipped = 0
    for _, row in raw.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped += 1
            continue
        exporter = clean(row.get("exporter"))
        rate     = clean(row.get("Rate"))
        rows.append({
            "uid":        make_uid(hs_code, exporter, rate),
            "hs_code":    hs_code,
            "exporter":   exporter,
            "rate":       rate,
            "valid_from": clean(row.get("Valid From")),
            "valid_to":   clean(row.get("Valid To")),
        })

    logger.info("  %d Anti-dumping records (skipped %d)", len(rows), skipped)
    with driver.session() as session:
        run_batched(session, _ANTIDUMP_CYPHER, rows, "Anti-dump batches")
    logger.info("  Anti-dumping ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2e – Procedures
# ---------------------------------------------------------------------------

_PROCEDURE_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode {code: row.hs_code})
MERGE (p:Procedure {uid: row.uid})
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

    rows: list[dict] = []
    skipped = 0
    for _, row in df.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped += 1
            continue
        name     = clean(row.get("Name"))
        category = clean(row.get("Category"))
        rows.append({
            "uid":         make_uid(hs_code, name, category),
            "hs_code":     hs_code,
            "name":        name,
            "description": clean(row.get("Procedure Description")),
            "category":    category,
            "url":         clean(row.get("Procedure URL")),
        })

    logger.info("  %d Procedure records (skipped %d)", len(rows), skipped)
    with driver.session() as session:
        run_batched(session, _PROCEDURE_CYPHER, rows, "Procedure batches")
    logger.info("  Procedures ingestion complete.")


# ---------------------------------------------------------------------------
# Step 2f – Measures
# ---------------------------------------------------------------------------

_MEASURE_CYPHER = """
UNWIND $batch AS row
MATCH (hs:HSCode {code: row.hs_code})
MERGE (m:Measure {uid: row.uid})
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

    rows: list[dict] = []
    skipped = 0
    for _, row in df.iterrows():
        hs_code = normalize_hs(row.get("HS Code"))
        if not hs_code:
            skipped += 1
            continue
        name   = clean(row.get("Name"))
        m_type = clean(row.get("Type"))
        rows.append({
            "uid":         make_uid(hs_code, name, m_type),
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

    logger.info("  %d Measure records (skipped %d)", len(rows), skipped)
    with driver.session() as session:
        run_batched(session, _MEASURE_CYPHER, rows, "Measure batches")
    logger.info("  Measures ingestion complete.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("╔══════════════════════════════════════════════════════╗")
    logger.info("║  TradeMate Knowledge Graph — Ingestion Pipeline      ║")
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
