"""
routes/query.py — Query HS codes and related data
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from db_utils import get_driver

router = APIRouter(prefix="/query", tags=["Query"])


class HSCodeDetail(BaseModel):
    code: str
    description: str
    source: str
    full_label: Optional[str] = None
    embedding: Optional[list[float]] = None
    tariffs: list[dict[str, Any]] = []
    exemptions: list[dict[str, Any]] = []
    procedures: list[dict[str, Any]] = []
    measures: list[dict[str, Any]] = []
    cess: list[dict[str, Any]] = []
    anti_dumping: list[dict[str, Any]] = []


class SearchResult(BaseModel):
    code: str
    description: str
    source: str
    full_label: Optional[str] = None
    similarity_score: Optional[float] = None


@router.get("/hs-code/{hs_code}", response_model=HSCodeDetail)
def get_hs_code(
    hs_code: str,
    source: str = Query("PK", description="Source: PK or US"),
    include_embedding: bool = Query(False, description="Include embedding vector in response"),
):
    """
    Get detailed information about a specific HS code including all relationships.

    - **hs_code**: The HS code to query (e.g., "010121000000" for PK, "0101.21" for US)
    - **source**: Data source - "PK" for Pakistan or "US" for United States
    - **include_embedding**: Whether to include the embedding vector in response
    """
    driver = get_driver()

    try:
        with driver.session() as session:
            # Get HS code node
            hs_result = session.run(
                f"MATCH (hs:HSCode:{source} {{code: $code}}) RETURN hs",
                code=hs_code,
            )
            hs_record = hs_result.single()

            if not hs_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"HS Code '{hs_code}' not found in {source} data",
                )

            hs_node = dict(hs_record["hs"])

            # Get tariffs
            tariffs_result = session.run(
                f"MATCH (hs:HSCode:{source} {{code: $code}})-[:HAS_TARIFF]->(t:Tariff) RETURN t",
                code=hs_code,
            )
            tariffs = [dict(record["t"]) for record in tariffs_result]

            # Get exemptions
            exemptions_result = session.run(
                f"MATCH (hs:HSCode:{source} {{code: $code}})-[:HAS_EXEMPTION]->(e:Exemption) RETURN e",
                code=hs_code,
            )
            exemptions = [dict(record["e"]) for record in exemptions_result]

            # Get procedures
            procedures_result = session.run(
                f"MATCH (hs:HSCode:{source} {{code: $code}})-[:REQUIRES_PROCEDURE]->(p:Procedure) RETURN p",
                code=hs_code,
            )
            procedures = [dict(record["p"]) for record in procedures_result]

            # Get measures
            measures_result = session.run(
                f"MATCH (hs:HSCode:{source} {{code: $code}})-[:HAS_MEASURE]->(m:Measure) RETURN m",
                code=hs_code,
            )
            measures = [dict(record["m"]) for record in measures_result]

            # Get cess (PK only)
            cess = []
            if source == "PK":
                cess_result = session.run(
                    f"MATCH (hs:HSCode:PK {{code: $code}})-[:HAS_CESS]->(c:Cess) RETURN c",
                    code=hs_code,
                )
                cess = [dict(record["c"]) for record in cess_result]

            # Get anti-dumping (PK only)
            anti_dumping = []
            if source == "PK":
                ad_result = session.run(
                    f"MATCH (hs:HSCode:PK {{code: $code}})-[:HAS_ANTI_DUMPING]->(a:AntiDumpingDuty) RETURN a",
                    code=hs_code,
                )
                anti_dumping = [dict(record["a"]) for record in ad_result]

        driver.close()

        # Remove embedding if not requested (it's a large array)
        embedding = None
        if include_embedding and "embedding" in hs_node:
            embedding = hs_node["embedding"]

        return HSCodeDetail(
            code=hs_code,
            description=hs_node.get("description", ""),
            source=source,
            full_label=hs_node.get("full_label"),
            embedding=embedding,
            tariffs=tariffs,
            exemptions=exemptions,
            procedures=procedures,
            measures=measures,
            cess=cess,
            anti_dumping=anti_dumping,
        )
    except HTTPException:
        driver.close()
        raise
    except Exception as e:
        driver.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query HS code: {str(e)}",
        )


@router.get("/search", response_model=list[SearchResult])
def search_hs_codes(
    q: str = Query(..., description="Search query"),
    source: str = Query("PK", description="Source: PK or US"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
):
    """
    Search HS codes by description using text matching.

    - **q**: Search query (matches against HS code descriptions)
    - **source**: Data source - "PK" for Pakistan or "US" for United States
    - **limit**: Maximum number of results to return (1-100)
    """
    driver = get_driver()

    try:
        with driver.session() as session:
            # Case-insensitive text search on description
            search_result = session.run(
                f"""
                MATCH (hs:HSCode:{source})
                WHERE toLower(hs.description) CONTAINS toLower($query)
                   OR hs.code CONTAINS $query
                RETURN hs.code AS code,
                       hs.description AS description,
                       hs.full_label AS full_label
                LIMIT $limit
                """,
                query=q,
                limit=limit,
            )

            results = []
            for record in search_result:
                results.append(
                    SearchResult(
                        code=record["code"],
                        description=record["description"],
                        source=source,
                        full_label=record.get("full_label"),
                    )
                )

        driver.close()
        return results

    except Exception as e:
        driver.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/hierarchy/{hs_code}", response_model=dict)
def get_hierarchy(
    hs_code: str,
    source: str = Query("PK", description="Source: PK or US"),
):
    """
    Get the complete hierarchy path for an HS code.

    Returns Chapter → SubChapter → Heading → SubHeading → HSCode
    """
    driver = get_driver()

    try:
        with driver.session() as session:
            hierarchy_result = session.run(
                f"""
                MATCH path = (ch:Chapter)-[:HAS_SUBCHAPTER]->(sc:SubChapter)
                             -[:HAS_HEADING]->(hd:Heading)
                             -[:HAS_SUBHEADING]->(sh:SubHeading)
                             -[:HAS_HSCODE]->(hs:HSCode:{source} {{code: $code}})
                RETURN ch, sc, hd, sh, hs
                """,
                code=hs_code,
            )

            record = hierarchy_result.single()

            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"HS Code '{hs_code}' or its hierarchy not found in {source} data",
                )

            hierarchy = {
                "chapter": dict(record["ch"]),
                "subchapter": dict(record["sc"]),
                "heading": dict(record["hd"]),
                "subheading": dict(record["sh"]),
                "hs_code": dict(record["hs"]),
            }

        driver.close()
        return hierarchy

    except HTTPException:
        driver.close()
        raise
    except Exception as e:
        driver.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hierarchy: {str(e)}",
        )
