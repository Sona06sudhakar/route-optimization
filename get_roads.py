
import osmnx as ox
import geopandas as gpd

print("Reading downloaded Surat map...")

file_path = "planet_72.780,21.165_72.841,21.207.gpkg"

# Check available layers
layers = gpd.list_layers(file_path)
print("Available layers:")
print(layers)

# Read the road data
roads = gpd.read_file(file_path, layer="lines")

print("\nRoad data loaded!")
print("Total road features:", len(roads))
print("Available columns:")
print(roads.columns.tolist())

# Keep drivable roads
if "highway" in roads.columns:
    roads = roads[
        roads["highway"].notna()
    ]

# Save road information
roads.to_csv("surat_road_segments.csv", index=False)

# Save geographic data
roads.to_file("surat_road_segments.geojson", driver="GeoJSON")

print("\nRoad files exported successfully!")
print("Total roads:", len(roads))
