"""
TIPP.gov.pk Scraper
====================
Scrapes all HS codes + tariff/cess/exemption/anti-dump/NTM/procedures data.

Flow:
  1. Fetch master list (26,000+ HS codes) from listView
  2. Extract 12-digit leaf HS codes (the ones with actual tariff data)
  3. For each, fetch codeView and parse 6 table types:
       - Tariffs (CD, RD, ACD, FED, ST, IT, DS, EOC, ERD …)
       - Cess Collection (province-wise)
       - Exemptions / Concessions
       - Anti-Dumping Duty
       - Non-Tariff Measures (NTM)
       - Trade Procedures
  4. Save to CSV files (one per table type) with incremental checkpointing

Resume:
  - checkpoint.txt       → tracks codes fully scraped (all 6 tables)
  - ntm_checkpoint.txt   → tracks codes scraped for NTM+Procedures
  Re-running resumes both passes automatically.
"""

import requests
import time
import csv
import os
import random
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from s3_utils import sync_data_from_s3, sync_data_to_s3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import (
    BASE_URL, DATA_DIR, PROXY_LIST, HEADERS, 
    TIMEOUT, MAX_RETRIES, DELAY_MIN, DELAY_MAX, MAX_WORKERS
)

# Output files
OUT_DIR            = DATA_DIR
FILE_MASTER        = os.path.join(OUT_DIR, "hs_codes_master.csv")
FILE_HIERARCHY     = os.path.join(OUT_DIR, "pct codes with hierarchy.csv")
FILE_TARIFFS       = os.path.join(OUT_DIR, "tariffs.csv")
FILE_CESS          = os.path.join(OUT_DIR, "cess_collection.csv")
FILE_EXEMPTIONS    = os.path.join(OUT_DIR, "exemption_concessions.csv")
FILE_ANTIDUMP      = os.path.join(OUT_DIR, "anti_dump_tariffs.csv")
FILE_MEASURES      = os.path.join(OUT_DIR, "measures.csv")
FILE_PROCEDURES    = os.path.join(OUT_DIR, "procedures.csv")
FILE_CHECKPOINT        = os.path.join(OUT_DIR, "checkpoint.txt")
FILE_NTM_CHECKPOINT    = os.path.join(OUT_DIR, "ntm_checkpoint.txt")
FILE_FAILED            = os.path.join(OUT_DIR, "failed.csv")

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("data", "scraper.log") if os.path.exists("data") else "scraper.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ── Proxy helpers ─────────────────────────────────────────────────────────────

_proxy_index = 0

def get_proxy_dict(index=None):
    global _proxy_index
    if index is None:
        proxy_str = PROXY_LIST[_proxy_index % len(PROXY_LIST)]
        _proxy_index += 1
    else:
        proxy_str = PROXY_LIST[index % len(PROXY_LIST)]
    ip, port, user, pw = proxy_str.split(":")
    url = f"http://{user}:{pw}@{ip}:{port}"
    return {"http": url, "https": url}

def fetch_with_retry(url, retries=MAX_RETRIES):
    """Fetch URL cycling through proxies on failure."""
    start_proxy = _proxy_index
    for attempt in range(retries):
        proxy_dict = get_proxy_dict(start_proxy + attempt)
        try:
            resp = requests.get(
                url, headers=HEADERS, proxies=proxy_dict,
                timeout=TIMEOUT, verify=False
            )
            resp.raise_for_status()
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            return resp.text
        except Exception as e:
            log.warning(f"Attempt {attempt+1}/{retries} failed for {url}: {e}")
            time.sleep(1.5 * (attempt + 1))
    return None

# ── CSV helpers ───────────────────────────────────────────────────────────────

def init_csv(filepath, headers):
    if not os.path.exists(filepath):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(headers)

def append_rows(filepath, rows):
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for row in rows:
            # Force first column (always HS Code) to string to prevent scientific notation
            safe_row = [str(row[0])] + list(row[1:]) if row else row
            w.writerow(safe_row)

