import time
import random
import numpy as np
from python_tsp.heuristics import solve_tsp_local_search

from app import haversine_km, nearest_neighbor, two_opt, total_distance_km


def make_points(n, seed=0, bbox=(37.83, 37.92, -122.33, -122.20)):
    random.seed(seed)
    lat_min, lat_max, lon_min, lon_max = bbox
    return [
        {
            "lat": random.uniform(lat_min, lat_max),
            "lng": random.uniform(lon_min, lon_max),
        }
        for _ in range(n)
    ]


def distance_matrix_from_points(points):
    n = len(points)
    D = np.zeros((n, n), dtype=float)

    for i in range(n):
        a = (points[i]["lat"], points[i]["lng"])
        for j in range(n):
            if i == j:
                continue
            b = (points[j]["lat"], points[j]["lng"])
            D[i, j] = haversine_km(a, b)

    return D


def run_one_instance(points):
    D = distance_matrix_from_points(points)

    # (1) Our backend heuristic
    t0 = time.perf_counter()
    route = nearest_neighbor(points)
    route = two_opt(route)
    dist_ours = total_distance_km(route, closed=True)
    t_ours = time.perf_counter() - t0

    # (2) python-tsp local search heuristic
    t0 = time.perf_counter()
    perm_ls, dist_ls = solve_tsp_local_search(D)
    t_ls = time.perf_counter() - t0

    return {
        "n": len(points),
        "t_ours_s": t_ours,
        "dist_ours_km": float(dist_ours),
        "t_ls_s": t_ls,
        "dist_ls_km": float(dist_ls),
        "delta_km": float(dist_ours - dist_ls),
        "delta_pct": (dist_ours - dist_ls) / dist_ls if dist_ls > 0 else np.nan,
    }


def summarize(rows, key):
    vals = np.array([r[key] for r in rows], dtype=float)
    return {
        "median": float(np.median(vals)),
        "p95": float(np.percentile(vals, 95)),
        "mean": float(np.mean(vals)),
    }


def main():
    Ns = [6, 8, 10, 12]
    trials_per_n = 50

    all_results = []

    for n in Ns:
        for s in range(trials_per_n):
            points = make_points(n, seed=1000 * n + s)
            all_results.append(run_one_instance(points))

    for n in Ns:
        rows = [r for r in all_results if r["n"] == n]
        

        time_ours = summarize(rows, "t_ours_s")
        time_ls = summarize(rows, "t_ls_s")
        dist_delta = summarize(rows, "delta_pct")

        print(f"\n=== n = {n}, trials = {len(rows)} ===")
        print(
            f"Our heuristic runtime (ms):        "
            f"median={time_ours['median'] * 1000:.2f}, "
            f"p95={time_ours['p95'] * 1000:.2f}"
        )
        print(
            f"python-tsp LS runtime (ms):         "
            f"median={time_ls['median'] * 1000:.2f}, "
            f"p95={time_ls['p95'] * 1000:.2f}"
        )
        print(
            f"Distance delta (ours vs LS):        "
            f"median={dist_delta['median']:.3%}, "
            f"p95={dist_delta['p95']:.3%}"
        )
        
        # print(delta_pct)


if __name__ == "__main__":
    main()

