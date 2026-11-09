
import geopandas as gpd
import pandas as pd
import json
import math
import re

# Load actual roads with pollution information
roads = gpd.read_file("surat_roads_with_pollution.geojson")

# Only roads usable by motor vehicles
drivable = {
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "unclassified", "residential", "living_street", "service",
    "motorway_link", "trunk_link", "primary_link",
    "secondary_link", "tertiary_link"
}

roads = roads[roads["highway"].isin(drivable)].copy()

# Default speeds are estimates, not live traffic speeds
speed_limits = {
    "motorway": 80,
    "trunk": 60,
    "primary": 50,
    "secondary": 40,
    "tertiary": 35,
    "unclassified": 30,
    "residential": 25,
    "living_street": 15,
    "service": 15,
    "motorway_link": 40,
    "trunk_link": 35,
    "primary_link": 30,
    "secondary_link": 25,
    "tertiary_link": 20
}

nodes = {}
edges = []
edge_id = 0


def haversine(a, b):
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 6371000 * 2 * math.asin(math.sqrt(h))


def parse_tags(value):
    if not isinstance(value, str):
        return {}

    return dict(re.findall(r'"([^"]+)"=>"([^"]*)"', value))


def node_id(coord, tags):
    lon = round(float(coord[0]), 7)
    lat = round(float(coord[1]), 7)

    layer = tags.get("layer", "0")

    # Keep bridges and tunnels distinguishable
    if layer == "0":
        if tags.get("bridge", "no") not in ("no", "false"):
            layer = "bridge"
        elif tags.get("tunnel", "no") not in ("no", "false"):
            layer = "tunnel"

    key = f"{lon},{lat}|{layer}"

    if key not in nodes:
        nodes[key] = {
            "id": key,
            "lon": lon,
            "lat": lat,
            "layer": layer
        }

    return key

def add_edge(a, b, road, tags, reverse=False):
    global edge_id


    if reverse:
        a, b = b, a

    start = (float(a[0]), float(a[1]))
    end = (float(b[0]), float(b[1]))

    length = haversine(start, end)

    if length < 0.1:
        return

    highway = str(road["highway"])

    # Use mapped maxspeed if available; otherwise estimate
    speed = speed_limits.get(highway, 25)

    maxspeed = tags.get("maxspeed", "")
    match = re.search(r"\d+", maxspeed)

    if match:
        speed = float(match.group())

    edges.append({
        "id": edge_id,
       "from": node_id(start, tags),
        "to": node_id(end, tags),
        "osm_id": str(road["osm_id"]),
        "name": (
            str(road["name"])
            if pd.notna(road["name"])
            else "Unnamed road"
        ),
        "highway": highway,
        "length_m": round(length, 2),
        "speed_kmh": speed,
        "speed_is_estimated": not bool(match),
        "oneway": tags.get("oneway", "no"),
        "bridge": tags.get("bridge", "no"),
        "tunnel": tags.get("tunnel", "no"),
        "layer": tags.get("layer", "0"),
        "surface": tags.get("surface", "unknown"),
        "smoothness": tags.get("smoothness", "unknown"),
        "PM2_5": (
            float(road["PM2_5_median"])
            if pd.notna(road["PM2_5_median"]) else None
        ),
        "PM10": (
            float(road["PM10_median"])
            if pd.notna(road["PM10_median"]) else None
        ),
        "pollution_score": (
            float(road["pollution_score"])
            if pd.notna(road["pollution_score"]) else None
        ),
        "measurement_status": road["measurement_status"],
        "unique_locations": (
            int(road["unique_locations"])
            if pd.notna(road["unique_locations"]) else 0
        )
    })

    edge_id += 1


# Process every road geometry
for _, road in roads.iterrows():

    geom = road.geometry

    if geom is None or geom.is_empty:
        continue

    tags = parse_tags(road.get("other_tags", ""))

    if geom.geom_type == "LineString":
        lines = [geom]

    elif geom.geom_type == "MultiLineString":
        lines = list(geom.geoms)

    else:
        continue

    for line in lines:

        coords = list(line.coords)

        for i in range(len(coords) - 1):

            a = coords[i]
            b = coords[i + 1]

            oneway = tags.get("oneway", "no").lower()

            if oneway in ("yes", "true", "1"):
                add_edge(a, b, road, tags)

            elif oneway == "-1":
                add_edge(a, b, road, tags, reverse=True)

            else:
                add_edge(a, b, road, tags)
                add_edge(a, b, road, tags, reverse=True)


# Save graph
graph = {
    "nodes": list(nodes.values()),
    "edges": edges
}

with open("surat_road_graph.json", "w", encoding="utf-8") as f:
    json.dump(graph, f)

print("\nROAD GRAPH CREATED")
print("Graph nodes:", len(nodes))
print("Directed road edges:", len(edges))
print("Measured road edges:", sum(
    e["measurement_status"] == "measured" for e in edges
))
print("Limited measurement edges:", sum(
    e["measurement_status"] == "limited" for e in edges
))
print("Unmeasured edges:", sum(
    e["measurement_status"] == "unmeasured" for e in edges
))
print("\nOutput: surat_road_graph.json")