def load_checkpoint(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_checkpoint(filepath, hs_code):
    with open(filepath, "a") as f:
        f.write(hs_code + "\n")

def clean_failed_csv(done):
    if not os.path.exists(FILE_FAILED):
        return
    with open(FILE_FAILED, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if len(rows) <= 1:
        return
    header = rows[0]
    still_failed = [r for r in rows[1:] if r and r[0] not in done]
    removed = len(rows) - 1 - len(still_failed)
    if removed > 0:
        with open(FILE_FAILED, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(still_failed)
        log.info(f"Cleaned failed.csv: removed {removed} codes that succeeded on retry.")

# ── Hierarchy file builder ────────────────────────────────────────────────────

def build_hierarchy_file(all_codes):
    """
    Generate 'pct codes with hierarchy.csv' from the scraped master list.
    Each row has the HS code plus its Chapter / Sub Chapter / Heading / Sub Heading
    descriptions derived from prefix lookups — same logic used by combine_output.py.
    Skipped if file already exists and is non-empty (idempotent).
    """
    if os.path.exists(FILE_HIERARCHY) and os.path.getsize(FILE_HIERARCHY) > 100:
        log.info("pct codes with hierarchy.csv already present — skipping rebuild.")
        return

    # Build code → description lookup (strip spaces so prefixes align cleanly)
    lookup = {}
    for hs_code, description, _, _ in all_codes:
        cleaned = hs_code.replace(" ", "")
        lookup[cleaned] = description

    rows = []
    for hs_code, description, _, _ in all_codes:
        cleaned = str(hs_code.replace(" ", ""))  # explicit str — no scientific notation
        rows.append([
            cleaned,
            description,
            lookup.get(cleaned[:2], ""),   # Chapter description
            lookup.get(cleaned[:4], ""),   # Sub Chapter description
            lookup.get(cleaned[:6], ""),   # Heading description
            lookup.get(cleaned[:8], ""),   # Sub Heading description
        ])

    init_csv(FILE_HIERARCHY, [
        "HS Code", "Description",
        "Chapter", "Sub Chapter", "Heading", "Sub Heading",
    ])
    append_rows(FILE_HIERARCHY, rows)
    log.info(f"Built pct codes with hierarchy.csv — {len(rows)} entries.")

# ── Page parsers ──────────────────────────────────────────────────────────────

def parse_master_list(html):
    soup = BeautifulSoup(html, "lxml")
    results = []
    table = soup.find("table")
    if not table:
        return results
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        a_tag = cells[0].find("a")
        if not a_tag:
            continue
        hs_code = a_tag.get_text(strip=True)
        description = cells[1].get_text(strip=True)
        href = a_tag.get("href", "")
        desc_id = ""
        if "id=" in href:
            desc_id = href.split("id=")[-1].strip()
        is_leaf = len(hs_code.replace(" ", "")) == 12
        results.append((hs_code, description, desc_id, is_leaf))
    return results


def parse_code_view(hs_code, description, html, ntm_only=False):
    """
    Parse a codeView page.
    Returns dict with keys:
      commodity, tariffs, cess, exemptions, antidump, measures, procedures.

    ntm_only=True: skips tariff/cess/exemptions/antidump tables but still
                   parses commodity block and measures/procedures.
    """
    soup = BeautifulSoup(html, "lxml")
    result = {
        "tariffs": [], "cess": [], "exemptions": [], "antidump": [],
        "measures": [], "procedures": [],
    }

    # ── Tables 1-4: Tariffs, Cess, Exemptions, Anti-dump ─────────────────────
    if not ntm_only:
        tables = soup.find_all("table")

        for tbl in tables:
            ths_text = " ".join(th.get_text(strip=True) for th in tbl.find_all("th"))

            # Tariffs — all duty rows including CD, RD, ACD, FED, ST, IT, DS, EOC, ERD
            if "Duty" in ths_text and "Tariff Rate" in ths_text and not result["tariffs"]:
                for row in tbl.find_all("tr")[1:]:
                    cells = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
                    if cells and cells[0].lower() != "no results found.":
                        result["tariffs"].append([hs_code, description] + cells)
                # Ensure every code has an explicit RD row.
                # If the website doesn't show RD, it means 0% applies.
                has_rd = any(r[2] == "RD" for r in result["tariffs"])
                if not has_rd and result["tariffs"]:
                    result["tariffs"].append([
                        hs_code, description,
                        "RD", "Statutory Regulatory Duty", "Import",
                        "0%", "", "", ""
                    ])

            # Cess Collection
            elif "Province" in ths_text and "Import" in ths_text and not result["cess"]:
                for row in tbl.find_all("tr")[1:]:
                    cells = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
                    if cells and cells[0].lower() != "no results found.":
                        result["cess"].append([hs_code, description] + cells)

            # Exemptions / Concessions
            elif "Exemption" in ths_text and not result["exemptions"]:
                for row in tbl.find_all("tr")[1:]:
                    cells = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
                    if cells and cells[0].lower() != "no results found.":
                        result["exemptions"].append([hs_code, description] + cells)

            # Anti-Dumping Duty — has Rate + Valid From but no Duty/Province/Exemption
            elif (
                "Rate" in ths_text and "Valid From" in ths_text
                and "Duty" not in ths_text and "Province" not in ths_text
                and "Exemption" not in ths_text and "Agency" not in ths_text
                and not result["antidump"]
            ):
                for row in tbl.find_all("tr")[1:]:
                    cells = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
                    if cells and cells[0].lower() != "no results found.":
                        result["antidump"].append([hs_code, description] + cells)

    # ── Measures (NTM) and Procedures ────────────────────────────────────────
    # These live in grid-view divs that each contain both an H1="Measures"
    # and an H1="Procedures" section, as direct children of the #content div.
    content_div = soup.find("div", id="content")
    if content_div:
        for gv in content_div.find_all("div", class_="grid-view"):
            h1_texts = [h.get_text(strip=True) for h in gv.find_all("h1")]
            if "Measures" not in h1_texts:
                continue  # not a Measures+Procedures block

            for h1 in gv.find_all("h1"):
                section_title = h1.get_text(strip=True)
                tbl = h1.find_next("table")
                if not tbl:
                    continue

                if section_title == "Measures":
                    for row in tbl.find_all("tr")[1:]:
                        cells = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
                        if not cells or cells[0].lower() == "no results found.":
                            continue
                        # Capture the measure detail URL from the first link
                        links = [
                            a["href"] for td in row.find_all("td")
                            for a in td.find_all("a") if a.get("href")
                        ]
                        measure_url = (BASE_URL + links[0]) if links else ""
                        # cells: [Name, Type, Agency, Description, Comments, Law, Validity]
                        padded = (cells + [""] * 7)[:7]
                        result["measures"].append(
                            [hs_code, description] + padded + [measure_url]
                        )

                elif section_title == "Procedures":
                    for row in tbl.find_all("tr")[1:]:
                        cells = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
                        if not cells or cells[0].lower() == "no results found.":
                            continue
                        links = [
                            a["href"] for td in row.find_all("td")
                            for a in td.find_all("a") if a.get("href")
                        ]
                        proc_url = (BASE_URL + links[0]) if links else ""
                        # cells: [Name, Description, Category, View]
                        padded = (cells + [""] * 3)[:3]
                        result["procedures"].append(
                            [hs_code, description] + padded + [proc_url]
                        )

    return result

# ── Worker ────────────────────────────────────────────────────────────────────

def fetch_and_parse_hs(item):
    """Worker: fetch codeView for one HS code and return parsed data."""
    hs_code, description, ntm_only = item
    url = (f"{BASE_URL}/index.php?r=tradeInfo/codeView"
           f"&hsType=Code&value={hs_code}&searchType=HSCODE")
    html = fetch_with_retry(url)
    if html is None:
        return hs_code, description, None, ntm_only
    data = parse_code_view(hs_code, description, html, ntm_only=ntm_only)
    return hs_code, description, data, ntm_only

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Sync existing data from S3 to resume checkpoints
    log.info("Syncing data from S3...")
    sync_data_from_s3(OUT_DIR)

    log.handlers.clear()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(OUT_DIR, "scraper.log")),
            logging.StreamHandler(),
        ],
        force=True,
    )

    # ── Step 1: Fetch master list ─────────────────────────────────────────────
    log.info("Fetching master HS code list…")
    master_url = f"{BASE_URL}/index.php?r=tradeInfo/listView&searchType=HSCODE&value="
    master_html = fetch_with_retry(master_url, retries=MAX_RETRIES)
    if master_html is None:
        log.error("Failed to fetch master list. Check proxies and try again.")
        return

    all_codes = parse_master_list(master_html)
    log.info(f"Parsed {len(all_codes)} total HS entries.")

    init_csv(FILE_MASTER, ["HS Code", "Description", "Desc ID", "Is Leaf"])
    if not os.path.exists(FILE_MASTER) or os.path.getsize(FILE_MASTER) < 100:
        append_rows(FILE_MASTER, [(c, d, i, l) for c, d, i, l in all_codes])

    # Build the hierarchy reference file (idempotent — skipped if already exists)
    build_hierarchy_file(all_codes)

    leaf_codes = [(hs, desc) for hs, desc, _, is_leaf in all_codes if is_leaf]
    log.info(f"Found {len(leaf_codes)} leaf-level HS codes to scrape.")

    # ── Step 2: Init all output CSVs ──────────────────────────────────────────
    init_csv(FILE_TARIFFS, [
        "HS Code", "Description",
        "Duty", "Group Description", "Activity", "Tariff Rate", "Unit", "Valid From", "Valid To"
    ])
    init_csv(FILE_CESS, [
        "HS Code", "Description",
        "Province", "Cess Description", "Import", "Export", "Forward Transit", "Reverse Transit"
    ])
    init_csv(FILE_EXEMPTIONS, [
        "HS Code", "Description",
        "Exemption/Concession", "Exemption Description", "Reference", "Activity",
        "Rate", "Unit", "Valid From", "Valid To"
    ])
    init_csv(FILE_ANTIDUMP, [
        "HS Code", "Description",
        "Description", "Rate", "Valid From", "Valid To"
    ])
    init_csv(FILE_MEASURES, [
        "HS Code", "Description",
        "Name", "Type", "Agency", "Measure Description", "Comments", "Law", "Validity", "Measure URL"
    ])
    init_csv(FILE_PROCEDURES, [
        "HS Code", "Description",
        "Name", "Procedure Description", "Category", "Procedure URL"
    ])
    init_csv(FILE_FAILED, ["HS Code", "Description", "Reason"])

    # ── Step 3: Load checkpoints ───────────────────────────────────────────────
    done     = load_checkpoint(FILE_CHECKPOINT)       # fully scraped (all tables)
    ntm_done = load_checkpoint(FILE_NTM_CHECKPOINT)   # scraped for NTM+Procedures
    clean_failed_csv(done)

    # Codes needing NTM-only re-fetch (tariffs etc. already done)
    ntm_pending = [(hs, desc, True) for hs, desc in leaf_codes
                   if hs in done and hs not in ntm_done]

    # Codes needing full scrape
    full_pending = [(hs, desc, False) for hs, desc in leaf_codes
                    if hs not in done]

    pending = ntm_pending + full_pending

    log.info(
        f"Checkpoint status — fully done: {len(done)} | "
        f"NTM done: {len(ntm_done)} | "
        f"NTM re-fetch: {len(ntm_pending)} | "
        f"Full scrape remaining: {len(full_pending)}"
    )

    if not pending:
        log.info("All HS codes fully scraped (tariffs + NTM). Done!")
        return

    # ── Step 4: Scrape concurrently ───────────────────────────────────────────
    total     = len(pending)
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_and_parse_hs, item): item for item in pending}
        for future in as_completed(futures):
            hs_code, description, data, ntm_only = future.result()
            completed += 1

            if data is None:
                log.warning(f"[{completed}/{total}] FAILED: {hs_code} (ntm_only={ntm_only})")
                append_rows(FILE_FAILED, [[hs_code, description, "fetch_failed"]])
                continue

            if not ntm_only:
                if data["tariffs"]:
                    append_rows(FILE_TARIFFS, data["tariffs"])
                if data["cess"]:
                    append_rows(FILE_CESS, data["cess"])
                if data["exemptions"]:
                    append_rows(FILE_EXEMPTIONS, data["exemptions"])
                if data["antidump"]:
                    append_rows(FILE_ANTIDUMP, data["antidump"])
                save_checkpoint(FILE_CHECKPOINT, hs_code)

            if hs_code not in ntm_done:
                if data["measures"]:
                    append_rows(FILE_MEASURES, data["measures"])
                if data["procedures"]:
                    append_rows(FILE_PROCEDURES, data["procedures"])
                save_checkpoint(FILE_NTM_CHECKPOINT, hs_code)

            log.info(
                f"[{completed}/{total}] {'NTM-only' if ntm_only else 'FULL'} {hs_code} | "
                f"tariffs={len(data['tariffs'])} cess={len(data['cess'])} "
                f"exempt={len(data['exemptions'])} antidump={len(data['antidump'])} "
                f"measures={len(data['measures'])} procs={len(data['procedures'])}"
            )
            
            # Periodically sync to S3
            if completed % 50 == 0:
                log.info("Performing periodic S3 sync...")
                sync_data_to_s3(OUT_DIR)

    # ── Step 5: Patch — ensure every code has an explicit RD row ─────────────
    patch_missing_rd()

    log.info("=" * 60)
    log.info(f"Scraping complete. Output saved to: {OUT_DIR}/")
    for f in [FILE_MASTER, FILE_HIERARCHY, FILE_TARIFFS, FILE_CESS, FILE_EXEMPTIONS,
              FILE_ANTIDUMP, FILE_MEASURES, FILE_PROCEDURES, FILE_FAILED]:
        log.info(f"  {f}")

    # Final sync to S3
    log.info("Performing final S3 sync...")
    sync_data_to_s3(OUT_DIR)


