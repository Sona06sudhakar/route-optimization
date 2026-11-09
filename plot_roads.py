
import geopandas as gpd
import matplotlib.pyplot as plt

roads = gpd.read_file("surat_road_segments.geojson")

fig, ax = plt.subplots(figsize=(12, 10))

roads.plot(
    ax=ax,
    linewidth=0.5,
    color="darkgreen"
)

ax.set_title("Actual Surat Road Network - OpenStreetMap")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.grid(True)

plt.tight_layout()
plt.savefig("surat_road_map.png", dpi=200)
plt.show()
