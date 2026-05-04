"""
combine_output.py
=================
Merges all data CSVs into a single flat file: combined_tariffs.csv
One row per HS Code with all tariff, cess, exemption, anti-dump,
NTM measures and procedures data as columns.

Run any time (mid-scrape or after completion):
    python combine_output.py
"""

import csv
import os
from collections import defaultdict

OUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUT_DIR, "combined_tariffs.csv")

# ── Build commodity hierarchy from master list ────────────────────────────────
# Master list has rows at 2/4/6/8/12-digit levels.  For each 12-digit leaf code
# we look up its parent entries to get Chapter, Sub Chapter, Heading, Sub Heading.
hierarchy = {}   # {hs_code_12: {Chapter, Sub Chapter, Heading, Sub Heading}}
master_lookup = {}  # {cleaned_code: description}

with open(os.path.join(OUT_DIR, "hs_codes_master.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        code = row["HS Code"].replace(" ", "")
        master_lookup[code] = row["Description"]

for code12, desc in master_lookup.items():
    if len(code12) != 12:
        continue
    hierarchy[code12] = {
        "Chapter":     master_lookup.get(code12[:2], ""),
        "Sub Chapter": master_lookup.get(code12[:4], ""),
        "Heading":     master_lookup.get(code12[:6], ""),
        "Sub Heading": master_lookup.get(code12[:8], ""),
    }

# Also load from commodity_details.csv if it exists (adds page-scraped values)
commodity_file = os.path.join(OUT_DIR, "commodity_details.csv")
if os.path.exists(commodity_file):
    with open(commodity_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hs = row["HS Code"].replace(" ", "")
            # Only override if master lookup had nothing
            if hs not in hierarchy:
                hierarchy[hs] = {}
            for col in ("Chapter", "Sub Chapter", "Heading", "Sub Heading"):
                if not hierarchy[hs].get(col) and row.get(col):
                    hierarchy[hs][col] = row[col]

# ── Load tariffs (pivot duty types into columns) ──────────────────────────────
# All duty types: CD, RD, ACD, FED, ST (VAT), IT, DS, EOC, ERD
DUTY_COLS = ["CD", "RD", "ACD", "FED", "ST (VAT)", "IT", "DS", "EOC", "ERD"]

tariffs = defaultdict(dict)   # {hs_code: {col: value}}
hs_meta = {}                  # {hs_code: description}

with open(os.path.join(OUT_DIR, "tariffs.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs = row["HS Code"]
        hs_meta[hs] = row["Description"]
        duty = row["Duty"]
        tariffs[hs][duty + "_Rate"]      = row["Tariff Rate"]
        tariffs[hs][duty + "_ValidFrom"] = row["Valid From"]
        tariffs[hs][duty + "_ValidTo"]   = row["Valid To"]

# ── Load cess (one column per province per direction) ─────────────────────────
PROVINCES = ["Punjab", "Sindh", "KPK", "Balochistan"]
cess = defaultdict(dict)

with open(os.path.join(OUT_DIR, "cess_collection.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs = row["HS Code"]
        hs_meta[hs] = row["Description"]
        p = row["Province"]
        cess[hs][f"{p}_Cess_Import"]     = row["Import"]
        cess[hs][f"{p}_Cess_Export"]     = row["Export"]
        cess[hs][f"{p}_Cess_FwdTransit"] = row["Forward Transit"]
        cess[hs][f"{p}_Cess_RevTransit"] = row["Reverse Transit"]

# ── Load exemptions (summarise as count + pipe-delimited list) ────────────────
exemptions = defaultdict(list)

with open(os.path.join(OUT_DIR, "exemption_concessions.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs = row["HS Code"]
        hs_meta[hs] = row["Description"]
        label = f"{row['Exemption/Concession']}: {row['Rate']}"
        exemptions[hs].append(label)

# ── Load anti-dump ────────────────────────────────────────────────────────────
antidump = {}

with open(os.path.join(OUT_DIR, "anti_dump_tariffs.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs = row["HS Code"]
        hs_meta[hs] = row["Description"]
        antidump[hs] = f"{row['Rate']} ({row['Valid From']} to {row['Valid To']})"

# ── Load NTM Measures (summarise as count + pipe-delimited list) ──────────────
measures_data = defaultdict(list)
ntm_file = os.path.join(OUT_DIR, "measures.csv")
if os.path.exists(ntm_file):
    with open(ntm_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hs = row["HS Code"]
            hs_meta[hs] = row["Description"]
            label = f"{row['Name']} [{row['Type']}] — {row['Agency']}"
            measures_data[hs].append(label)

# ── Load Procedures (summarise as count + pipe-delimited list) ────────────────
procedures_data = defaultdict(list)
proc_file = os.path.join(OUT_DIR, "procedures.csv")
if os.path.exists(proc_file):
    with open(proc_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hs = row["HS Code"]
            hs_meta[hs] = row["Description"]
            label = f"{row['Name']} [{row['Category']}]"
            procedures_data[hs].append(label)

# ── Build combined headers ────────────────────────────────────────────────────
tariff_headers = []
for d in DUTY_COLS:
    tariff_headers += [f"{d}_Rate", f"{d}_ValidFrom", f"{d}_ValidTo"]

cess_headers = []
for p in PROVINCES:
    cess_headers += [
        f"{p}_Cess_Import", f"{p}_Cess_Export",
        f"{p}_Cess_FwdTransit", f"{p}_Cess_RevTransit"
    ]

all_headers = (
    ["HS Code", "Description", "Chapter", "Sub Chapter", "Heading", "Sub Heading"]
    + tariff_headers
    + cess_headers
    + ["Exemptions_Count", "Exemptions_List"]
    + ["AntiDump_Rate"]
    + ["NTM_Measures_Count", "NTM_Measures_List"]
    + ["Procedures_Count", "Procedures_List"]
)

# ── Write combined CSV ────────────────────────────────────────────────────────
all_hs_codes = sorted(hs_meta.keys())

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=all_headers, extrasaction="ignore")
    w.writeheader()
    for hs in all_hs_codes:
        hier = hierarchy.get(hs, {})
        row = {
            "HS Code":     hs,
            "Description": hs_meta[hs],
            "Chapter":     hier.get("Chapter", ""),
            "Sub Chapter": hier.get("Sub Chapter", ""),
            "Heading":     hier.get("Heading", ""),
            "Sub Heading": hier.get("Sub Heading", ""),
        }
        for col in tariff_headers:
            row[col] = tariffs[hs].get(col, "")
        for col in cess_headers:
            row[col] = cess[hs].get(col, "")
        exs = exemptions.get(hs, [])
        row["Exemptions_Count"] = len(exs)
        row["Exemptions_List"]  = " | ".join(exs) if exs else ""
        row["AntiDump_Rate"]    = antidump.get(hs, "")
        meas = measures_data.get(hs, [])
        row["NTM_Measures_Count"] = len(meas)
        row["NTM_Measures_List"]  = " | ".join(meas) if meas else ""
        procs = procedures_data.get(hs, [])
        row["Procedures_Count"] = len(procs)
        row["Procedures_List"]  = " | ".join(procs) if procs else ""
        w.writerow(row)

total = len(all_hs_codes)
print(f"Done. Combined {total} HS codes into: {OUTPUT_FILE}")
print(f"Columns: {len(all_headers)}")
