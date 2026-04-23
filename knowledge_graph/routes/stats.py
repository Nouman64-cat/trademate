"""
routes/stats.py — Knowledge graph statistics endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from db_utils import get_driver

router = APIRouter(prefix="/stats", tags=["Statistics"])


class GraphStats(BaseModel):
    total_nodes: int
    total_relationships: int
    pk_hs_codes: int
    us_hs_codes: int
    chapters: int
    subchapters: int
    headings: int
    subheadings: int
    tariffs: int
    exemptions: int
    procedures: int
    measures: int
    cess: int
    anti_dumping: int


@router.get("", response_model=GraphStats)
def get_graph_stats():
    """Get comprehensive knowledge graph statistics."""
    driver = get_driver()

    try:
        with driver.session() as session:
            # Total nodes and relationships
            total_nodes_result = session.run("MATCH (n) RETURN count(n) AS count")
            total_nodes = total_nodes_result.single()["count"]

            total_rels_result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            total_rels = total_rels_result.single()["count"]

            # HS Codes by source
            pk_hs_result = session.run("MATCH (n:HSCode:PK) RETURN count(n) AS count")
            pk_hs_codes = pk_hs_result.single()["count"]

            us_hs_result = session.run("MATCH (n:HSCode:US) RETURN count(n) AS count")
            us_hs_codes = us_hs_result.single()["count"]

            # Hierarchy nodes
            chapters_result = session.run("MATCH (n:Chapter) RETURN count(n) AS count")
            chapters = chapters_result.single()["count"]

            subchapters_result = session.run("MATCH (n:SubChapter) RETURN count(n) AS count")
            subchapters = subchapters_result.single()["count"]

            headings_result = session.run("MATCH (n:Heading) RETURN count(n) AS count")
            headings = headings_result.single()["count"]

            subheadings_result = session.run("MATCH (n:SubHeading) RETURN count(n) AS count")
            subheadings = subheadings_result.single()["count"]

            # Related data nodes
            tariffs_result = session.run("MATCH (n:Tariff) RETURN count(n) AS count")
            tariffs = tariffs_result.single()["count"]

            exemptions_result = session.run("MATCH (n:Exemption) RETURN count(n) AS count")
            exemptions = exemptions_result.single()["count"]

            procedures_result = session.run("MATCH (n:Procedure) RETURN count(n) AS count")
            procedures = procedures_result.single()["count"]

            measures_result = session.run("MATCH (n:Measure) RETURN count(n) AS count")
            measures = measures_result.single()["count"]

            cess_result = session.run("MATCH (n:Cess) RETURN count(n) AS count")
            cess = cess_result.single()["count"]

            anti_dump_result = session.run("MATCH (n:AntiDumpingDuty) RETURN count(n) AS count")
            anti_dumping = anti_dump_result.single()["count"]

        driver.close()

        return GraphStats(
            total_nodes=total_nodes,
            total_relationships=total_rels,
            pk_hs_codes=pk_hs_codes,
            us_hs_codes=us_hs_codes,
            chapters=chapters,
            subchapters=subchapters,
            headings=headings,
            subheadings=subheadings,
            tariffs=tariffs,
            exemptions=exemptions,
            procedures=procedures,
            measures=measures,
            cess=cess,
            anti_dumping=anti_dumping,
        )
    except Exception as e:
        driver.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get graph stats: {str(e)}"
        )
