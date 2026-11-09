
import pandas as pd

df = pd.read_csv("environmental_data_cleaned.csv")

# Convert coordinates to numbers
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

# Bounding box of our downloaded Surat road network
MIN_LAT, MAX_LAT = 21.1416, 21.2222
MIN_LON, MAX_LON = 72.7550, 72.8499

# Keep only coordinates inside the road network area
valid = df[
    df["latitude"].between(MIN_LAT, MAX_LAT) &
    df["longitude"].between(MIN_LON, MAX_LON)
].copy()

print("TOTAL RECORDS:", len(df))
print("VALID GPS RECORDS INSIDE ROAD MAP:", len(valid))
print("REMOVED RECORDS:", len(df) - len(valid))

print("\nVALID GPS RANGE:")
print("Latitude:", valid["latitude"].min(), "to", valid["latitude"].max())
print("Longitude:", valid["longitude"].min(), "to", valid["longitude"].max())

print("\nUNIQUE GPS LOCATIONS:",
      valid[["latitude", "longitude"]].drop_duplicates().shape[0])

print("\nSAMPLE VALID RECORDS:")
print(valid.head(10).to_string(index=False))

valid.to_csv("surat_valid_sensor_data.csv", index=False)

print("\nSaved as surat_valid_sensor_data.csv")
