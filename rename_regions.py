"""
SIH26162 - Fixes the region names in your already-downloaded real data files,
so the website's "Choose what to analyse" search actually works.

Why this is needed: the website looks up REAL administrative boundaries using
OpenStreetMap's place database. Descriptive names like "Surat-Bharuch-Vadodara
corridor, Gujarat, India" aren't official place names, so that lookup fails.
Simple real state names like "Gujarat, India" work correctly.

This does NOT re-download anything from NASA or OSM - it just relabels the
region column in your two already-fetched real data files.

Run this once, then re-run data_prep.py, fire_classifier.py, and
generate_dashboard_data.py as usual (no need to re-run the two fetch scripts).
"""

import pandas as pd

# Maps your old descriptive region names to simple, real, recognizable ones
RENAME_MAP = {
    "Surat-Bharuch-Vadodara corridor, Gujarat, India": "Gujarat, India",
    "Mumbai-Pune industrial belt, Maharashtra, India": "Maharashtra, India",
    "Delhi NCR industrial belt, Haryana, India": "Haryana, India",
    "Chennai-Sriperumbudur corridor, Tamil Nadu, India": "Tamil Nadu, India",
    "Kolkata-Haldia industrial belt, West Bengal, India": "West Bengal, India",
}

for filename in ["firms_real_data.csv", "osm_real_facilities.csv"]:
    df = pd.read_csv(filename)
    if "region" in df.columns:
        before = df["region"].unique().tolist()
        df["region"] = df["region"].replace(RENAME_MAP)
        after = df["region"].unique().tolist()
        df.to_csv(filename, index=False)
        print(f"{filename}: updated {len(df)} rows")
        print(f"  Old region names: {before}")
        print(f"  New region names: {after}\n")
    else:
        print(f"{filename}: no 'region' column found - skipped")

print("Done! Now re-run: python data_prep.py, then python fire_classifier.py")
