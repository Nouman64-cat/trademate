"""
UN Comtrade Data Processor.
Fetches trade data, converts it to textual descriptions, and upserts to Pinecone.
"""
import logging
import json
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.un_comtrade import ComtradeClient
from app.services.embedder import embed_texts
from app.services.vector_store import make_vector_id, upsert_vectors
from app.logger import get_logger

logger = get_logger("trademate.comtrade_processor")

# M49 Codes
PAKISTAN_CODE = "586"
USA_CODE = "842"

# HS Code Fallback Descriptions (Common US-Pak commodities)
HS_FALLBACK = {
    "10": "Cereals (e.g., Rice)",
    "52": "Cotton",
    "61": "Articles of apparel and clothing accessories, knitted or crocheted",
    "62": "Articles of apparel and clothing accessories, not knitted or crocheted",
    "63": "Other made up textile articles; sets; worn clothing and worn textile articles",
    "84": "Nuclear reactors, boilers, machinery and mechanical appliances; parts thereof",
    "85": "Electrical machinery and equipment and parts thereof",
    "90": "Optical, photographic, cinematographic, measuring, checking, precision, medical instruments",
    "TOTAL": "Total of all commodities",
}

def textualize_record(record: Dict[str, Any]) -> str:
    """
    Convert a Comtrade record into a descriptive sentence.
    Example: "In 2023, Pakistan exported Cotton (HS 52) to the USA worth $520M."
    """
    year = record.get("period")
    flow = record.get("flowDesc", "trade")
    # Simplify flow for text (e.g., 'Export' or 'Import')
    if flow:
        flow = flow.lower()
    
    reporter = "Pakistan" if str(record.get("reporterCode")) == PAKISTAN_CODE else "the USA"
    partner = "the USA" if str(record.get("partnerCode")) == USA_CODE else "Pakistan"
    
    cmd_code = record.get("cmdCode")
    cmd_desc = record.get("cmdDesc") or HS_FALLBACK.get(cmd_code, f"HS code {cmd_code}")
    
    value = record.get("primaryValue", 0)
    # Convert value to readable format (usually USD)
    if value > 1_000_000:
        value_str = f"${value / 1_000_000:.2f} million"
    elif value > 1_000:
        value_str = f"${value / 1_000:.2f} thousand"
    else:
        value_str = f"${value:.2f}"

    text = f"In {year}, {reporter} {flow} {cmd_desc} ({cmd_code}) to {partner} with a total value of {value_str}."
    return text

def fetch_and_store_trade_data(
    years: List[str],
    reporter_code: str,
    partner_code: str,
    cl_code: str = "HS",
):
    """
    Fetch annual trade data for specific years and corridors, then store in Pinecone.
    """
    client = ComtradeClient()
    all_texts = []
    all_metadata = []

    for year in years:
        logger.info(f"Fetching {cl_code} trade data for {year}: Reporter={reporter_code}, Partner={partner_code}")
        try:
            # Fetch preview data (usually returns top results)
            result = client.get_preview(
                type_code="C",
                freq_code="A",
                cl_code=cl_code,
                reporter_code=reporter_code,
                partner_code=partner_code,
                period=year
            )
            
            data = result.get("data", [])
            logger.info(f"Retrieved {len(data)} records for {year}.")
            
            for record in data:
                text = textualize_record(record)
                all_texts.append(text)
                
                # Build metadata for Pinecone (ensure no null values as Pinecone rejects them)
                meta = {
                    "text": text,
                    "year": str(year),
                    "reporter": "Pakistan" if reporter_code == PAKISTAN_CODE else "USA",
                    "partner": "USA" if partner_code == USA_CODE else "Pakistan",
                    "flow": record.get("flowDesc") or "unknown",
                    "cmd_code": str(record.get("cmdCode") or "unknown"),
                    "source": "UN Comtrade",
                    "type": "trade_data",
                    "timestamp": datetime.utcnow().isoformat()
                }
                all_metadata.append(meta)

        except Exception as e:
            logger.error(f"Failed to fetch data for {year}: {e}")

    if not all_texts:
        logger.warning("No data fetched to store.")
        return

    logger.info(f"Generating embeddings for {len(all_texts)} trade records...")
    embeddings = embed_texts(all_texts)

    vectors = []
    for idx, (text, embedding, meta) in enumerate(zip(all_texts, embeddings, all_metadata)):
        # Generate a unique ID
        vid = f"comtrade_{meta['reporter']}_{meta['partner']}_{meta['year']}_{meta['cmd_code']}_{idx}"
        vectors.append({
            "id": vid,
            "values": embedding,
            "metadata": meta
        })

    logger.info(f"Upserting {len(vectors)} vectors to Pinecone...")
    upsert_vectors(vectors)
    logger.info("Ingestion complete.")

def run_us_pak_ingestion():
    """Run the ingestion for US-Pakistan corridors for the last 5 years."""
    years = ["2019", "2020", "2021", "2022", "2023"]
    
    # Corridor 1: Pakistan -> USA
    logger.info("### Starting Pakistan to USA Ingestion ###")
    fetch_and_store_trade_data(years, PAKISTAN_CODE, USA_CODE)
    
    # Corridor 2: USA -> Pakistan
    logger.info("### Starting USA to Pakistan Ingestion ###")
    fetch_and_store_trade_data(years, USA_CODE, PAKISTAN_CODE)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_us_pak_ingestion()
