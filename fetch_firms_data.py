"""
SIH26162 - Pair 1 (Data Team) - Automatic NASA FIRMS Data Download (MULTI-REGION)
-----------------------------------------------------------------------------------
This script downloads REAL fire/heat spot data directly from NASA, automatically,
for SEVERAL real industrial regions across India - not just one - so your map
shows genuine national-scale coverage instead of a single small pocket.

BEFORE RUNNING THIS, YOU NEED A FREE "MAP_KEY" (takes 2 minutes):
  1. Go to: https://firms.modaps.eosdis.nasa.gov/api/area/
  2. Scroll down to "Map Key" section, click "Get MAP_KEY"
  3. Enter your email - NASA emails you a key (a short code) within a minute or two
  4. Paste that key into the MAP_KEY variable below, between the quotes

Then just run this file - it downloads real data for every region below and
combines it into one CSV.
"""

import requests
import pandas as pd
import io

# -----------------------------------------------------------------------
# STEP 1: FILL IN YOUR DETAILS HERE
# -----------------------------------------------------------------------
MAP_KEY = "PASTE_YOUR_FREE_MAP_KEY_HERE"  # <-- replace this with your real key

# SOURCE options (pick one - VIIRS gives more detail/newer satellite):
SOURCE = "VIIRS_SNPP_NRT"

# DAY_RANGE = how many past days of data to fetch (1 to 5 allowed - NASA's max for this API)
DAY_RANGE = 5

# -----------------------------------------------------------------------
# STEP 2: REAL INDIAN INDUSTRIAL REGIONS TO PULL DATA FROM
# -----------------------------------------------------------------------
# Each entry: a real, well-known industrial belt, its bounding box
# (west,south,east,north), and a clean display name used throughout the site.
# Add or remove regions here any time - everything downstream adapts automatically.
REGIONS = [
    {
        "name": "Gujarat, India",
        "bbox": "72.5,20.2,73.5,22.6",
    },
    {
        "name": "Maharashtra, India",
        "bbox": "72.7,18.3,74.3,19.5",
    },
    {
        "name": "Haryana, India",
        "bbox": "76.7,28.0,77.6,29.2",
    },
    {
        "name": "Tamil Nadu, India",
        "bbox": "79.8,12.7,80.4,13.3",
    },
    {
        "name": "West Bengal, India",
        "bbox": "87.8,22.0,88.5,22.9",
    },
]

# -----------------------------------------------------------------------
# STEP 3: FETCH EACH REGION AND COMBINE
# -----------------------------------------------------------------------
all_rows = []

for region in REGIONS:
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{region['bbox']}/{DAY_RANGE}"
    print(f"Requesting real fire data for: {region['name']} ...")

    try:
        response = requests.get(url, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"  -> Connection error for this region: {e}. Skipping.")
        continue

    if response.status_code == 200 and "latitude" in response.text.lower():
        try:
            region_df = pd.read_csv(io.StringIO(response.text))
        except Exception as e:
            print(f"  -> Could not read the data for this region ({e}). Skipping.")
            continue
        region_df["region"] = region["name"]
        all_rows.append(region_df)
        print(f"  -> Success: {len(region_df)} real hotspots found.")
    else:
        print(f"  -> No data or an error for this region (status {response.status_code}). Skipping.")

# -----------------------------------------------------------------------
# STEP 4: SAVE THE COMBINED RESULT
# -----------------------------------------------------------------------
if all_rows:
    combined = pd.concat(all_rows, ignore_index=True)
    combined.to_csv("firms_real_data.csv", index=False)
    print(f"\nDone! Combined {len(combined)} real hotspots across {len(all_rows)} region(s).")
    print("Saved to firms_real_data.csv\n")
    print(combined.head(10).to_string(index=False))
else:
    print(
        "\nNo data was retrieved from any region. Check your MAP_KEY is filled in "
        "correctly and has had a minute to activate, then try again."
    )

