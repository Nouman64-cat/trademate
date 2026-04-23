"""
scrape_details.py
=================
Scrapes detail pages for unique Measures and Procedures already captured
in data/measures.csv and data/procedures.csv.

Produces EXACTLY 3 new files (no existing file is touched):
  data/measures_detail.csv   — full detail for each unique measure
  data/procedures_detail.csv — full detail for each unique procedure
  data/products.csv          — products table from both page types

Run:
    python scrape_details.py

Resumes automatically if interrupted (reads existing output rows as checkpoint).
"""

import csv
import os
import random
import re
import time
import logging
import requests
import urllib3
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from s3_utils import sync_data_from_s3, sync_data_to_s3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "https://tipp.gov.pk"

PROXY_LIST = [
    "45.43.83.148:6431:wlukdecd:e2u6bssg5n7i",
    "82.24.236.68:7878:wlukdecd:e2u6bssg5n7i",
    "82.24.242.39:7858:wlukdecd:e2u6bssg5n7i",
    "107.181.142.34:5627:wlukdecd:e2u6bssg5n7i",
    "45.43.65.112:6626:wlukdecd:e2u6bssg5n7i",
    "107.181.148.183:6043:wlukdecd:e2u6bssg5n7i",
    "198.37.116.109:6068:wlukdecd:e2u6bssg5n7i",
    "45.39.13.121:5558:wlukdecd:e2u6bssg5n7i",
    "64.137.77.99:5534:wlukdecd:e2u6bssg5n7i",
    "103.99.33.252:6247:wlukdecd:e2u6bssg5n7i",
    "104.253.82.202:6623:wlukdecd:e2u6bssg5n7i",
    "45.41.162.100:6737:wlukdecd:e2u6bssg5n7i",
    "92.112.137.90:6033:wlukdecd:e2u6bssg5n7i",
    "154.29.65.179:6287:wlukdecd:e2u6bssg5n7i",
    "82.26.208.115:5422:wlukdecd:e2u6bssg5n7i",
    "198.23.147.145:5160:wlukdecd:e2u6bssg5n7i",
    "45.39.5.60:6498:wlukdecd:e2u6bssg5n7i",
    "50.114.99.68:6809:wlukdecd:e2u6bssg5n7i",
    "216.173.120.231:6523:wlukdecd:e2u6bssg5n7i",
    "82.27.246.212:7536:wlukdecd:e2u6bssg5n7i",
    "31.58.10.10:5978:wlukdecd:e2u6bssg5n7i",
    "45.39.25.128:5563:wlukdecd:e2u6bssg5n7i",
    "103.75.228.37:6116:wlukdecd:e2u6bssg5n7i",
    "64.137.59.61:6654:wlukdecd:e2u6bssg5n7i",
    "136.0.207.52:6629:wlukdecd:e2u6bssg5n7i",
    "82.21.244.167:5490:wlukdecd:e2u6bssg5n7i",
    "104.252.49.195:6131:wlukdecd:e2u6bssg5n7i",
    "104.239.35.132:5814:wlukdecd:e2u6bssg5n7i",
    "173.214.177.99:5790:wlukdecd:e2u6bssg5n7i",
    "104.239.90.85:6476:wlukdecd:e2u6bssg5n7i",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://tipp.gov.pk/",
}

TIMEOUT     = 25
MAX_RETRIES = 6
DELAY_MIN   = 0.3
DELAY_MAX   = 0.9
MAX_WORKERS = 4

OUT_DIR               = "data"
FILE_MEASURES_IN      = os.path.join(OUT_DIR, "measures.csv")
FILE_PROCEDURES_IN    = os.path.join(OUT_DIR, "procedures.csv")
FILE_MEASURES_OUT     = os.path.join(OUT_DIR, "measures_detail.csv")
FILE_PROCEDURES_OUT   = os.path.join(OUT_DIR, "procedures_detail.csv")
FILE_PRODUCTS_OUT     = os.path.join(OUT_DIR, "products.csv")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(OUT_DIR, "details_scraper.log"), encoding="utf-8"),
        logging.StreamHandler(stream=open(os.devnull, "w")),  # suppress console unicode errors
    ],
)
# Re-add a safe console handler
_console = logging.StreamHandler()
_console.setLevel(logging.INFO)
_console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_console.stream = __import__("sys").stdout
logging.getLogger().addHandler(_console)
log = logging.getLogger(__name__)

