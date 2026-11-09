
import geopandas as gpd

roads = gpd.read_file("surat_road_segments.geojson")

print("\n--- ROAD TYPES ---")
print(roads["highway"].value_counts().head(20))

print("\n--- ROAD NAMES ---")
print(roads["name"].dropna().head(20))

print("\n--- OTHER TAGS ---")
print(roads["other_tags"].dropna().head(10))

print("\n--- MAP COVERAGE ---")
print("Bounds:", roads.total_bounds)

print("\n--- COORDINATE SYSTEM ---")
print(roads.crs)
