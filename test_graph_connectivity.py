
import json
import math
import networkx as nx

# Load generated graph
with open("surat_road_graph.json", "r", encoding="utf-8") as f:
    data = json.load(f)

G = nx.DiGraph()

for node in data["nodes"]:
    G.add_node(node["id"], **node)

for edge in data["edges"]:
    G.add_edge(
        edge["from"],
        edge["to"],
        length=edge["length_m"]
    )

# Approximate locations
locations = {
    "SVNIT": (21.1654602, 72.7854551),
    "Surat Railway Station": (21.205538, 72.840954)
}


def distance(lat1, lon1, lat2, lon2):
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
    candidates = []

    for node_id, node in G.nodes(data=True):
        d = distance(lat, lon, node["lat"], node["lon"])
        candidates.append((d, node_id))

    return min(candidates)


# Find nearest graph nodes
start_dist, start = nearest_node(*locations["SVNIT"])
end_dist, end = nearest_node(*locations["Surat Railway Station"])

print("GRAPH NODES:", G.number_of_nodes())
print("GRAPH EDGES:", G.number_of_edges())

print("\nCONNECTED COMPONENTS:")
print("Weakly connected:", nx.number_weakly_connected_components(G))
print("Strongly connected:", nx.number_strongly_connected_components(G))

print("\nNEAREST GRAPH NODES:")
print(f"SVNIT: {start_dist:.2f} metres away")
print(f"Railway Station: {end_dist:.2f} metres away")

print("\nROUTE CONNECTIVITY:")

if nx.has_path(G, start, end):
    path = nx.shortest_path(G, start, end, weight="length")
    length = nx.shortest_path_length(G, start, end, weight="length")

    print("SVNIT -> Railway Station: CONNECTED")
    print("Path nodes:", len(path))
    print("Approximate road distance:", round(length / 1000, 2), "km")

else:
    print("SVNIT -> Railway Station: NOT CONNECTED")

if nx.has_path(G, end, start):
    print("Railway Station -> SVNIT: CONNECTED")
else:
    print("Railway Station -> SVNIT: NOT CONNECTED")
