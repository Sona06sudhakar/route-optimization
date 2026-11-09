
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Load real road network and filtered sensor data
roads = gpd.read_file("surat_road_segments.geojson")
df = pd.read_csv("surat_valid_sensor_data.csv")

# Ensure sensor values are numeric
df["PM2.5"] = pd.to_numeric(df["PM2.5"], errors="coerce")

# Remove rows without usable PM2.5 values
df = df.dropna(subset=["latitude", "longitude", "PM2.5"])

# Create map
fig, ax = plt.subplots(figsize=(13, 11))

# Plot actual Surat roads
roads.plot(
    ax=ax,
    color="lightgray",
    linewidth=0.6,
    zorder=1
)

# Plot sensor readings
scatter = ax.scatter(
    df["longitude"],
    df["latitude"],
    c=df["PM2.5"],
    cmap="RdYlGn_r",
    s=5,
    alpha=0.75,
    vmin=0,
    vmax=df["PM2.5"].quantile(0.95),
    zorder=2
)

# Add color scale
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label("PM2.5 reading (µg/m³; scale capped at 95th percentile)")

ax.set_title("Surat: Actual Road Network and Sensor Journey")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal")
ax.grid(alpha=0.2)

plt.tight_layout()
plt.savefig("surat_sensor_coverage.png", dpi=250)
plt.show()

print("Map saved as surat_sensor_coverage.png")
print("Sensor readings plotted:", len(df))
print("PM2.5 95th percentile:", df["PM2.5"].quantile(0.95))
