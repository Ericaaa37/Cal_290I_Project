# app.py
from flask import Flask, send_from_directory, request, jsonify
import math
import itertools
import time

app = Flask(__name__, static_folder="static")

def haversine_km(a, b):
    # a, b are (lat, lng) in degrees, returns distance in kilometers
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    R = 6371.0
    aa = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(aa), math.sqrt(1-aa))
    return R * c

# def total_distance_km(route):
    # d = 0.0
    # for i in range(len(route)-1):
        # d += haversine_km((route[i]["lat"], route[i]["lng"]), (route[i+1]["lat"], route[i+1]["lng"]))
    # return d

def total_distance_km(route, closed=True):
    d = 0.0
    n = len(route)
    if n < 2:
        return 0.0
    for i in range(n - 1):
        d += haversine_km(
            (route[i]["lat"], route[i]["lng"]),
            (route[i + 1]["lat"], route[i + 1]["lng"])
        )
    # TSP tour closed
    if closed:
        d += haversine_km(
            (route[-1]["lat"], route[-1]["lng"]),
            (route[0]["lat"], route[0]["lng"])
        )
    return d


def solve_tsp_bruteforce(points):
    # find best permutation that minimize path length
    best = None
    best_d = float("inf")
    for perm in itertools.permutations(points):
        d = total_distance_km(perm, closed=True)
        if d < best_d:
            best_d = d
            best = perm
    return list(best), best_d

def nearest_neighbor(points):
    # simple nearest neighbor heuristic, returns order as list
    if not points:
        return []
    unvisited = points.copy()
    route = [unvisited.pop(0)]  # start at first point, could choose best start strategy
    while unvisited:
        last = route[-1]
        # find nearest
        idx, _ = min(enumerate(unvisited), key=lambda it: haversine_km((last["lat"],last["lng"]), (it[1]["lat"], it[1]["lng"])))
        route.append(unvisited.pop(idx))
    return route

def two_opt(route):
    # simple 2-opt for path improvement
    improved = True
    while improved:
        improved = False
        n = len(route)
        for i in range(0, n-2):
            for j in range(i+2, n):
                # try reversing route[i+1:j+1]
                new_route = route[:i+1] + list(reversed(route[i+1:j+1])) + route[j+1:]
                if total_distance_km(new_route, closed=True) + 1e-9 < total_distance_km(route, closed=True):
                    route = new_route
                    improved = True
    return route

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.post("/api/tsp")
def tsp():
    data = request.get_json() or {}
    points = data.get("points", [])
    n = len(points)
    if n < 2:
        return jsonify({"error":"need at least 2 points"}), 400
    if n > 12:
        return jsonify({"error":"too many points, limit is 12 for server-side brute/heuristic"},), 400

    # choose solver
    start_time = time.time()
    if n <= 8:
        route, dist_km = solve_tsp_bruteforce(points)
        method = "bruteforce"
    else:
        # heuristic for larger n (threshold: 6)
        route = nearest_neighbor(points)
        route = two_opt(route)
        dist_km = total_distance_km(route, closed=True)
        method = "nn_2opt"
    elapsed = time.time() - start_time

    if route and len(route) > 0:
        closed_route = route + [route[0]]
    else:
        closed_route = route
        
    return jsonify({
        "route": closed_route,
        "distance_km": dist_km,
        "method": method,
        "time_s": elapsed
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
