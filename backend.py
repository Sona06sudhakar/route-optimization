
import json
import math
import heapq
import time
from pathlib import Path

import networkx as nx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


# --------------------------------------------------
# APP SETUP
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Surat Pollution-Aware Routing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# LOAD ROAD GRAPH AND GEOJSON
# --------------------------------------------------

with open(BASE_DIR / "surat_road_graph.json", "r", encoding="utf-8") as f:
    data = json.load(f)

G = nx.MultiDiGraph()

for node in data["nodes"]:
    G.add_node(node["id"], **node)

for edge in data["edges"]:
    G.add_edge(
        edge["from"],
        edge["to"],
        key=edge["id"],
        **edge
    )

print(
    "Road graph loaded:",
    G.number_of_nodes(), "nodes,",
    G.number_of_edges(), "edges"
)

ROADS_FILE = BASE_DIR / "surat_roads_with_pollution.geojson"

with open(ROADS_FILE, "r", encoding="utf-8") as f:
    ROADS_GEOJSON = json.load(f)

print("Road GeoJSON loaded:", len(ROADS_GEOJSON["features"]), "features")


# --------------------------------------------------
# REQUEST FORMAT
# --------------------------------------------------

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float

    efficiency: float = Field(default=0.4, ge=0, le=1)
    air_quality: float = Field(default=0.3, ge=0, le=1)
    safety: float = Field(default=0.15, ge=0, le=1)
    smoothness: float = Field(default=0.15, ge=0, le=1)


# --------------------------------------------------
# DISTANCE AND NODE HELPERS
# --------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


def nearest_node(lat, lon):
    best_distance = float("inf")
    best_node_id = None

    for node_id, node_data in G.nodes(data=True):
        distance = haversine(
            lat, lon,
            node_data["lat"], node_data["lon"]
        )

        if distance < best_distance:
            best_distance = distance
            best_node_id = node_id

    return best_distance, best_node_id


def edge_speed(edge):
    return max(float(edge.get("speed_kmh") or 25), 1)


def edge_travel_time_seconds(edge):
    return edge["length_m"] / (edge_speed(edge) * 1000 / 3600)


# --------------------------------------------------
# ROUTE COST CALCULATION
# --------------------------------------------------

def calculate_edge_cost(edge, weights):
    length = edge["length_m"]
    speed = edge_speed(edge)

    # Faster roads receive a lower efficiency cost
    efficiency_factor = 25 / speed

    # Unknown pollution is treated as neutral, not zero
    pollution = edge.get("pollution_score")

    if pollution is None:
        air_factor = 0.5
    else:
        air_factor = float(pollution) / 100

    # These remain neutral until real road-condition
    # and safety observations are available
    safety_factor = 0.5
    smoothness_factor = 0.5

    score = (
        weights["efficiency"] * efficiency_factor
        + weights["air_quality"] * air_factor
        + weights["safety"] * safety_factor
        + weights["smoothness"] * smoothness_factor
    )

    return length * score


def optimized_edge_cost(u, v, parallel_edges, weights):
    return min(
        calculate_edge_cost(edge, weights)
        for edge in parallel_edges.values()
    )


def fastest_edge_cost(u, v, parallel_edges):
    return min(
        edge_travel_time_seconds(edge)
        for edge in parallel_edges.values()
    )



def dijkstra_with_trace(source, target, weights, max_events=150, max_settled=100):
    """
    Run Dijkstra on the real directed multigraph using the same weighted
    edge-cost function as the pollution-aware route.

    The trace stores a bounded sample of events, while the counters cover
    the complete algorithm execution.
    """
    started = time.perf_counter()

    distances = {source: 0.0}
    previous = {}
    priority_queue = [(0.0, source)]
    settled = set()

    settled_order_sample = []
    relaxation_sample = []
    settled_count = 0
    successful_relaxations = 0
    examined_edges = 0

    while priority_queue:
        current_distance, u = heapq.heappop(priority_queue)

        # Ignore stale queue entries and nodes already finalized.
        if u in settled or current_distance > distances.get(u, float("inf")):
            continue

        settled.add(u)
        settled_count += 1

        if len(settled_order_sample) < max_settled:
            settled_order_sample.append({
                "node": u,
                "distance_cost": round(current_distance, 4)
            })

        if u == target:
            break

        for v, parallel_edges in G[u].items():
            if v in settled:
                continue

            examined_edges += 1
            edge_cost = optimized_edge_cost(u, v, parallel_edges, weights)
            new_distance = current_distance + edge_cost
            old_distance = distances.get(v, float("inf"))

            if new_distance < old_distance:
                distances[v] = new_distance
                previous[v] = u
                successful_relaxations += 1
                heapq.heappush(priority_queue, (new_distance, v))

                if len(relaxation_sample) < max_events:
                    relaxation_sample.append({
                        "from_node": u,
                        "to_node": v,
                        "previous_cost": (
                            round(old_distance, 4)
                            if old_distance != float("inf") else None
                        ),
                        "updated_cost": round(new_distance, 4)
                    })

    if target not in distances:
        raise nx.NetworkXNoPath(f"No path between {source} and {target}")

    # Reconstruct the route by following predecessor links backwards.
    path = [target]
    while path[-1] != source:
        path.append(previous[path[-1]])
    path.reverse()

    elapsed_ms = (time.perf_counter() - started) * 1000

    trace = {
        "algorithm": "Dijkstra",
        "description": (
            "Pollution-aware Dijkstra using the normalized user-selected "
            "weights and the real Surat road graph."
        ),
        "total_nodes_settled": settled_count,
        "total_edges_examined": examined_edges,
        "successful_distance_updates": successful_relaxations,
        "execution_time_ms": round(elapsed_ms, 3),
        "settled_nodes_sample": settled_order_sample,
        "distance_updates_sample": relaxation_sample,
        "settled_nodes_sample_limit": max_settled,
        "distance_updates_sample_limit": max_events,
        "trace_is_sampled": (
            settled_count > len(settled_order_sample)
            or successful_relaxations > len(relaxation_sample)
        ),
        "final_path_node_ids": path
    }

    return path, trace


