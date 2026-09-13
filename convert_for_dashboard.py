"""
SIH26162 - Converts your real classified_hotspots.csv into the exact
format the other team's dashboard (dash.py) expects, and saves it as
pair2_classified.csv - the exact filename their dashboard looks for.

Just run this AFTER fire_classifier.py has already run once.
"""

import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------------
# STEP 1: LOAD YOUR REAL CLASSIFIED DATA
# -----------------------------------------------------------------------
df = pd.read_csv("classified_hotspots.csv")

# -----------------------------------------------------------------------
# STEP 2: RENAME COLUMNS TO MATCH WHAT THEIR DASHBOARD EXPECTS
# -----------------------------------------------------------------------

def extract_state(region_text):
    """Pulls just the state name out of a full region string, e.g.
    'Surat-Bharuch-Vadodara corridor, Gujarat, India' -> 'Gujarat'"""
    if not isinstance(region_text, str):
        return "Unknown"
    parts = [p.strip() for p in region_text.split(",")]
    return parts[-2] if len(parts) >= 2 else region_text


if "region" in df.columns:
    state_values = df["region"].apply(extract_state)
else:
    state_values = "Gujarat"  # fallback if running on older single-region data

converted = pd.DataFrame({
    "lat": df["latitude"],
    "lon": df["longitude"],
    "type": df["classification"].replace({
        "Possible Industrial Fire": "Industrial Fire",
        "Wildfire / Natural Fire": "Other/Natural",
        "Other / Unclassified": "Other/Natural",
    }),
    "confidence": df["confidence_percent"],
    "risk_level": df["risk_level"],
    "distance_km": df["distance_to_facility_km"],
    "days_seen": df["days_active"],
    "source": "NASA FIRMS",       # your real data source, same for every row
    "state": state_values,        # now reflects each hotspot's real region
    "detected_on": datetime.now().strftime("%Y-%m-%d"),  # today's date as a placeholder
})

# -----------------------------------------------------------------------
# STEP 3: SAVE WITH THE EXACT FILENAME THEIR DASHBOARD LOOKS FOR
# -----------------------------------------------------------------------
converted.to_csv("pair2_classified.csv", index=False)

print("Done! Converted your data and saved it as pair2_classified.csv\n")
print(converted.to_string(index=False))
