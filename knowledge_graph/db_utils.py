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

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_driver():
    """Return a verified Neo4j driver instance."""
    if not NEO4J_URI:
        raise EnvironmentError("Missing NEO4J_URI in .env")
    
    # Memgraph accepts empty strings for default auth
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    driver.verify_connectivity()
    logger.info("Database connection established → %s", NEO4J_URI)
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
