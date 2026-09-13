"""
SIH26162 - Pair 1 (Data Team) - Automatic OpenStreetMap Facility Download (MULTI-REGION)
--------------------------------------------------------------------------------------------
This script downloads REAL factory/industrial location data from OpenStreetMap,
automatically, for the SAME 5 regions as fetch_firms_data.py, so both files
cover the same real, national-scale area.

No API key needed for this one - OpenStreetMap's data is fully free and open.
"""

import requests
import pandas as pd
import time

# -----------------------------------------------------------------------
# STEP 1: SAME 5 REGIONS AS fetch_firms_data.py
# -----------------------------------------------------------------------
# Format here: south, west, north, east (matches this script's query style)
REGIONS = [
    {"name": "Gujarat, India", "bbox": (20.2, 72.5, 22.6, 73.5)},
    {"name": "Maharashtra, India", "bbox": (18.3, 72.7, 19.5, 74.3)},
    {"name": "Haryana, India", "bbox": (28.0, 76.7, 29.2, 77.6)},
    {"name": "Tamil Nadu, India", "bbox": (12.7, 79.8, 13.3, 80.4)},
    {"name": "West Bengal, India", "bbox": (22.0, 87.8, 22.9, 88.5)},
]

headers = {
    "User-Agent": "SIH26162-StudentProject/1.0 (educational hackathon prototype)"
}

servers = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

all_facilities = []
failed_regions = []


def fetch_region(region, pause_before=0):
    """Tries to fetch one region's facilities. Returns True if it succeeded."""
    if pause_before:
        print(f"  -> Waiting {pause_before}s before trying (avoids rate-limits)...")
        time.sleep(pause_before)

    south, west, north, east = region["bbox"]
    overpass_query = f"""
    [out:json][timeout:60];
    (
      node["landuse"="industrial"]({south},{west},{north},{east});
      way["landuse"="industrial"]({south},{west},{north},{east});
      node["man_made"="works"]({south},{west},{north},{east});
      node["power"="plant"]({south},{west},{north},{east});
    );
    out center;
    """

    response = None
    for server in servers:
        try:
            response = requests.post(server, data={"data": overpass_query}, headers=headers, timeout=60)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            continue
        time.sleep(2)  # brief pause before trying the backup server

    if response is not None and response.status_code == 200:
        try:
            result = response.json()
        except Exception:
            print("  -> Could not read the response for this region.")
            return False
        elements = result.get("elements", [])
        count = 0
        for el in elements:
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            name = el.get("tags", {}).get("name", "Unnamed Facility")
            if lat and lon:
                all_facilities.append({
                    "name": name,
                    "latitude": lat,
                    "longitude": lon,
                    "region": region["name"],
                })
                count += 1
        print(f"  -> Success: {count} real facilities found.")
        return True
    else:
        status = response.status_code if response is not None else "no response"
        print(f"  -> This region's request failed (status: {status}).")
        return False


for i, region in enumerate(REGIONS):
    print(f"Requesting real facility data for: {region['name']} ...")
    ok = fetch_region(region)
    if not ok:
        failed_regions.append(region)
    if i < len(REGIONS) - 1:
        time.sleep(8)  # pause between regions so we don't get rate-limited

# -----------------------------------------------------------------------
# STEP 1b: RETRY ANY REGIONS THAT FAILED THE FIRST TIME
# -----------------------------------------------------------------------
if failed_regions:
    print(f"\n{len(failed_regions)} region(s) failed on the first try - waiting, then retrying...")
    time.sleep(20)
    still_failed = []
    for region in failed_regions:
        print(f"Retrying: {region['name']} ...")
        ok = fetch_region(region, pause_before=5)
        if not ok:
            still_failed.append(region["name"])
    if still_failed:
        print(f"\nStill couldn't reach: {', '.join(still_failed)}")
        print("You can just run this script again in a minute to try those specific regions again.")

# -----------------------------------------------------------------------
# STEP 2: SAVE THE COMBINED RESULT
# -----------------------------------------------------------------------
if all_facilities:
    facilities_df = pd.DataFrame(all_facilities)
    facilities_df.to_csv("osm_real_facilities.csv", index=False)
    print(f"\nDone! Combined {len(facilities_df)} real facilities across all regions.")
    print("Saved to osm_real_facilities.csv\n")
    print(facilities_df.head(10).to_string(index=False))
else:
    print(
        "\nNo facilities were found in any region. This is unusual - try running "
        "the script again, as Overpass servers occasionally time out under load."
    )
