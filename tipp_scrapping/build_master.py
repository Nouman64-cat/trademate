"""
build_master.py
===============
Builds a single comprehensive master CSV: master_tipp.csv
One row per HS Code with every scraped column included.

Structure:
  - Product Hierarchy  : Chapter, Sub Chapter, Heading, Sub Heading
  - Tariff Duties      : CD, RD, ACD, FED, ST(VAT), IT, DS, EOC, ERD  (rate + valid from/to)
  - Cess Collection    : Punjab, Sindh, KPK, Balochistan  (import/export/fwd/rev transit)
  - Exemptions         : count + full pipe-delimited detail
  - Anti-Dumping       : rate + validity
  - NTM Measures       : count + full detail (name | type | agency | description | law | validity)
  - Procedures         : count + full detail (name | category | description | url)

Run:
    python build_master.py
"""

import csv
import os
from collections import defaultdict, OrderedDict
from s3_utils import sync_data_from_s3, sync_data_to_s3

OUT_DIR     = "data"
OUTPUT_FILE = os.path.join(OUT_DIR, "master_tipp.csv")

# ── 1. Product hierarchy from master list ─────────────────────────────────────
sync_data_from_s3(OUT_DIR)
print("Loading product hierarchy...")
master_lookup = {}   # {cleaned_code: description}
with open(os.path.join(OUT_DIR, "hs_codes_master.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        code = row["HS Code"].replace(" ", "")
        master_lookup[code] = row["Description"]

hierarchy = {}   # {12-digit: {Chapter, Sub Chapter, Heading, Sub Heading}}
for code12 in master_lookup:
    if len(code12) == 12:
        hierarchy[code12] = {
            "Chapter":     master_lookup.get(code12[:2], ""),
            "Sub Chapter": master_lookup.get(code12[:4], ""),
            "Heading":     master_lookup.get(code12[:6], ""),
            "Sub Heading": master_lookup.get(code12[:8], ""),
        }

# ── 2. Tariffs ────────────────────────────────────────────────────────────────
print("Loading tariffs...")
DUTY_COLS = ["CD", "RD", "ACD", "FED", "ST (VAT)", "IT", "DS", "EOC", "ERD"]
tariffs   = defaultdict(dict)
hs_meta   = {}

with open(os.path.join(OUT_DIR, "tariffs.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs   = row["HS Code"]
        hs_meta[hs] = row["Description"]
        duty = row["Duty"]
        tariffs[hs][duty + "_Rate"]      = row["Tariff Rate"]
        tariffs[hs][duty + "_ValidFrom"] = row["Valid From"]
        tariffs[hs][duty + "_ValidTo"]   = row["Valid To"]

# ── 3. Cess Collection ────────────────────────────────────────────────────────
print("Loading cess...")
PROVINCES = ["Punjab", "Sindh", "KPK", "Balochistan"]
cess = defaultdict(dict)

with open(os.path.join(OUT_DIR, "cess_collection.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs = row["HS Code"]
        hs_meta[hs] = row["Description"]
        p  = row["Province"]
        cess[hs][f"{p}_Import"]     = row["Import"]
        cess[hs][f"{p}_Export"]     = row["Export"]
        cess[hs][f"{p}_FwdTransit"] = row["Forward Transit"]
        cess[hs][f"{p}_RevTransit"] = row["Reverse Transit"]

# ── 4. Exemptions / Concessions ───────────────────────────────────────────────
print("Loading exemptions...")
exemptions = defaultdict(list)

with open(os.path.join(OUT_DIR, "exemption_concessions.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs = row["HS Code"]
        hs_meta[hs] = row["Description"]
        detail = (
            f"{row['Exemption/Concession']} | "
            f"{row['Exemption Description']} | "
            f"Activity: {row['Activity']} | "
            f"Rate: {row['Rate']} | "
            f"Valid: {row['Valid From']} to {row['Valid To']}"
        )
        exemptions[hs].append(detail)

# ── 5. Anti-Dumping ───────────────────────────────────────────────────────────
print("Loading anti-dump...")
antidump = defaultdict(list)

with open(os.path.join(OUT_DIR, "anti_dump_tariffs.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs = row["HS Code"]
        hs_meta[hs] = row["Description"]
        detail = f"{row['Description']} | Rate: {row['Rate']} | Valid: {row['Valid From']} to {row['Valid To']}"
        antidump[hs].append(detail)

# ── 6. NTM Measures ───────────────────────────────────────────────────────────
print("Loading NTM measures...")
measures = defaultdict(list)

with open(os.path.join(OUT_DIR, "measures.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs = row["HS Code"]
        hs_meta[hs] = row["Description"]
        detail = (
            f"{row['Name']} | "
            f"Type: {row['Type']} | "
            f"Agency: {row['Agency']} | "
            f"Law: {row['Law']} | "
            f"Validity: {row['Validity']} | "
            f"URL: {row['Measure URL']}"
        )
        measures[hs].append(detail)

# ── 7. Procedures ─────────────────────────────────────────────────────────────
print("Loading procedures...")
procedures = defaultdict(list)

with open(os.path.join(OUT_DIR, "procedures.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hs = row["HS Code"]
        hs_meta[hs] = row["Description"]
        detail = (
            f"{row['Name']} | "
            f"Category: {row['Category']} | "
            f"{row['Procedure Description'][:120]} | "
            f"URL: {row['Procedure URL']}"
        )
        procedures[hs].append(detail)

# ── Build headers ─────────────────────────────────────────────────────────────
tariff_headers = []
for d in DUTY_COLS:
    tariff_headers += [f"{d}_Rate", f"{d}_ValidFrom", f"{d}_ValidTo"]

cess_headers = []
for p in PROVINCES:
    cess_headers += [
        f"Cess_{p}_Import", f"Cess_{p}_Export",
        f"Cess_{p}_FwdTransit", f"Cess_{p}_RevTransit",
    ]

all_headers = (
    ["HS Code", "Description", "Chapter", "Sub Chapter", "Heading", "Sub Heading"]
    + tariff_headers
    + cess_headers
    + ["Exemptions_Count", "Exemptions_Detail"]
    + ["AntiDump_Count", "AntiDump_Detail"]
    + ["NTM_Measures_Count", "NTM_Measures_Detail"]
    + ["Procedures_Count", "Procedures_Detail"]
)

# ── Write master CSV ──────────────────────────────────────────────────────────
print("Writing master_tipp.csv...")
all_hs = sorted(hs_meta.keys())

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=all_headers, extrasaction="ignore")
    w.writeheader()

    for hs in all_hs:
        hier = hierarchy.get(hs, {})
        row  = {
            "HS Code":     hs,
            "Description": hs_meta[hs],
            "Chapter":     hier.get("Chapter", ""),
            "Sub Chapter": hier.get("Sub Chapter", ""),
            "Heading":     hier.get("Heading", ""),
            "Sub Heading": hier.get("Sub Heading", ""),
        }

        # Tariffs
        for col in tariff_headers:
            row[col] = tariffs[hs].get(col, "")

        # Cess
        for p in PROVINCES:
            row[f"Cess_{p}_Import"]     = cess[hs].get(f"{p}_Import", "")
            row[f"Cess_{p}_Export"]     = cess[hs].get(f"{p}_Export", "")
            row[f"Cess_{p}_FwdTransit"] = cess[hs].get(f"{p}_FwdTransit", "")
            row[f"Cess_{p}_RevTransit"] = cess[hs].get(f"{p}_RevTransit", "")

        # Exemptions
        exs = exemptions.get(hs, [])
        row["Exemptions_Count"]  = len(exs)
        row["Exemptions_Detail"] = " || ".join(exs) if exs else ""

        # Anti-dump
        ads = antidump.get(hs, [])
        row["AntiDump_Count"]  = len(ads)
        row["AntiDump_Detail"] = " || ".join(ads) if ads else ""

        # NTM Measures
        meas = measures.get(hs, [])
        row["NTM_Measures_Count"]  = len(meas)
        row["NTM_Measures_Detail"] = " || ".join(meas) if meas else ""

        # Procedures
        procs = procedures.get(hs, [])
        row["Procedures_Count"]  = len(procs)
        row["Procedures_Detail"] = " || ".join(procs) if procs else ""

        w.writerow(row)

    # Sync result to S3
    sync_data_to_s3(OUT_DIR)

print(f"\nDone.")
print(f"  File    : {OUTPUT_FILE}")
print(f"  HS Codes: {len(all_hs)}")
print(f"  Columns : {len(all_headers)}")