# ── Proxy helpers ─────────────────────────────────────────────────────────────
_proxy_idx = 0

def _next_proxy():
    global _proxy_idx
    s = PROXY_LIST[_proxy_idx % len(PROXY_LIST)]
    _proxy_idx += 1
    ip, port, user, pw = s.split(":")
    url = f"http://{user}:{pw}@{ip}:{port}"
    return {"http": url, "https": url}

def fetch(url, retries=MAX_RETRIES):
    """Fetch URL with proxy rotation and retry."""
    start = _proxy_idx
    for attempt in range(retries):
        proxies = _next_proxy()
        try:
            r = requests.get(url, headers=HEADERS, proxies=proxies,
                             timeout=TIMEOUT, verify=False)
            r.raise_for_status()
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            return r.text
        except Exception as e:
            log.warning(f"  Attempt {attempt+1}/{retries} failed for {url}: {e}")
            time.sleep(1.5 * (attempt + 1))
    log.error(f"  All retries exhausted for {url}")
    return None

# ── Generic helpers ───────────────────────────────────────────────────────────

def txt(el):
    """Get stripped text from a BS4 element or return ''."""
    return el.get_text(" ", strip=True) if el else ""

def extract_id_from_url(url):
    m = re.search(r'[?&]id=(\d+)', url)
    return m.group(1) if m else url

def parse_kv_table(tbl):
    """
    Parse a 2-column <table> where col0=key, col1=value (no <th> headers).
    Returns dict.
    """
    result = {}
    if not tbl:
        return result
    for tr in tbl.find_all("tr"):
        tds = tr.find_all(["td", "th"])
        if len(tds) >= 2:
            key = tds[0].get_text(strip=True).rstrip(":")
            val = tds[1].get_text(" ", strip=True)
            if key:
                result[key] = val
    return result

def parse_data_table(tbl):
    """
    Parse a data <table> with a header row (<th> or first <tr>).
    Returns list of dicts.
    """
    if not tbl:
        return []
    rows = tbl.find_all("tr")
    if not rows:
        return []
    # Header row: prefer <th> elements, fall back to first row <td>
    header_row = rows[0]
    headers = [c.get_text(strip=True) for c in header_row.find_all(["th", "td"])]
    result = []
    for tr in rows[1:]:
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if any(cells):
            result.append(dict(zip(headers, cells)))
    return result

