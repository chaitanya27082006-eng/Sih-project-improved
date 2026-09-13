"""
SIH26162 - Regenerates assets/data.js with your REAL classified hotspot data,
replacing the synthetic sample data that came with the dashboard.

Run this AFTER your normal pipeline (fetch_firms_data.py, fetch_osm_facilities.py,
data_prep.py, fire_classifier.py) has already produced classified_hotspots.csv.

This is a drop-in replacement - it writes the exact same format the website
already expects, so nothing else in the site's code needs to change.
"""

import pandas as pd

# -----------------------------------------------------------------------
# STEP 1: LOAD YOUR REAL CLASSIFIED DATA
# -----------------------------------------------------------------------
df = pd.read_csv("classified_hotspots.csv")

# -----------------------------------------------------------------------
# STEP 2: CONVERT TO THE WEBSITE'S EXPECTED FORMAT
# -----------------------------------------------------------------------
# The website expects a type from exactly these 3 options:
TYPE_MAP = {
    "Industrial Fire": "Industrial Fire",
    "Possible Industrial Fire": "Industrial Fire",
    "Agricultural Burning": "Agricultural Burning",
    "Wildfire / Natural Fire": "Other/Natural",
    "Other / Unclassified": "Other/Natural",
}

# Change this only if you're running on old single-region data with no 'region' column
FALLBACK_REGION_NAME = "Surat-Bharuch-Vadodara corridor, Gujarat, India"
SOURCE_NAME = "NASA FIRMS (VIIRS), live"

rows = []
for _, r in df.iterrows():
    fw_type = TYPE_MAP.get(r["classification"], "Other/Natural")
    region_name = r["region"] if "region" in df.columns and pd.notna(r.get("region")) else FALLBACK_REGION_NAME
    rows.append([
        round(r["latitude"], 4),
        round(r["longitude"], 4),
        fw_type,
        int(r["confidence_percent"]),
        r["risk_level"],
        SOURCE_NAME,
        region_name,
        round(r["distance_to_facility_km"], 1),
        int(r["days_active"]),
    ])

# -----------------------------------------------------------------------
# STEP 3: WRITE THE NEW data.js FILE
# -----------------------------------------------------------------------
lines = []
lines.append("// FireWatch page data. REAL detection feed - generated from our actual pipeline.")
lines.append("// Columns: lat, lon, type, confidence, risk, source, region, distance_km (to nearest mapped industrial site), days_seen")
lines.append("window.FW_DATA = {")
lines.append("  sites: [")
for i, row in enumerate(rows):
    comma = "," if i < len(rows) - 1 else ""
    formatted = [
        str(row[0]), str(row[1]), f'"{row[2]}"', str(row[3]), f'"{row[4]}"',
        f'"{row[5]}"', f'"{row[6]}"', str(row[7]), str(row[8]),
    ]
    lines.append("    [" + ", ".join(formatted) + "]" + comma)
lines.append("  ]")
lines.append("};")

output = "\n".join(lines)

with open("data.js", "w", encoding="utf-8") as f:
    f.write(output)

print(f"Done! Wrote {len(rows)} REAL hotspots into data.js\n")
print("Preview of what was written:\n")
print(output[:800])
print("\n...(truncated preview)..." if len(output) > 800 else "")
print(f"\nNext step: copy this new data.js into your website's assets/ folder, replacing the old one.")
