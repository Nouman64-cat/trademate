"""
db_utils.py — Neo4j connection, OpenAI embedding model, and schema constraints.
"""
import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings

# Load .env from the knowledge_graph directory (same folder as this file)
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

logger = logging.getLogger(__name__)

# Read from MEMGRAPH_URI (Memgraph uses Neo4j-compatible Bolt protocol)
MEMGRAPH_URI = os.getenv("MEMGRAPH_URI") or os.getenv("NEO4J_URI")
MEMGRAPH_USERNAME = os.getenv("MEMGRAPH_USERNAME") or os.getenv("NEO4J_USERNAME", "")
MEMGRAPH_PASSWORD = os.getenv("MEMGRAPH_PASSWORD") or os.getenv("NEO4J_PASSWORD", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_driver():
    """Return a verified Memgraph driver instance (Neo4j-compatible)."""
    if not MEMGRAPH_URI:
        raise EnvironmentError("Missing MEMGRAPH_URI in .env")

    # Memgraph accepts empty strings for default auth
    driver = GraphDatabase.driver(MEMGRAPH_URI, auth=(MEMGRAPH_USERNAME, MEMGRAPH_PASSWORD))
    driver.verify_connectivity()
    logger.info("Memgraph connection established → %s", MEMGRAPH_URI)
    return driver


def get_embeddings() -> OpenAIEmbeddings:
    """Return a LangChain OpenAI embeddings instance (text-embedding-3-small)."""
    if not OPENAI_API_KEY:
        raise EnvironmentError("Missing OPENAI_API_KEY in .env")
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
    )


# ---------------------------------------------------------------------------
# Constraints — run once at pipeline start to guarantee uniqueness
# ---------------------------------------------------------------------------

_CONSTRAINTS = [
    "CREATE CONSTRAINT ON (n:Chapter) ASSERT n.code IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:SubChapter) ASSERT n.code IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Heading) ASSERT n.code IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:SubHeading) ASSERT n.code IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:HSCode) ASSERT n.code IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Tariff) ASSERT n.uid IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Cess) ASSERT n.uid IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Exemption) ASSERT n.uid IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:AntiDumpingDuty) ASSERT n.uid IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Procedure) ASSERT n.uid IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Measure) ASSERT n.uid IS UNIQUE;",
]


def create_constraints(driver) -> None:
    """Idempotently create all uniqueness constraints."""
    with driver.session() as session:
        for cypher in _CONSTRAINTS:
            try:
                session.run(cypher)
            except Exception as e:
                # Memgraph throws an error if the constraint already exists, we can safely ignore it
                if "already exists" not in str(e).lower():
                    logger.warning(f"Constraint issue: {e}")
    logger.info("Schema constraints verified / created.")
