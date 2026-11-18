"""Ngọc Thanh: ba ca gốc, bốn ngách, cùng 30 seed.

Chốt câu hỏi trước khi nhìn đáp án. Mỗi dòng chỉ đổi yếu tố đang hỏi.
"""
import argparse
import copy
import csv
import json
from pathlib import Path
from src.n4_hoang_yen_du_lieu import ROOT, load_problem, default_settings
from src.n3_phuc_khang_danh_gia import evaluate, evaluate_benchmark
from src.n6_van_lam_woa import woa


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=1, allow_nan=False)


def save_csv(path, rows):
    if not rows:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def experiment_plan():
    return [
        {"id": "A_goc", "label": "A · cơ bản", "map": "co_ban"},
        {"id": "B_goc", "label": "B · khe hẹp", "map": "khe_hep"},
        {"id": "C_goc", "label": "C · chắn đường", "map": "chan_duong"},
        {"id": "A_l_independent", "label": "l độc lập", "map": "co_ban", "reference": "A_goc", "l_mode": "independent_l"},
        {"id": "B_l_independent", "label": "l độc lập", "map": "khe_hep", "reference": "B_goc", "l_mode": "independent_l"},
        {"id": "A_reinit", "label": "Re-init", "map": "co_ban", "reference": "A_goc", "boundary": "reinit"},
        {"id": "B_reinit", "label": "Re-init", "map": "khe_hep", "reference": "B_goc", "boundary": "reinit"},
        {"id": "B_a_cosine", "label": "a cosine", "map": "khe_hep", "reference": "B_goc", "a_mode": "cosine"},
        {"id": "B_a_quadratic", "label": "a quadratic", "map": "khe_hep", "reference": "B_goc", "a_mode": "quadratic"},
        {"id": "A_den_6", "label": "Tối đa 6 đèn", "map": "co_ban", "reference": "A_goc", "active_lights": 6},
        {"id": "A_den_8", "label": "Tối đa 8 đèn", "map": "co_ban", "reference": "A_goc", "active_lights": 8},
    ]


def study_groups():
    return [
        ["1_l_A", "Ngách 1 · l dùng chung và độc lập · ca A", ["A_goc", "A_l_independent"]],
        ["1_l_B", "Ngách 1 · l dùng chung và độc lập · ca B", ["B_goc", "B_l_independent"]],
        ["2_bien_A", "Ngách 2 · clip và re-init · ca A", ["A_goc", "A_reinit"]],
        ["2_bien_B", "Ngách 2 · clip và re-init · ca B", ["B_goc", "B_reinit"]],
        ["3_a", "Ngách 3 · ba lịch giảm a · ca B", ["B_goc", "B_a_cosine", "B_a_quadratic"]],
        ["4_so_den", "Ngách 4 · số đèn hoạt động, giữ 30 biến · ca A", ["A_goc", "A_den_6", "A_den_8"]],
    ]


def make_configuration(spec, seed, population=30, iterations=800):
    problem = load_problem(spec["map"])
    settings = default_settings()
    settings["seed"] = seed
    settings["population"] = population
    settings["iterations"] = iterations
    for key in ["a_mode", "l_mode", "boundary"]:
        if key in spec:
            settings[key] = spec[key]
    if "active_lights" in spec:
        problem["active_lights"] = spec["active_lights"]
    return problem, settings


def run_to_row(result):
    overall = result["best_overall"]["evaluation"]
    row = {"id": result["experiment"]["id"], "seed": result["settings"]["seed"],
           "population": result["settings"]["population"], "iterations": result["settings"]["iterations"],
           "evaluations": result["evaluations"], "dimensions": 30,
           "active_lights": result["problem"]["active_lights"], "budget": 220,
           "valid": int(result["best_valid"] is not None), "overall_valid": int(overall["valid"]),
           "gate_found": int(result["best_gate"] is not None), "final_through_gate": 0,
           "overall_score": overall["score"], "overall_collision": overall["collision"],
           "overall_over": overall["over"], "first_valid_iteration": result["first_valid_iteration"],
           "utility_sat": None, "minimum_service": None, "base_score": None,
           "length": None, "energy": None, "flight": None, "lamps": None,
           "seconds": result["elapsed_seconds"]}
    if result["best_valid"] is not None:
        report = result["best_valid"]["evaluation"]
        for key in ["utility_sat", "minimum_service", "base_score", "length", "flight", "lamps"]:
            row[key] = report[key]
        row["energy"] = report["total"]
        row["final_through_gate"] = int(report["through_gate"])
    return row


def export_trials(output):
    rows = []
    for path in sorted((Path(output) / "runs").glob("*/seed_*.json")):
        with open(path, encoding="utf-8") as file:
            rows.append(run_to_row(json.load(file)))
    save_csv(Path(output) / "trials.csv", rows)


def run_paths(output, seeds, population, iterations, only):
    for spec in experiment_plan():
        if only and spec["id"] not in only:
            continue
        for seed in range(1, seeds + 1):
            problem, settings = make_configuration(spec, seed, population, iterations)
            result = woa(evaluate, problem, settings)
            result["experiment"] = spec
            short_history = []
            for row in result["history"]:
                if row["iteration"] % 20 == 0 or row["iteration"] == iterations - 1:
                    short_history.append(row)
            result["history"] = short_history
            save_json(output / "runs" / spec["id"] / ("seed_" + str(seed).zfill(2) + ".json"), result)
            print(spec["id"], seed, "valid", result["best_valid"] is not None,
                  "qua khe", result["best_gate"] is not None, flush=True)


def run_benchmarks(output, seeds):
    functions = [
        {"function": "quadratic", "dimensions": 1, "lower": -20, "upper": 20, "target": 0.00000001},
        {"function": "sphere", "dimensions": 30, "lower": -100, "upper": 100, "target": 0.00000001},
        {"function": "rastrigin", "dimensions": 30, "lower": -5.12, "upper": 5.12, "target": 0.000001},
    ]
    for problem in functions:
        for seed in range(1, seeds + 1):
            settings = default_settings()
            settings["seed"] = seed
            settings["iterations"] = 500
            result = woa(evaluate_benchmark, problem, settings)
            result["final_population"] = []
            result["history"] = []
            save_json(output / "benchmarks" / problem["function"] / ("seed_" + str(seed).zfill(2) + ".json"), result)
            print("benchmark", problem["function"], seed, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "results"))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--population", type=int, default=30, help="Cỡ đàn bài bay; benchmark cố định N=30.")
    parser.add_argument("--iterations", type=int, default=800, help="Lượt bài bay; benchmark cố định T=500.")
    parser.add_argument("--only", default="")
    parser.add_argument("--suite", choices=["path", "benchmark", "all"], default="all")
    parser.add_argument("--no-summary", action="store_true")
    args = parser.parse_args()
    output = Path(args.output)
    if args.seeds < 1 or args.population < 2 or args.iterations < 2:
        parser.error("Cần seeds>=1, population>=2, iterations>=2 nhé.")
    only = []
    if args.only:
        only = args.only.split(",")
        known = []
        for spec in experiment_plan():
            known.append(spec["id"])
        for name in only:
            if name not in known:
                parser.error("Không có cấu hình " + name + ". Xem experiment_plan trong n7 nhé.")
    if args.suite in ["path", "all"]:
        run_paths(output, args.seeds, args.population, args.iterations, only)
    if args.suite in ["benchmark", "all"]:
        run_benchmarks(output, args.seeds)
    if not args.no_summary:
        export_trials(output)
        from src.n8_trang_bui_thong_ke import summarize_folder
        summarize_folder(output)


if __name__ == "__main__":
    main()
