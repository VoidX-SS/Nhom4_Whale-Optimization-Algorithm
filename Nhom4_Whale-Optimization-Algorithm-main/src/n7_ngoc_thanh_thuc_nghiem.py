"""N7 Ngọc Thanh: chạy 11 cấu hình, 3 ca đường bay và benchmark; lưu đủ dữ liệu."""
import argparse
import csv
import json
import time
from pathlib import Path
import numpy as np

from src.n4_hoang_yen_du_lieu import ROOT, load_problem, get_bounds, get_a_value, get_a2_author
from src.n3_phuc_khang_danh_gia import evaluate, evaluate_benchmark
from src.n5_quynh_ngan_buoc_woa import make_woa_hooks
from src.n6_van_lam_woa import woa


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    def convert(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        if isinstance(value, (np.bool_,)):
            return bool(value)
        raise TypeError("Không thể chuyển sang JSON: " + type(value).__name__)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=convert, allow_nan=False)


def save_csv(path, rows):
    if not rows:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def experiment_plan():
    return [
        {"id": "A_goc", "label": "A · cơ bản", "map": "A"},
        {"id": "B_goc", "label": "B · khe hẹp", "map": "B"},
        {"id": "C_goc", "label": "C · chắn đường", "map": "C"},
        {"id": "A_l_independent", "label": "l độc lập", "map": "A", "reference": "A_goc", "l_mode": "independent_l"},
        {"id": "B_l_independent", "label": "l độc lập", "map": "B", "reference": "B_goc", "l_mode": "independent_l"},
        {"id": "A_reinit", "label": "Re-init", "map": "A", "reference": "A_goc", "boundary": "reinit"},
        {"id": "B_reinit", "label": "Re-init", "map": "B", "reference": "B_goc", "boundary": "reinit"},
        {"id": "B_a_cosine", "label": "a cosine", "map": "B", "reference": "B_goc", "a_mode": "cosine"},
        {"id": "B_a_quadratic", "label": "a quadratic", "map": "B", "reference": "B_goc", "a_mode": "quadratic"},
        {"id": "A_den_6", "label": "Tối đa 6 đèn", "map": "A", "reference": "A_goc", "active_lights": 6},
        {"id": "A_den_8", "label": "Tối đa 8 đèn", "map": "A", "reference": "A_goc", "active_lights": 8},
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
    if "active_lights" in spec:
        problem["active_lights"] = spec["active_lights"]
    return problem


def _evaluate_with_details(x, problem):
    return evaluate(x.tolist() if hasattr(x, "tolist") else list(x), problem)


def run_one_path(spec, seed, population=30, iterations=800):
    problem = make_configuration(spec, seed, population, iterations)
    lower, upper = get_bounds(30)
    l_mode = spec.get("l_mode", "shared_l")
    boundary = spec.get("boundary", "clip")
    init_fn, update_fn, bounds_fn = make_woa_hooks(l_mode, boundary, seed)
    a_mode = spec.get("a_mode", "linear")
    start = time.perf_counter()
    result = woa(lambda x: evaluate(x, problem), lower, upper,
                 n_whales=population, n_iter=iterations, seed=seed,
                 snapshot_every=20, init_fn=init_fn, update_fn=update_fn,
                 bounds_fn=bounds_fn,
                 a_fn=lambda k, t: get_a_value(k, t, a_mode),
                 a2_fn=get_a2_author)
    elapsed = time.perf_counter() - start
    for key in ("best_overall", "best_valid", "best_gate"):
        if result[key] is not None:
            result[key]["evaluation"] = _evaluate_with_details(result[key]["x"], problem)
    result["experiment"] = spec
    result["problem"] = problem
    result["settings"] = {"seed": seed, "population": population, "iterations": iterations,
                          "l_mode": l_mode, "boundary": boundary, "a_mode": a_mode}
    result["elapsed_seconds"] = elapsed
    return result


def run_to_row(result):
    overall_entry = result["best_overall"]
    overall = overall_entry["evaluation"]
    best_valid = result["best_valid"]
    report = None if best_valid is None else best_valid["evaluation"]
    final = result["final_population"]
    return {
        "id": result["experiment"]["id"], "seed": result["settings"]["seed"],
        "population": result["settings"]["population"], "iterations": result["settings"]["iterations"],
        "evaluations": result["n_evaluations"], "dimensions": 30,
        "active_lights": result["problem"]["active_lights"], "budget": result["problem"]["budget"],
        "valid": int(best_valid is not None), "overall_valid": int(overall["valid"]),
        "gate_found": int(result["best_gate"] is not None),
        "final_through_gate": int(any(final["through_gate"])),
        "overall_score": overall["score"], "overall_collision": overall["collision"],
        "overall_over": overall["over"],
        "first_valid_iteration": next((h["iteration"] for h in result["history"] if h["n_valid"] > 0), None),
        "utility_sat": None if report is None else report["utility_sat"],
        "minimum_service": None if report is None else report["minimum_service"],
        "base_score": None if report is None else report["base_score"],
        "length": None if report is None else report["length"],
        "energy": None if report is None else report["total"],
        "flight": None if report is None else report["flight"],
        "lamps": None if report is None else report["lamps"],
        "seconds": result["elapsed_seconds"]
    }


def run_paths(output, seeds=30, population=30, iterations=800, only=None):
    output = Path(output)
    only = set(only or [])
    for spec in experiment_plan():
        if only and spec["id"] not in only:
            continue
        for seed in range(1, seeds + 1):
            result = run_one_path(spec, seed, population, iterations)
            save_json(output / "runs" / spec["id"] / (f"seed_{seed:02d}.json"), result)
            print(spec["id"], seed, "valid", result["best_valid"] is not None,
                  "qua khe", result["best_gate"] is not None, flush=True)


def run_benchmarks(output, seeds=30):
    output = Path(output)
    functions = [
        {"function": "quadratic", "dimensions": 1, "lower": -20, "upper": 20, "target": 1e-8},
        {"function": "sphere", "dimensions": 30, "lower": -100, "upper": 100, "target": 1e-8},
        {"function": "rastrigin", "dimensions": 30, "lower": -5.12, "upper": 5.12, "target": 1e-6},
    ]
    for problem in functions:
        dim = problem["dimensions"]
        lower = np.full(dim, problem["lower"], dtype=float)
        upper = np.full(dim, problem["upper"], dtype=float)
        for seed in range(1, seeds + 1):
            start = time.perf_counter()
            result = woa(lambda x: _benchmark_record(x, problem), lower, upper,
                         n_whales=30, n_iter=500, seed=seed, snapshot_every=20)
            elapsed = time.perf_counter() - start
            result["benchmark"] = problem
            result["seed"] = seed
            result["elapsed_seconds"] = elapsed
            result["best_evaluation"] = evaluate_benchmark(result["best_overall"]["x"], problem)
            result["target_success"] = bool(result["best_evaluation"].get("success", False))
            save_json(output / "benchmarks" / problem["function"] / f"seed_{seed:02d}.json", result)
            print("benchmark", problem["function"], seed, flush=True)


def _benchmark_record(x, problem):
    out = evaluate_benchmark(x, problem)
    return {"score": float(out["score"]), "base_score": float(out["base_score"]),
            "valid": bool(out["in_domain"]), "through_gate": False}


def export_trials(output):
    rows = []
    for path in sorted((Path(output) / "runs").glob("*/seed_*.json")):
        with open(path, encoding="utf-8") as f:
            rows.append(run_to_row(json.load(f)))
    save_csv(Path(output) / "trials.csv", rows)
    return rows



def replay_demos(output, seeds):
    """Chạy lại A/B/C theo seed được nhóm chỉ định và đối chiếu với JSON gốc."""
    output = Path(output)
    specs = [spec for spec in experiment_plan() if spec["id"] in ("A_goc", "B_goc", "C_goc")]
    for spec in specs:
        for seed in seeds:
            original_path = output / "runs" / spec["id"] / f"seed_{seed:02d}.json"
            if not original_path.is_file():
                raise FileNotFoundError(f"Thiếu lần chạy gốc để replay: {original_path}")
            with open(original_path, encoding="utf-8") as f:
                original = json.load(f)
            rerun = run_one_path(spec, seed, original["settings"]["population"],
                                 original["settings"]["iterations"])
            same_score = abs(rerun["best_overall"]["score"] - original["best_overall"]["score"]) <= 1e-12
            same_population = np.allclose(np.asarray(rerun["final_population"]["population"]),
                                          np.asarray(original["final_population"]["population"]),
                                          rtol=0.0, atol=1e-12)
            rerun["replay_check"] = {"matches_original_score": bool(same_score),
                                     "matches_final_population": bool(same_population),
                                     "matches_original": bool(same_score and same_population)}
            save_json(output / "demos" / spec["id"] / f"seed_{seed:02d}.json", rerun)
            print("replay", spec["id"], seed, rerun["replay_check"], flush=True)


def main():
    parser = argparse.ArgumentParser(description="Thí nghiệm WOA N7")
    parser.add_argument("--output", default=str(ROOT / "results"))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--population", type=int, default=30)
    parser.add_argument("--iterations", type=int, default=800)
    parser.add_argument("--only", default="")
    parser.add_argument("--suite", choices=["path", "benchmark", "all", "pilot", "replay"], default="all")
    parser.add_argument("--replay-seeds", default="", help="Seed do Trang Bùi chọn, ví dụ 1,7,12")
    parser.add_argument("--no-summary", action="store_true")
    args = parser.parse_args()
    if args.seeds < 1 or args.population < 2 or args.iterations < 2:
        parser.error("Cần seeds>=1, population>=2, iterations>=2")
    output = Path(args.output)
    if args.suite == "pilot":
        output = output / "pilot"
        run_paths(output, seeds=min(args.seeds, 2), population=min(args.population, 8),
                  iterations=min(args.iterations, 20), only=args.only.split(",") if args.only else None)
    elif args.suite == "replay":
        if not args.replay_seeds:
            parser.error("Suite replay cần --replay-seeds, dùng đúng seed do nhóm chọn.")
        replay_seeds = [int(x.strip()) for x in args.replay_seeds.split(",") if x.strip()]
        if not replay_seeds or any(seed < 1 for seed in replay_seeds):
            parser.error("--replay-seeds phải là danh sách số nguyên dương.")
        replay_demos(output, replay_seeds)
    else:
        only = args.only.split(",") if args.only else None
        if args.suite in ("path", "all"):
            run_paths(output, args.seeds, args.population, args.iterations, only)
        if args.suite in ("benchmark", "all"):
            run_benchmarks(output, args.seeds)
    if not args.no_summary and args.suite not in ("pilot", "replay"):
        rows = export_trials(output)
        print("Đã xuất", len(rows), "dòng trials.csv", flush=True)


if __name__ == "__main__":
    main()