# --------------------------------------------------
# ROUTE GENERATION AND STATISTICS
# --------------------------------------------------

def get_selected_edges(path, edge_cost_function):
    selected_edges = []

    for u, v in zip(path[:-1], path[1:]):
        alternatives = G[u][v]

        best_edge = min(
            alternatives.values(),
            key=edge_cost_function
        )

        selected_edges.append(best_edge)

    return selected_edges


def build_route_result(path, selected_edges):
    distance_m = sum(
        edge["length_m"] for edge in selected_edges
    )

    travel_time_seconds = sum(
        edge_travel_time_seconds(edge)
        for edge in selected_edges
    )

    measured = sum(
        edge.get("measurement_status") == "measured"
        for edge in selected_edges
    )

    limited = sum(
        edge.get("measurement_status") == "limited"
        for edge in selected_edges
    )

    unmeasured = sum(
        edge.get("measurement_status") == "unmeasured"
        for edge in selected_edges
    )

    pollution_values = [
        float(edge["PM2_5"])
        for edge in selected_edges
        if edge.get("measurement_status") == "measured"
        and edge.get("PM2_5") is not None
    ]

    coordinates = [
        {
            "lat": G.nodes[node]["lat"],
            "lon": G.nodes[node]["lon"]
        }
        for node in path
    ]

    total_edges = len(selected_edges)

    return {
        "route": coordinates,

        "statistics": {
            "distance_km": round(distance_m / 1000, 2),
            "estimated_time_min": round(travel_time_seconds / 60, 2),
            "road_edges": total_edges,

            "measured_edges": measured,
            "limited_edges": limited,
            "unmeasured_edges": unmeasured,

            # Strictly fully measured roads
            "measured_coverage_percent": round(
                measured / total_edges * 100, 2
            ) if total_edges else 0,

            # Fully measured + limited measurement roads
            "any_sensor_coverage_percent": round(
                (measured + limited) / total_edges * 100, 2
            ) if total_edges else 0,

            "mean_measured_PM2_5": round(
                sum(pollution_values) / len(pollution_values), 2
            ) if pollution_values else None
        }
    }


# --------------------------------------------------
# ROUTING ENDPOINT
# --------------------------------------------------

@app.post("/api/route")
def find_route(request: RouteRequest):

    weights = {
        "efficiency": request.efficiency,
        "air_quality": request.air_quality,
        "safety": request.safety,
        "smoothness": request.smoothness
    }

    total = sum(weights.values())

    if total == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one routing weight must be greater than zero."
        )

    # Normalize weights
    weights = {
        key: value / total
        for key, value in weights.items()
    }

    # Snap requested start/end points to nearest road graph nodes
    start_distance, start = nearest_node(
        request.start_lat,
        request.start_lon
    )

    end_distance, end = nearest_node(
        request.end_lat,
        request.end_lon
    )

    try:
        # Pollution-aware optimized route with a real Dijkstra execution trace
        optimized_path, dijkstra_trace = dijkstra_with_trace(
            start, end, weights
        )

        # Fastest route based on estimated road speeds
        fastest_path = nx.shortest_path(
            G,
            source=start,
            target=end,
            weight=fastest_edge_cost
        )

    except nx.NetworkXNoPath:
        raise HTTPException(
            status_code=404,
            detail="No connected road route found."
        )

    optimized_edges = get_selected_edges(
        optimized_path,
        lambda edge: calculate_edge_cost(edge, weights)
    )

    fastest_edges = get_selected_edges(
        fastest_path,
        edge_travel_time_seconds
    )

    optimized_result = build_route_result(
        optimized_path,
        optimized_edges
    )

    fastest_result = build_route_result(
        fastest_path,
        fastest_edges
    )

    return {
        # Existing response fields retained
        "route": optimized_result["route"],
        "statistics": optimized_result["statistics"],

        # New fastest-route fields
        "fastest_route": fastest_result["route"],
        "fastest_statistics": fastest_result["statistics"],

        "weights_used": weights,

        # Actual execution details from the optimized Dijkstra run
        "trace": dijkstra_trace,

        "snapping": {
            "start_distance_m": round(start_distance, 2),
            "end_distance_m": round(end_distance, 2)
        },

        "notes": {
            "fastest_route": "Minimizes estimated travel time using road speed data.",
            "optimized_route": "Uses the selected efficiency, air-quality, safety and smoothness weights.",
            "speed_data": "Travel times use estimated road speeds where actual speed limits are unavailable.",
            "safety_smoothness": "Currently neutral because verified road-condition and safety measurements are not available."
        }
    }


# --------------------------------------------------
# REAL ROAD GEOMETRY ENDPOINT
# --------------------------------------------------

@app.get("/api/roads")
def get_roads():
    return JSONResponse(content=ROADS_GEOJSON)


# --------------------------------------------------
# HEALTH AND GRAPH SUMMARY
# --------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "status": "running",
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges()
    }


@app.get("/api/graph-summary")
def graph_summary():
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "weakly_connected_components":
            nx.number_weakly_connected_components(G),
        "road_features": len(ROADS_GEOJSON["features"])
    }
