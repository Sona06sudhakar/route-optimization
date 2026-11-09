
import pandas as pd

df = pd.read_csv("environmental_data_cleaned.csv")

print("TOTAL RECORDS:", len(df))
print("\nCOLUMNS:")
print(df.columns.tolist())

# Convert GPS and sensor columns to numeric
numeric_columns = [
    "latitude", "longitude", "PM1", "PM2.5", "PM10",
    "CO2", "SO2", "NO2", "CO", "O3", "H2S",
    "TEMP.", "HUMI."
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# GPS coverage
gps = df.dropna(subset=["latitude", "longitude"])

print("\nGPS INFORMATION")
print("Records with GPS:", len(gps))
print("Records without GPS:", len(df) - len(gps))

if not gps.empty:
    print("\nLatitude range:", gps["latitude"].min(), "to", gps["latitude"].max())
    print("Longitude range:", gps["longitude"].min(), "to", gps["longitude"].max())
    print("Unique GPS locations:", gps[["latitude", "longitude"]].drop_duplicates().shape[0])

# Missing values
print("\nMISSING VALUES:")
print(df.isnull().sum())

# Sensor readings
print("\nSENSOR DATA SUMMARY:")
print(df[["PM1", "PM2.5", "PM10", "CO2", "SO2",
          "NO2", "CO", "O3", "H2S", "TEMP.", "HUMI."]].describe())

# Show sample records
print("\nFIRST 10 GPS RECORDS:")
print(gps.head(10).to_string(index=False))

# Save records that have valid GPS coordinates
gps.to_csv("environmental_data_with_gps.csv", index=False)

print("\nSaved GPS records to environmental_data_with_gps.csv")