def is_kv_table(tbl):
    """
    Heuristic: a key-value table has 2 columns and the first cell of each
    row looks like a label (no spaces or short text).
    """
    rows = tbl.find_all("tr")
    if not rows:
        return False
    two_col_count = sum(1 for tr in rows if len(tr.find_all(["td", "th"])) == 2)
    return two_col_count >= max(1, len(rows) // 2)

# ── Output field definitions ──────────────────────────────────────────────────

MEASURE_FIELDS = [
    "Measure ID",
    "Name",
    "Description",
    "Comments",
    "Validity From",
    "Validity To",
    "Reference",
    "Technical Code",
    "Agency",
    "Created Date",
    "Updated Date",
    "Status",
    "Measure Type",
    "Legal/Regulation",
    "Un Code",
    "Applies To HS Codes",
    "Source URL",
]

PROCEDURE_FIELDS = [
    "Procedure ID",
    "Procedure Name",
    "Description",
    "Category",
    "Forms",
    "Associated Measures",
    "Source URL",
]

PRODUCT_FIELDS = [
    "Source Type",
    "Source ID",
    "Source URL",
    "Product Name",
    "Product Family",
    "Product Technical Name",
    "Brand Name",
    "Comments",
    "File",
]

# ── Measure page parser ───────────────────────────────────────────────────────

# These known field names appear in the first KV table on measure pages.
# Any 2-col table whose first-column entries match these is the main info table.
MEASURE_KV_KEYS = {
    "Name", "Description", "Comments", "Validity From", "Validity To",
    "Reference", "Technical Code", "Agency", "Created Date", "Updated Date",
    "Status", "Measure Type", "Legal/Regulation", "Un Code",
    "Validity",  # alias
}

def parse_measure_page(url, mid):
    """
    Returns (data_dict, products_list).
    data_dict keys match MEASURE_FIELDS.
    """
    html = fetch(url)
    if not html:
        return None, []

    soup = BeautifulSoup(html, "lxml")
    data = {"Measure ID": mid, "Source URL": url}
    products = []

    tables = soup.find_all("table")
    hs_codes = []

    for tbl in tables:
        rows = tbl.find_all("tr")
        if not rows:
            continue

        tds_in_rows = [tr.find_all(["td", "th"]) for tr in rows]
        col_counts = [len(c) for c in tds_in_rows if c]

        # ── 2-col KV table (main info) ────────────────────────────────────────
        if col_counts and all(c == 2 for c in col_counts):
            first_keys = {tds[0].get_text(strip=True) for tds in tds_in_rows if len(tds) == 2}
            if first_keys & MEASURE_KV_KEYS:
                kv = parse_kv_table(tbl)
                for k, v in kv.items():
                    canonical = _measure_key(k)
                    if canonical not in data:
                        data[canonical] = v
                continue

        # ── HS Code table: has columns "HS Code" and "Description" ───────────
        headers = [c.get_text(strip=True) for c in (rows[0].find_all(["th", "td"]))]
        if headers and "HS Code" in headers:
            for row_d in parse_data_table(tbl):
                hs  = row_d.get("HS Code", "").strip()
                dsc = row_d.get("Description", "").strip()
                if hs:
                    hs_codes.append(f"{hs} | {dsc}" if dsc else hs)
            continue

        # ── Products table ────────────────────────────────────────────────────
        if headers and any("Product" in h for h in headers):
            for row_d in parse_data_table(tbl):
                prod = _build_product(row_d, "Measure", mid, url)
                if prod:
                    products.append(prod)

    data["Applies To HS Codes"] = " || ".join(hs_codes)
    return data, products


def _measure_key(raw):
    """Normalise measure field labels to canonical column names."""
    mapping = {
        "Measure Name": "Name",
        "Validity": "Validity From",
        "Valid From": "Validity From",
        "Valid To": "Validity To",
        "Un-Code": "Un Code",
        "UNCODE": "Un Code",
        "Legal / Regulation": "Legal/Regulation",
        "Legal/Regulations": "Legal/Regulation",
        "Legal Regulation": "Legal/Regulation",
    }
    return mapping.get(raw, raw)

# ── Procedure page parser ─────────────────────────────────────────────────────

PROCEDURE_KV_KEYS = {"Procedure Name", "Description", "Category", "Name"}

def parse_procedure_page(url, pid):
    """
    Returns (data_dict, products_list).
    data_dict keys match PROCEDURE_FIELDS.
    """
    html = fetch(url)
    if not html:
        return None, []

    soup = BeautifulSoup(html, "lxml")
    data = {"Procedure ID": pid, "Source URL": url}
    products = []

    tables = soup.find_all("table")
    forms_list = []
    assoc_measures = []

    for tbl in tables:
        rows = tbl.find_all("tr")
        if not rows:
            continue

        # Detect whether the first row is an all-<th> header row (data table)
        # vs a mixed th/td row (KV table where <th> is the label).
        row0_cells = rows[0].find_all(["th", "td"])
        all_th_header = bool(row0_cells) and all(c.name == "th" for c in row0_cells)
        headers = [c.get_text(strip=True) for c in row0_cells]

        # ── Main KV info table (Procedure Name / Description / Category) ──────
        # These tables have <th> for each label but NOT an all-<th> header row.
        tds_in_rows = [tr.find_all(["td", "th"]) for tr in rows]
        first_keys = {tds[0].get_text(strip=True) for tds in tds_in_rows if tds}
        if (not all_th_header
                and first_keys & PROCEDURE_KV_KEYS
                and not any("Title" in h for h in headers)):
            kv = parse_kv_table(tbl)
            for k, v in kv.items():
                canonical = _procedure_key(k)
                if canonical not in data and v:
                    data[canonical] = v
            continue

        # ── Forms table: all-<th> header row and has "Title" column ──────────
        if all_th_header and "Title" in headers:
            for row_d in parse_data_table(tbl):
                if any(row_d.values()):
                    parts = []
                    for col in ("Title", "Description", "Created Date", "Updated Date", "Issued By"):
                        if col in row_d and row_d[col]:
                            parts.append(f"{col}: {row_d[col]}")
                    if parts:
                        forms_list.append(" | ".join(parts))
            continue

        # ── Measures table: all-<th> header row with "Name" + "Measure Type" ─
        if all_th_header and "Name" in headers and "Measure Type" in headers:
            for row_d in parse_data_table(tbl):
                parts = []
                for col in ("Name", "Measure Type", "Agency", "Description",
                            "Comments", "Legal Document", "Validity To", "Measure Class"):
                    if col in row_d and row_d[col]:
                        parts.append(f"{col}: {row_d[col]}" if col != "Name" else row_d[col])
                if parts:
                    assoc_measures.append(" | ".join(parts))
            continue

        # ── Products table ────────────────────────────────────────────────────
        if any("Product" in h for h in headers):
            for row_d in parse_data_table(tbl):
                prod = _build_product(row_d, "Procedure", pid, url)
                if prod:
                    products.append(prod)

    data["Forms"]               = " ;; ".join(forms_list)
    data["Associated Measures"] = " || ".join(assoc_measures)
    return data, products


def _procedure_key(raw):
    mapping = {
        "Name": "Procedure Name",
        "Procedure Description": "Description",
    }
    return mapping.get(raw, raw)

# ── Product builder ───────────────────────────────────────────────────────────

def _build_product(row_d, source_type, source_id, source_url):
    prod = {
        "Source Type": source_type,
        "Source ID":   source_id,
        "Source URL":  source_url,
        "Product Name":           row_d.get("Product Name",          row_d.get("Name", "")),
        "Product Family":         row_d.get("Product Family",        row_d.get("Family", "")),
        "Product Technical Name": row_d.get("Product Technical Name",row_d.get("Technical Name", "")),
        "Brand Name":             row_d.get("Brand Name",            row_d.get("Brand", "")),
        "Comments":               row_d.get("Comments",              row_d.get("Comment", "")),
        "File":                   row_d.get("File",                  row_d.get("Attachment", "")),
    }
    if any(prod[k] for k in ("Product Name", "Product Family", "Brand Name")):
        return prod
    return None

# ── CSV helpers ───────────────────────────────────────────────────────────────

def load_done_ids(filepath, id_col):
    """Return set of IDs already written to an output file."""
    done = set()
    if not os.path.exists(filepath):
        return done
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                val = row.get(id_col, "").strip()
                if val:
                    done.add(val)
    except Exception:
        pass
    return done

def open_csv_append(filepath, fieldnames):
    """Open file for append; write header only if file is new/empty."""
    is_new = not os.path.exists(filepath) or os.path.getsize(filepath) == 0
    fh  = open(filepath, "a", newline="", encoding="utf-8")
    w   = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
    if is_new:
        w.writeheader()
    return fh, w

def collect_unique_urls(filepath, url_col):
    """Return ordered list of unique (url, id) tuples preserving first-seen order."""
    seen = {}
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                val = row.get(url_col)
                url = (val or "").strip()
                if url and url not in seen:
                    mid = extract_id_from_url(url)
                    seen[url] = mid
    except FileNotFoundError:
        log.error(f"Input file not found: {filepath}")
    return list(seen.items())   # [(url, id), ...]

# ── Scrape runners ────────────────────────────────────────────────────────────

def run_measures():
    log.info("=== Scraping Measure detail pages ===")
    urls = collect_unique_urls(FILE_MEASURES_IN, "Measure URL")
    log.info(f"  Unique measure URLs : {len(urls)}")

    done_ids = load_done_ids(FILE_MEASURES_OUT, "Measure ID")
    log.info(f"  Already done        : {len(done_ids)}")

    pending = [(url, mid) for url, mid in urls if mid not in done_ids]
    log.info(f"  Pending             : {len(pending)}")

    if not pending:
        log.info("  Nothing to do for measures.")
        return

    mfh, mw = open_csv_append(FILE_MEASURES_OUT, MEASURE_FIELDS)
    pfh, pw  = open_csv_append(FILE_PRODUCTS_OUT, PRODUCT_FIELDS)

    done = 0
    failed = 0

    def _scrape(args):
        url, mid = args
        data, products = parse_measure_page(url, mid)
        return url, mid, data, products

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(_scrape, item): item for item in pending}
        for fut in as_completed(futures):
            url, mid, data, products = fut.result()
            if data:
                mw.writerow(data)
                mfh.flush()
                for prod in products:
                    pw.writerow(prod)
                pfh.flush()
                done += 1
                log.info(f"  [Measure {mid:>4}] OK  products={len(products)}  ({done}/{len(pending)})")
            else:
                failed += 1
                log.warning(f"  [Measure {mid}] FAILED  (total failures: {failed})")

    mfh.close()
    pfh.close()
    log.info(f"  Measures done: {done}  failed: {failed}")


