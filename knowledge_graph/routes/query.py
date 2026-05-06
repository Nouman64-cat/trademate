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


# PK nodes use property "code" (12-digit); US nodes use property "hts_code" (dotted).
def _code_prop(source: str) -> str:
    return "hts_code" if source == "US" else "code"


@router.get("/hs-code/{hs_code}", response_model=HSCodeDetail)
def get_hs_code(
    hs_code: str,
    source: str = Query("PK", description="Source: PK or US"),
    include_embedding: bool = Query(False, description="Include embedding vector in response"),
):
    """
    Get detailed information about a specific HS code including all relationships.

    - **hs_code**: The HS code to query (e.g., "010121000000" for PK, "0101.21.00" for US)
    - **source**: Data source - "PK" for Pakistan or "US" for United States
    - **include_embedding**: Whether to include the embedding vector in response
    """
    prop = _code_prop(source)
    driver = get_driver()

    try:
        with driver.session() as session:
            hs_result = session.run(
                f"MATCH (hs:HSCode:{source} {{{prop}: $code}}) RETURN hs",
                code=hs_code,
            )
            hs_record = hs_result.single()

            if not hs_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"HS Code '{hs_code}' not found in {source} data",
                )

            hs_node = dict(hs_record["hs"])

            tariffs_result = session.run(
                f"MATCH (hs:HSCode:{source} {{{prop}: $code}})-[:HAS_TARIFF]->(t:Tariff) RETURN t",
                code=hs_code,
            )
            tariffs = [dict(record["t"]) for record in tariffs_result]

            exemptions_result = session.run(
                f"MATCH (hs:HSCode:{source} {{{prop}: $code}})-[:HAS_EXEMPTION]->(e:Exemption) RETURN e",
                code=hs_code,
            )
            exemptions = [dict(record["e"]) for record in exemptions_result]

            procedures_result = session.run(
                f"MATCH (hs:HSCode:{source} {{{prop}: $code}})-[:REQUIRES_PROCEDURE]->(p:Procedure) RETURN p",
                code=hs_code,
            )
            procedures = [dict(record["p"]) for record in procedures_result]

            measures_result = session.run(
                f"MATCH (hs:HSCode:{source} {{{prop}: $code}})-[:HAS_MEASURE]->(m:Measure) RETURN m",
                code=hs_code,
            )
            measures = [dict(record["m"]) for record in measures_result]

            cess = []
            if source == "PK":
                cess_result = session.run(
                    "MATCH (hs:HSCode:PK {code: $code})-[:HAS_CESS]->(c:Cess) RETURN c",
                    code=hs_code,
                )
                cess = [dict(record["c"]) for record in cess_result]

            anti_dumping = []
            if source == "PK":
                ad_result = session.run(
                    "MATCH (hs:HSCode:PK {code: $code})-[:HAS_ANTI_DUMPING]->(a:AntiDumpingDuty) RETURN a",
                    code=hs_code,
                )
                anti_dumping = [dict(record["a"]) for record in ad_result]

        driver.close()

        embedding = None
        if include_embedding and "embedding" in hs_node:
            embedding = hs_node["embedding"]

        return HSCodeDetail(
            code=hs_code,
            description=hs_node.get("description", ""),
            source=source,
            full_label=hs_node.get("full_label") or hs_node.get("full_path_description"),
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
            if source == "US":
                search_result = session.run(
                    """
                    MATCH (hs:HSCode:US)
                    WHERE toLower(hs.description) CONTAINS toLower($query)
                       OR (hs.hts_code IS NOT NULL AND hs.hts_code CONTAINS $query)
                    RETURN hs.hts_code          AS code,
                           hs.description        AS description,
                           hs.full_path_description AS full_label
                    LIMIT $limit
                    """,
                    query=q,
                    limit=limit,
                )
            else:
                search_result = session.run(
                    """
                    MATCH (hs:HSCode:PK)
                    WHERE toLower(hs.description) CONTAINS toLower($query)
                       OR hs.code CONTAINS $query
                    RETURN hs.code       AS code,
                           hs.description AS description,
                           hs.full_label  AS full_label
                    LIMIT $limit
                    """,
                    query=q,
                    limit=limit,
                )

            results = []
            for record in search_result:
                results.append(
                    SearchResult(
                        code=record["code"] or "",
                        description=record["description"] or "",
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
    Get the hierarchy path for an HS code.

    PK: returns Chapter → SubChapter → Heading → SubHeading → HSCode
    US: returns the ancestor chain via HAS_CHILD relationships
    """
    driver = get_driver()

    try:
        with driver.session() as session:
            if source == "US":
                # US nodes use HAS_CHILD chains; no Chapter/Heading hierarchy.
                result = session.run(
                    """
                    MATCH (hs:HSCode:US {hts_code: $code})
                    OPTIONAL MATCH (hs)<-[:HAS_CHILD*1..6]-(ancestor:HSCode:US)
                    RETURN hs,
                           collect(DISTINCT {
                               hts_code: ancestor.hts_code,
                               description: ancestor.description,
                               indent: ancestor.indent
                           }) AS ancestors
                    """,
                    code=hs_code,
                )
                record = result.single()

                if not record or record["hs"] is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"HS Code '{hs_code}' not found in US data",
                    )

                hs_node = dict(record["hs"])
                # Sort ancestors by indent ascending (root first)
                ancestors = sorted(
                    [a for a in record["ancestors"] if a.get("hts_code")],
                    key=lambda a: a.get("indent") or 0,
                )
                return {
                    "hs_code": hs_node,
                    "ancestors": ancestors,
                }

            else:
                hierarchy_result = session.run(
                    """
                    MATCH path = (ch:Chapter)-[:HAS_SUBCHAPTER]->(sc:SubChapter)
                                 -[:HAS_HEADING]->(hd:Heading)
                                 -[:HAS_SUBHEADING]->(sh:SubHeading)
                                 -[:HAS_HSCODE]->(hs:HSCode:PK {code: $code})
                    RETURN ch, sc, hd, sh, hs
                    """,
                    code=hs_code,
                )

                record = hierarchy_result.single()

                if not record:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"HS Code '{hs_code}' or its hierarchy not found in PK data",
                    )

                return {
                    "chapter":    dict(record["ch"]),
                    "subchapter": dict(record["sc"]),
                    "heading":    dict(record["hd"]),
                    "subheading": dict(record["sh"]),
                    "hs_code":    dict(record["hs"]),
                }

        driver.close()

    except HTTPException:
        driver.close()
        raise
    except Exception as e:
        driver.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hierarchy: {str(e)}",
        )
