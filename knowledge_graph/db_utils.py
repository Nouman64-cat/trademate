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
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        raise EnvironmentError(
            "Missing NEO4J_URI, NEO4J_USERNAME, or NEO4J_PASSWORD in .env"
        )
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    driver.verify_connectivity()
    logger.info("Neo4j connection established → %s", NEO4J_URI)
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
    # Hierarchy nodes keyed on their code
    "CREATE CONSTRAINT chapter_code IF NOT EXISTS FOR (n:Chapter) REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT subchapter_code IF NOT EXISTS FOR (n:SubChapter) REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT heading_code IF NOT EXISTS FOR (n:Heading) REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT subheading_code IF NOT EXISTS FOR (n:SubHeading) REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT hscode_code IF NOT EXISTS FOR (n:HSCode) REQUIRE n.code IS UNIQUE",
    # Leaf nodes keyed on a computed uid hash
    "CREATE CONSTRAINT tariff_uid IF NOT EXISTS FOR (n:Tariff) REQUIRE n.uid IS UNIQUE",
    "CREATE CONSTRAINT cess_uid IF NOT EXISTS FOR (n:Cess) REQUIRE n.uid IS UNIQUE",
    "CREATE CONSTRAINT exemption_uid IF NOT EXISTS FOR (n:Exemption) REQUIRE n.uid IS UNIQUE",
    "CREATE CONSTRAINT antidumping_uid IF NOT EXISTS FOR (n:AntiDumpingDuty) REQUIRE n.uid IS UNIQUE",
    "CREATE CONSTRAINT procedure_uid IF NOT EXISTS FOR (n:Procedure) REQUIRE n.uid IS UNIQUE",
    "CREATE CONSTRAINT measure_uid IF NOT EXISTS FOR (n:Measure) REQUIRE n.uid IS UNIQUE",
]


def create_constraints(driver) -> None:
    """Idempotently create all uniqueness constraints."""
    with driver.session() as session:
        for cypher in _CONSTRAINTS:
            session.run(cypher)
    logger.info("Schema constraints verified / created.")