def run_procedures():
    log.info("=== Scraping Procedure detail pages ===")
    urls = collect_unique_urls(FILE_PROCEDURES_IN, "Procedure URL")
    log.info(f"  Unique procedure URLs : {len(urls)}")

    done_ids = load_done_ids(FILE_PROCEDURES_OUT, "Procedure ID")
    log.info(f"  Already done          : {len(done_ids)}")

    pending = [(url, pid) for url, pid in urls if pid not in done_ids]
    log.info(f"  Pending               : {len(pending)}")

    if not pending:
        log.info("  Nothing to do for procedures.")
        return

    pfh_proc, pw_proc = open_csv_append(FILE_PROCEDURES_OUT, PROCEDURE_FIELDS)
    pfh_prod, pw_prod = open_csv_append(FILE_PRODUCTS_OUT, PRODUCT_FIELDS)

    done = 0
    failed = 0

    def _scrape(args):
        url, pid = args
        data, products = parse_procedure_page(url, pid)
        return url, pid, data, products

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(_scrape, item): item for item in pending}
        for fut in as_completed(futures):
            url, pid, data, products = fut.result()
            if data:
                pw_proc.writerow(data)
                pfh_proc.flush()
                for prod in products:
                    pw_prod.writerow(prod)
                pfh_prod.flush()
                done += 1
                log.info(f"  [Procedure {pid:>4}] OK  products={len(products)}  ({done}/{len(pending)})")
            else:
                failed += 1
                log.warning(f"  [Procedure {pid}] FAILED  (total failures: {failed})")

    pfh_proc.close()
    pfh_prod.close()
    log.info(f"  Procedures done: {done}  failed: {failed}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    # Sync from S3 to resume
    sync_data_from_s3(OUT_DIR)
    run_measures()
    # Sync after measures
    sync_data_to_s3(OUT_DIR)
    
    run_procedures()
    # Final sync
    sync_data_to_s3(OUT_DIR)

    log.info("\n====== Summary ======")
    for fpath in (FILE_MEASURES_OUT, FILE_PROCEDURES_OUT, FILE_PRODUCTS_OUT):
        if os.path.exists(fpath):
            with open(fpath, encoding="utf-8") as f:
                n = sum(1 for _ in f) - 1
            log.info(f"  {os.path.basename(fpath)}: {n} data rows")
        else:
            log.info(f"  {os.path.basename(fpath)}: not created (nothing scraped)")
