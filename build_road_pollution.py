
import pandas as pd
import geopandas as gpd

# Load real roads and accepted sensor-to-road matches
roads = gpd.read_file("surat_road_segments.geojson")
matches = pd.read_csv("sensor_road_matches_accepted.csv")

# Keep only roads usable by motor vehicles
drivable = [
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "unclassified", "residential", "living_street", "service",
    "motorway_link", "trunk_link", "primary_link",
    "secondary_link", "tertiary_link"
]

roads = roads[
    roads["highway"].astype(str).isin(drivable)
].copy()

# Use a consistent ID format
roads["osm_id"] = roads["osm_id"].astype(str)
matches["osm_id"] = matches["osm_id"].astype(str)

# Convert sensor readings to numbers
sensor_columns = ["PM1", "PM2.5", "PM10"]

for col in sensor_columns:
    matches[col] = pd.to_numeric(matches[col], errors="coerce")

# Remove invalid particulate readings
matches = matches.dropna(subset=["latitude", "longitude", "PM2.5", "PM10"])
matches = matches[
    (matches["PM2.5"] >= 0) & (matches["PM10"] >= 0)
].copy()

# Round coordinates to approximately 1-metre precision.
# This combines repeated readings at practically the same location.
matches["lat_key"] = matches["latitude"].round(5)
matches["lon_key"] = matches["longitude"].round(5)

# Step 1: Calculate median readings at each unique GPS location
location_data = (
    matches.groupby(["osm_id", "lat_key", "lon_key"])
    .agg(
        PM1=("PM1", "median"),
        PM2_5=("PM2.5", "median"),
        PM10=("PM10", "median"),
        raw_readings=("reading_id", "count")
    )
    .reset_index()
)

# Step 2: Aggregate unique locations for each road
road_data = (
    location_data.groupby("osm_id")
    .agg(
        PM1_median=("PM1", "median"),
        PM2_5_median=("PM2_5", "median"),
        PM10_median=("PM10", "median"),
        unique_locations=("lat_key", "count"),
        raw_readings=("raw_readings", "sum")
    )
    .reset_index()
)

# Add pollution information to actual road geometries
roads = roads.merge(road_data, on="osm_id", how="left")

# Classify measurement coverage
roads["measurement_status"] = "unmeasured"

roads.loc[
    roads["unique_locations"].between(1, 2),
    "measurement_status"
] = "limited"

roads.loc[
    roads["unique_locations"] >= 3,
    "measurement_status"
] = "measured"

# Calculate a PM2.5 score from 0 to 100.
# The 95th percentile is used as the upper scaling reference.
p95 = roads["PM2_5_median"].quantile(0.95)

if pd.notna(p95) and p95 > 0:
    roads["pollution_score"] = (
        roads["PM2_5_median"] / p95 * 100
    ).clip(upper=100)
else:
    roads["pollution_score"] = None

# Save road pollution data
roads.to_file(
    "surat_roads_with_pollution.geojson",
    driver="GeoJSON"
)

roads.drop(columns="geometry").to_csv(
    "surat_roads_with_pollution.csv",
    index=False
)

# Summary
print("\nROAD POLLUTION DATA CREATED")
print("Total drivable road features:", len(roads))

print("\nMEASUREMENT COVERAGE:")
print(roads["measurement_status"].value_counts())

print("\nUNIQUE SENSOR LOCATIONS USED:", len(location_data))
print("RAW SENSOR READINGS USED:", int(roads["raw_readings"].sum()))

print("\nPOLLUTION STATISTICS:")
print(roads[[
    "PM2_5_median",
    "PM10_median",
    "pollution_score"
]].describe())

print("\nTOP 10 ROADS BY PM2.5:")
print(
    roads[roads["PM2_5_median"].notna()]
    .sort_values("PM2_5_median", ascending=False)
    [["name", "highway", "PM2_5_median",
      "PM10_median", "unique_locations", "pollution_score"]]
    .head(10)
    .to_string(index=False)
)

print("\nFILES CREATED:")
print("1. surat_roads_with_pollution.geojson")
print("2. surat_roads_with_pollution.csv")
