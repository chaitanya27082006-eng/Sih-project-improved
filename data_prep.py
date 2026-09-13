"""
SIH26162 - Pair 1 (Data Team) - Data Collection & Preparation
-----------------------------------------------------------------
This script takes:
  1. Fire/heat spot data (from NASA FIRMS)
  2. Factory/facility location data (from OpenStreetMap)

...and combines them into ONE clean file that Pair 2's classifier can use directly.

It calculates, for every heat spot:
  - distance_to_facility_km : how far it is from the nearest known factory
  - days_active             : how many different days this same spot has appeared
  - land_cover_type         : a simple guess (industrial / farmland / forest / other)

HOW TO USE WITH YOUR REAL DATA (once you've downloaded it):
  1. Download your FIRMS CSV from firms.modap.eosdis.nasa.gov/map
     -> Replace the "firms_data" sample block below with:
        firms_df = pd.read_csv("your_firms_file.csv")
     (Real FIRMS files already have columns named latitude, longitude, acq_date, frp - matching what we use here)

  2. Get your factory/facility list from OpenStreetMap (via Overpass Turbo)
     -> Replace the "facilities_data" sample block below with:
        facilities_df = pd.read_csv("your_facilities_file.csv")
     (Make sure it has at least: name, latitude, longitude columns)

Everything else in this script runs exactly the same either way.
"""

import pandas as pd
import math

# -----------------------------------------------------------------------
# STEP 1: LOAD YOUR REAL FIRMS DATA (downloaded via fetch_firms_data.py)
# -----------------------------------------------------------------------
firms_df = pd.read_csv("firms_real_data.csv")

# Real FIRMS files use lowercase column names, but just in case, make sure
# our column names match exactly what the rest of this script expects.
firms_df.columns = [c.lower() for c in firms_df.columns]

# Keep only the columns we actually need (including 'region', now that we
# pull data from several real regions instead of just one)
keep_cols = ["latitude", "longitude", "acq_date", "frp"]
if "region" in firms_df.columns:
    keep_cols.append("region")
firms_df = firms_df[keep_cols]

# -----------------------------------------------------------------------
# STEP 2: LOAD YOUR REAL FACILITY DATA (downloaded via fetch_osm_facilities.py)
# -----------------------------------------------------------------------
facilities_df = pd.read_csv("osm_real_facilities.csv")


# -----------------------------------------------------------------------
# STEP 3: DISTANCE CALCULATION (no extra install needed - plain math formula)
# -----------------------------------------------------------------------
def distance_km(lat1, lon1, lat2, lon2):
    """
    Calculates the distance in kilometers between two lat/lon points on Earth.
    This is called the 'haversine formula' - it accounts for the Earth being round.
    """
    R = 6371  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def nearest_facility_distance(lat, lon, facilities_df, region=None):
    """
    Finds the closest facility to a given point, and returns the distance in km.
    If a region is given and facility data has a matching 'region' column,
    we only compare against facilities in that same real region - this is both
    faster and more accurate now that we cover several regions across India.
    """
    candidates = facilities_df
    if region is not None and "region" in facilities_df.columns:
        same_region = facilities_df[facilities_df["region"] == region]
        if len(same_region) > 0:
            candidates = same_region
    distances = candidates.apply(
        lambda f: distance_km(lat, lon, f["latitude"], f["longitude"]), axis=1
    )
    return distances.min()


firms_df["distance_to_facility_km"] = firms_df.apply(
    lambda row: round(
        nearest_facility_distance(
            row["latitude"], row["longitude"], facilities_df, row.get("region")
        ),
        2,
    ),
    axis=1,
)


# -----------------------------------------------------------------------
# STEP 4: "DAYS ACTIVE" CALCULATION (how many different days this spot repeated)
# -----------------------------------------------------------------------
# We group nearby points together (within ~0.01 degrees, roughly 1 km) and treat
# them as "the same spot" if they're close together, then count unique dates.

def round_coord(value):
    """Rounds a coordinate so nearby points are grouped as the same location."""
    return round(value, 2)  # ~1.1 km grid


firms_df["grid_lat"] = firms_df["latitude"].apply(round_coord)
firms_df["grid_lon"] = firms_df["longitude"].apply(round_coord)

group_cols = ["grid_lat", "grid_lon"]
if "region" in firms_df.columns:
    group_cols = ["region"] + group_cols  # keeps grouping correct even if two regions share a coordinate grid cell by coincidence

days_active_lookup = (
    firms_df.groupby(group_cols)["acq_date"]
    .nunique()
    .reset_index()
    .rename(columns={"acq_date": "days_active"})
)

firms_df = firms_df.merge(days_active_lookup, on=group_cols, how="left")


# -----------------------------------------------------------------------
# STEP 5: LAND COVER TYPE (simple placeholder guess)
# -----------------------------------------------------------------------
# NOTE: A real land-cover dataset (like ESA WorldCover) would give this properly.
# For now, as a reasonable placeholder for the demo, we guess based on distance:
#   - very close to a facility -> "industrial"
#   - otherwise -> "other" (your team can manually correct specific points if needed)
# If you have time later, replace this with a real land-cover lookup.

def guess_land_cover(distance):
    if distance <= 2:
        return "industrial"
    elif distance <= 8:
        return "farmland"
    else:
        return "forest"


firms_df["land_cover_type"] = firms_df["distance_to_facility_km"].apply(guess_land_cover)


# -----------------------------------------------------------------------
# STEP 6: CLEAN UP AND SAVE - one row per unique location (not per date)
# -----------------------------------------------------------------------
# Pair 2's classifier expects ONE row per hotspot location, so we keep the most
# recent detection per grid location, along with its days_active count.

dedup_cols = ["grid_lat", "grid_lon"]
if "region" in firms_df.columns:
    dedup_cols = ["region"] + dedup_cols

final_df = (
    firms_df.sort_values("acq_date")
    .drop_duplicates(subset=dedup_cols, keep="last")
    .reset_index(drop=True)
)

final_df["hotspot_id"] = range(1, len(final_df) + 1)

final_cols = [
    "hotspot_id",
    "latitude",
    "longitude",
    "distance_to_facility_km",
    "days_active",
    "land_cover_type",
    "frp",
]
if "region" in final_df.columns:
    final_cols.append("region")

final_df = final_df[final_cols]

print("\n=== PREPARED DATA (ready for Pair 2's classifier) ===\n")
print(final_df.to_string(index=False))

final_df.to_csv("pair1_prepared_data.csv", index=False)
print("\nSaved to pair1_prepared_data.csv - send this file to Pair 2 (and the Team Leader).")
