
import csv

input_file = "environmental_data.csv"
output_file = "environmental_data_cleaned.csv"

with open(input_file, "r", encoding="utf-8-sig") as f:
    lines = f.readlines()

header = [
    "Data", "Time", "latitude", "longitude",
    "PM1", "PM2.5", "PM10", "CO2", "SO2",
    "NO2", "CO", "O3", "H2S", "TEMP.", "HUMI."
]

clean_rows = []
recovered = 0
discarded = 0

for line_no, line in enumerate(lines[1:], start=2):

    line = line.strip()

    # Handle accidentally merged records
    parts = line.split('""2025/')

    for i, part in enumerate(parts):

        if i > 0:
            part = '"2025/' + part

        # Remove surrounding quotation marks
        part = part.strip('"')

        row = part.split('","')

        # Keep only complete 15-column records
        if len(row) == 15:
            clean_rows.append(row)
            if len(parts) > 1:
                recovered += 1
        else:
            discarded += 1
            print(
                f"Skipping incomplete record "
                f"at original line {line_no}: {len(row)} fields"
            )

# Write cleaned dataset
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(clean_rows)

print("\nCLEANING COMPLETE!")
print("Valid records:", len(clean_rows))
print("Recovered records:", recovered)
print("Discarded incomplete records:", discarded)
print("Output file:", output_file)
