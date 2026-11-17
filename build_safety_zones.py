import json
import re
from collections import Counter
from pathlib import Path

import geopandas as gpd
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
SOURCE_FILE = BASE_DIR / "planet_72.780,21.165_72.841,21.207.gpkg"
OUTPUT_FILE = BASE_DIR / "surat_safety_zones.geojson"

TAG_PATTERN = re.compile(r'"([^"]+)"=>"([^"]*)"')
EDUCATION_AMENITIES = {"school", "kindergarten", "college", "university"}
HEALTHCARE_AMENITIES = {"hospital", "clinic", "doctors", "dentist"}


def parse_tags(value):
    if not isinstance(value, str):
        return {}
    return dict(TAG_PATTERN.findall(value))


def first_text(*values):
    for value in values:
        if value is None or pd.isna(value):
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def zone_category(amenity):
    if amenity in EDUCATION_AMENITIES:
        return "education"
    if amenity in HEALTHCARE_AMENITIES:
        return "healthcare"
    return None


def main():
    layers = set(gpd.list_layers(SOURCE_FILE)["name"])
    features = []
    seen = set()

    for layer_name in ("points", "multipolygons"):
        if layer_name not in layers:
            continue

        frame = gpd.read_file(SOURCE_FILE, layer=layer_name)
        if frame.crs and frame.crs.to_epsg() != 4326:
            frame = frame.to_crs(epsg=4326)

        for _, row in frame.iterrows():
            tags = parse_tags(row.get("other_tags"))
            amenity = first_text(row.get("amenity"), tags.get("amenity"))
            category = zone_category(amenity)
            geometry = row.geometry
            if not category or geometry is None or geometry.is_empty:
                continue

            point = geometry if geometry.geom_type == "Point" else geometry.representative_point()
            osm_id = first_text(row.get("osm_id"), row.get("id"))
            key = (layer_name, osm_id, category)
            if key in seen:
                continue
            seen.add(key)

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(point.x), float(point.y)]
                },
                "properties": {
                    "id": f"{layer_name}:{osm_id}",
                    "name": first_text(row.get("name"), tags.get("name"), amenity.title()),
                    "category": category,
                    "amenity": amenity,
                    "osm_id": osm_id
                }
            })

    if not features:
        raise SystemExit("No school or healthcare POIs found in the GeoPackage.")

    collection = {"type": "FeatureCollection", "features": features}
    OUTPUT_FILE.write_text(json.dumps(collection, ensure_ascii=True), encoding="utf-8")
    print(f"Wrote {len(features)} safety zones to {OUTPUT_FILE.name}")
    print("By category:", dict(Counter(feature["properties"]["category"] for feature in features)))


if __name__ == "__main__":
    main()