def patch_missing_rd():
    """
    Post-processing: ensure every HS code in tariffs.csv has a Statutory
    Regulatory Duty (RD) row.  If the website did not show RD for a code,
    the rate is 0% (i.e. no RD applies).  Safe to run multiple times.
    """
    if not os.path.exists(FILE_TARIFFS):
        return
    from collections import OrderedDict
    rows_by_code = OrderedDict()
    fieldnames = None
    with open(FILE_TARIFFS, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows_by_code.setdefault(row["HS Code"], []).append(row)

    tmp = FILE_TARIFFS + ".tmp"
    added = 0
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for hs, rows in rows_by_code.items():
            w.writerows(rows)
            if not any(r["Duty"] == "RD" for r in rows):
                w.writerow({
                    "HS Code": hs, "Description": rows[0]["Description"],
                    "Duty": "RD", "Group Description": "Statutory Regulatory Duty",
                    "Activity": "Import", "Tariff Rate": "0%",
                    "Unit": "", "Valid From": "", "Valid To": "",
                })
                added += 1
    os.replace(tmp, FILE_TARIFFS)
    if added:
        log.info(f"patch_missing_rd: added RD=0% rows for {added} codes.")
    else:
        log.info("patch_missing_rd: all codes already have RD. No changes.")


if __name__ == "__main__":
    run()
