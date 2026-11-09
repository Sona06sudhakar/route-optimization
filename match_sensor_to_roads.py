
import pandas as pd
import geopandas as gpd

# Load data
roads = gpd.read_file("surat_road_segments.geojson")
sensors = pd.read_csv("surat_valid_sensor_data.csv")

# Keep drivable roads only
drivable_roads = [
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "unclassified", "residential", "living_street", "service",
    "motorway_link", "trunk_link", "primary_link",
    "secondary_link", "tertiary_link"
]

roads = roads[
    roads["highway"].astype(str).isin(drivable_roads)
].copy()

# Clean coordinates
sensors["latitude"] = pd.to_numeric(sensors["latitude"], errors="coerce")
sensors["longitude"] = pd.to_numeric(sensors["longitude"], errors="coerce")
sensors = sensors.dropna(subset=["latitude", "longitude"]).copy()

# Give every sensor reading a unique ID
sensors["reading_id"] = range(len(sensors))

# Convert GPS coordinates into points
points = gpd.GeoDataFrame(
    sensors,
    geometry=gpd.points_from_xy(
        sensors["longitude"],
        sensors["latitude"]
    ),
    crs="EPSG:4326"
)

# Convert to metres using UTM Zone 43N
points = points.to_crs("EPSG:32643")
roads = roads.to_crs("EPSG:32643")

roads = roads[["osm_id", "name", "highway", "geometry"]]

# Find nearest road
matched = gpd.sjoin_nearest(
    points,
    roads,
    how="left",
    distance_col="distance_m"
)

# Keep only one nearest road per sensor reading
matched = (
    matched.sort_values("distance_m")
    .drop_duplicates(subset="reading_id", keep="first")
)

# Accept matches within 30 metres
accepted = matched[matched["distance_m"] <= 30].copy()
rejected = matched[matched["distance_m"] > 30].copy()

print("TOTAL SENSOR READINGS:", len(sensors))
print("UNIQUE MATCHES:", len(matched))
print("ACCEPTED MATCHES (within 30m):", len(accepted))
print("UNASSIGNED READINGS:", len(rejected))

print("\nACCEPTED MATCH DISTANCES:")
print(accepted["distance_m"].describe())

print("\nMATCHING QUALITY:")
for distance in [5, 10, 20, 30]:
    count = (accepted["distance_m"] <= distance).sum()
    print(f"Within {distance}m: {count}")

# Save results
accepted.drop(columns="geometry").to_csv(
    "sensor_road_matches_accepted.csv", index=False
)

rejected.drop(columns="geometry").to_csv(
    "sensor_road_matches_rejected.csv", index=False
)

print("\nFILES CREATED:")
print("1. sensor_road_matches_accepted.csv")
print("2. sensor_road_matches_rejected.csv")
