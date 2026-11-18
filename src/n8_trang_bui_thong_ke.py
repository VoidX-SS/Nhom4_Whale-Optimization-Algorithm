"""Trang Bùi: đọc CSV, đếm cả lượt thất bại rồi mới kể kết quả.

U trung bình là trên các lượt hợp lệ. Bảng luôn giữ n hợp lệ / n chạy.
"""
import csv
import json
import math
import statistics
from pathlib import Path
from src.n7_ngoc_thanh_thuc_nghiem import save_csv, export_trials, experiment_plan


def load_runs(output):
    results = []
    for path in sorted((Path(output) / "runs").glob("*/seed_*.json")):
        with open(path, encoding="utf-8") as file:
            results.append(json.load(file))
    return results


def read_trials(output):
    rows = []
    path = Path(output) / "trials.csv"
    if not path.exists():
        return rows
    with open(path, encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            for key in row:
                if key == "id":
                    continue
                if row[key] == "":
                    row[key] = None
                else:
                    row[key] = float(row[key])
            rows.append(row)
    return rows


def average(values):
    if not values:
        return None
    return statistics.mean(values)


def std(values):
    if len(values) < 2:
        return None
    return statistics.stdev(values)


def summarize_rows(rows):
    groups = {}
    for row in rows:
        if row["id"] not in groups:
            groups[row["id"]] = []
        groups[row["id"]].append(row)
    summary = []
    for name in groups:
        group = groups[name]
        item = {"id": name, "n": len(group), "valid_n": 0, "overall_valid_n": 0,
                "gate_found_n": 0, "final_through_gate_n": 0,
                "population": int(group[0]["population"]), "iterations": int(group[0]["iterations"])}
        for row in group:
            if row["population"] != item["population"] or row["iterations"] != item["iterations"]:
                raise ValueError("Đang trộn ngân sách tính toán trong " + name)
            item["valid_n"] += int(row["valid"])
            item["overall_valid_n"] += int(row["overall_valid"])
            item["gate_found_n"] += int(row["gate_found"])
            item["final_through_gate_n"] += int(row["final_through_gate"])
        for key in ["utility_sat", "minimum_service", "base_score", "length", "energy", "seconds", "first_valid_iteration"]:
            values = []
            for row in group:
                if row[key] is not None:
                    values.append(row[key])
            item[key + "_mean"] = average(values)
            item[key + "_std"] = std(values)
        summary.append(item)
    return summary


def representative_seeds(results, name):
    valid = []
    failed = []
    for result in results:
        if result["experiment"]["id"] == name:
            if result["best_valid"] is not None:
                valid.append(result)
            else:
                failed.append(result)
    if not valid:
        return {"typical": failed[0]["settings"]["seed"], "best": None, "worst": None}
    scores = []
    for result in valid:
        scores.append(result["best_valid"]["evaluation"]["base_score"])
    target = statistics.median(scores)
    typical = valid[0]
    best = valid[0]
    worst = valid[0]
    for result in valid:
        score = result["best_valid"]["evaluation"]["base_score"]
        if abs(score - target) < abs(typical["best_valid"]["evaluation"]["base_score"] - target):
            typical = result
        if score < best["best_valid"]["evaluation"]["base_score"]:
            best = result
        if score > worst["best_valid"]["evaluation"]["base_score"]:
            worst = result
    return {"typical": typical["settings"]["seed"], "best": best["settings"]["seed"],
            "worst": worst["settings"]["seed"]}


def path_diagnostics(report):
    # Đo việc bám mép và dồn điểm; những thước này không tham gia chấm J.
    beacons = report["beacons"]
    edge = 0
    max_cluster = 0
    actual_lights = 0
    for a in beacons:
        if min(a["x"], a["y"], 100 - a["x"], 100 - a["y"]) <= 1:
            edge += 1
        if a["energy"] > 0.001:
            actual_lights += 1
        neighbors = 0
        for b in beacons:
            if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) <= 3:
                neighbors += 1
        max_cluster = max(max_cluster, neighbors)
    concentration = 0
    if report["lamps"] > 0:
        for beacon in beacons:
            concentration += (beacon["energy"] / report["lamps"]) ** 2
    return {"edge_fraction": edge / 10, "largest_neighborhood_radius3": max_cluster,
            "positive_lights": actual_lights, "energy_concentration": concentration}


def paired_rows(rows):
    lookup = {}
    for row in rows:
        lookup[(row["id"], int(row["seed"]))] = row
    out = []
    for spec in experiment_plan():
        if "reference" not in spec:
            continue
        deltas = []
        variant_only = 0
        reference_only = 0
        for seed in range(1, 31):
            new = lookup.get((spec["id"], seed))
            old = lookup.get((spec["reference"], seed))
            if new is None or old is None:
                continue
            if new["valid"] and old["valid"]:
                deltas.append(new["utility_sat"] - old["utility_sat"])
            elif new["valid"]:
                variant_only += 1
            elif old["valid"]:
                reference_only += 1
        out.append({"variant": spec["id"], "reference": spec["reference"],
                    "both_valid_n": len(deltas), "variant_only_n": variant_only,
                    "reference_only_n": reference_only, "delta_U_mean": average(deltas), "delta_U_std": std(deltas)})
    return out


def summarize_benchmarks(output):
    rows = []
    for path in sorted((Path(output) / "benchmarks").glob("*/seed_*.json")):
        with open(path, encoding="utf-8") as file:
            result = json.load(file)
        problem = result["problem"]
        report = result["best_overall"]["evaluation"]
        square_distance = 0
        for value in report["values"]:
            optimum = 0
            if problem["function"] == "quadratic":
                optimum = 7
            square_distance += (value - optimum) ** 2
        rows.append({"function": problem["function"], "seed": result["settings"]["seed"],
                     "dimensions": problem["dimensions"], "score": report["score"],
                     "target": problem["target"], "success": int(report["score"] <= problem["target"]),
                     "distance_to_known_optimum": math.sqrt(square_distance), "evaluations": result["evaluations"]})
    save_csv(Path(output) / "benchmark_trials.csv", rows)
    summary = []
    for name in ["quadratic", "sphere", "rastrigin"]:
        values = []
        successes = 0
        for row in rows:
            if row["function"] == name:
                values.append(row["score"])
                successes += row["success"]
        if values:
            summary.append({"function": name, "n": len(values), "success_n": successes,
                            "score_mean": average(values), "score_std": std(values)})
    save_csv(Path(output) / "benchmark_summary.csv", summary)


def summarize_folder(output):
    export_trials(output)
    rows = read_trials(output)
    save_csv(Path(output) / "summary.csv", summarize_rows(rows))
    save_csv(Path(output) / "paired.csv", paired_rows(rows))
    summarize_benchmarks(output)
