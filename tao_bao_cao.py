

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SCR_DIR = PROJECT_ROOT / "scr"
for p in (str(PROJECT_ROOT), str(SCR_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import argparse
import copy
import importlib
import math
import random
from typing import Any

import numpy as np

from n9_trang_nguyen_ve_hinh import (
    chosen_report,
    one_shot,
    plot_population,
    plot_seed_triplets,
    population_story,
    save_figure,
    utility_and_energy,
)

RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def _try_import_attr(module_names: list[str], attr_names: list[str]) -> Any | None:
    for mod_name in module_names:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        for attr in attr_names:
            if hasattr(mod, attr):
                return getattr(mod, attr)
    return None


def get_problem(case_key: str, active_lights: int | None = None, beacon_max: float = 25.0) -> dict[str, Any]:
    external_fn = _try_import_attr(
        ["n4_hoang_yen_du_lieu", "n3_phuc_khang_danh_gia", "du_lieu", "danh_gia"],
        ["get_problem", "build_problem", "create_problem"],
    )
    if callable(external_fn):
        try:
            return external_fn(case_key, active_lights=active_lights, beacon_max=beacon_max)
        except TypeError:
            prob = external_fn(case_key)
            if active_lights is not None:
                prob["active_lights"] = int(active_lights)
            prob["beacon_max"] = float(beacon_max)
            return prob

    camps = [
        {"name": "C1", "x": 12.0, "y": 70.0, "weight": 12.0},
        {"name": "C2", "x": 20.0, "y": 25.0, "weight": 18.0},
        {"name": "C3", "x": 38.0, "y": 31.0, "weight": 15.0},
        {"name": "C4", "x": 43.0, "y": 85.0, "weight": 20.0},
        {"name": "C5", "x": 61.0, "y": 43.0, "weight": 16.0},
        {"name": "C6", "x": 65.0, "y": 83.0, "weight": 12.0},
        {"name": "C7", "x": 84.0, "y": 63.0, "weight": 18.0},
        {"name": "C8", "x": 90.0, "y": 22.0, "weight": 14.0},
    ]
    prob: dict[str, Any] = {
        "case_id": case_key,
        "start": [0.0, 50.0],
        "target": [100.0, 50.0],
        "safety": 2.0,
        "budget": 220.0,
        "flight_cost": 0.45,
        "signal_range": 18.0,
        "alpha": 0.1,
        "beacon_max": float(beacon_max),
        "active_lights": 10 if active_lights is None else int(active_lights),
        "length_weight": 0.12,
        "collision_weight": 100.0,
        "battery_weight": 30.0,
        "map_weight": 100.0,
        "camps": camps,
    }
    if case_key in ("A_goc", "co_ban"):
        prob["storms"] = [
            {"name": "V1", "x": 28.0, "y": 50.0, "r": 14.0},
            {"name": "V2", "x": 50.0, "y": 50.0, "r": 14.0},
            {"name": "V3", "x": 72.0, "y": 50.0, "r": 14.0},
        ]
    elif case_key in ("B_goc", "khe_hep"):
        prob["storms"] = [
            {"name": "V1", "x": 40.0, "y": 25.0, "r": 18.0},
            {"name": "V2", "x": 40.0, "y": 75.0, "r": 18.0},
            {"name": "V3", "x": 70.0, "y": 50.0, "r": 12.0},
        ]
        prob["gate"] = {"x": 40.0, "y_min": 43.0, "y_max": 57.0}
    elif case_key in ("C_goc", "chan_duong"):
        prob["storms"] = [
            {"name": "V1", "x": 25.0, "y": 50.0, "r": 15.0},
            {"name": "V2", "x": 50.0, "y": 50.0, "r": 15.0},
            {"name": "V3", "x": 75.0, "y": 50.0, "r": 15.0},
        ]
    else:
        raise ValueError(f"Không nhận diện được ca: {case_key}")
    return prob


def _dist(a: list[float], b: list[float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _dist_point_seg(pt: list[float], a: list[float], b: list[float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    len_sq = dx * dx + dy * dy
    if len_sq == 0.0:
        return _dist(pt, a)
    t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / len_sq))
    return _dist(pt, [a[0] + t * dx, a[1] + t * dy])


def decode_beacons(whale: list[float], problem: dict[str, Any]) -> list[dict[str, Any]]:
    k_limit = min(10, int(problem.get("active_lights", 10)))
    beacons = [
        {
            "x": float(whale[3 * k]),
            "y": float(whale[3 * k + 1]),
            "energy": float(whale[3 * k + 2]),
            "active": False,
        }
        for k in range(10)
    ]
    for _ in range(k_limit):
        chosen = -1
        for k in range(10):
            if not beacons[k]["active"]:
                if chosen == -1 or beacons[k]["energy"] > beacons[chosen]["energy"]:
                    chosen = k
        if chosen != -1:
            beacons[chosen]["active"] = True
    for b in beacons:
        if not b["active"]:
            b["energy"] = 0.0
    return beacons


def crosses_gate(points: list[list[float]], problem: dict[str, Any]) -> bool:
    if "gate" not in problem:
        return False
    gate = problem["gate"]
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        if (a[0] < gate["x"] <= b[0]) or (b[0] <= gate["x"] < a[0]):
            if b[0] != a[0]:
                frac = (gate["x"] - a[0]) / (b[0] - a[0])
                y = a[1] + frac * (b[1] - a[1])
                if gate["y_min"] <= y <= gate["y_max"]:
                    return True
    return False


def evaluate(whale: list[float], problem: dict[str, Any]) -> dict[str, Any]:
    external_fn = _try_import_attr(
        ["n3_phuc_khang_danh_gia", "danh_gia"],
        ["evaluate", "evaluate_whale", "danh_gia_ca_voi"],
    )
    if callable(external_fn):
        return external_fn(whale, problem)

    beacons = decode_beacons(whale, problem)
    points = [problem["start"]] + [[b["x"], b["y"]] for b in beacons] + [problem["target"]]

    length = 0.0
    collision = 0.0
    clearance: float | None = None
    bad_segments: list[int] = []

    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        length += _dist(a, b)
        bad = False
        for storm in problem["storms"]:
            safe_r = storm["r"] + problem["safety"]
            gap = _dist_point_seg([storm["x"], storm["y"]], a, b) - safe_r
            if clearance is None or gap < clearance:
                clearance = gap
            if gap < -1e-9:
                bad = True
            depth = max(0.0, -gap) / safe_r
            collision += depth * depth
        if bad:
            bad_segments.append(i)

    flight = problem["flight_cost"] * length
    lamps = sum(b["energy"] for b in beacons)
    total = flight + lamps
    over_pin = max(0.0, total - problem["budget"]) / problem["budget"]

    satisfaction: list[float] = []
    weighted_sat = 0.0
    weight_sum = 0.0
    r_sq = problem["signal_range"] ** 2
    for camp in problem["camps"]:
        level = sum(
            b["energy"] / (1.0 + ((b["x"] - camp["x"]) ** 2 + (b["y"] - camp["y"]) ** 2) / r_sq)
            for b in beacons
        )
        sat = 1.0 - math.exp(-problem["alpha"] * level)
        satisfaction.append(sat)
        w_val = float(camp.get("weight", camp.get("w", 1.0)))
        weighted_sat += w_val * sat
        weight_sum += w_val

    utility_sat = weighted_sat / weight_sum if weight_sum > 0 else 0.0
    box_ok = all(
        0.0 <= whale[3 * k] <= 100.0
        and 0.0 <= whale[3 * k + 1] <= 100.0
        and 0.0 <= whale[3 * k + 2] <= problem["beacon_max"]
        for k in range(10)
    )
    map_violation = sum(
        (max(0.0, -v, v - 100.0) / 100.0) ** 2
        for k in range(10)
        for v in (whale[3 * k], whale[3 * k + 1])
    )

    base_score = -utility_sat + problem["length_weight"] * length / 100.0
    penalty = (
        problem["collision_weight"] * collision
        + problem["battery_weight"] * (over_pin ** 2)
        + problem["map_weight"] * map_violation
    )
    valid = (
        box_ok
        and (clearance is None or clearance >= -1e-9)
        and (total <= problem["budget"] + 1e-7)
    )
    through_gate = valid and crosses_gate(points, problem)

    return {
        "score": base_score + penalty,
        "base_score": base_score,
        "penalty": penalty,
        "valid": valid,
        "through_gate": through_gate,
        "beacons": beacons,
        "points": points,
        "utility_sat": utility_sat,
        "minimum_service": min(satisfaction) if satisfaction else 0.0,
        "total": total,
        "flight": flight,
        "lamps": lamps,
        "length": length,
        "satisfaction": satisfaction,
        "bad_segments": bad_segments,
    }


def _a_schedule(t: int, total_iter: int, mode: str) -> float:
    s = max(0.0, min(1.0, t / max(1, total_iter)))
    if mode == "linear":
        return 2.0 * (1.0 - s)
    if mode == "cosine":
        return 1.0 + math.cos(math.pi * s)
    if mode == "quadratic":
        return 2.0 * ((1.0 - s) ** 2)
    raise ValueError(f"Chưa hỗ trợ a_mode: {mode}")


def run_woa(
    problem: dict[str, Any],
    seed: int,
    pop_size: int = 30,
    iterations: int = 120,
    a_mode: str = "linear",
    l_mode: str = "shared_l",
    boundary: str = "clip",
    snapshot_every: int = 20,
) -> dict[str, Any]:
    external_fn = _try_import_attr(
        ["n6_van_lam_woa", "woa"],
        ["run_woa", "chay_woa"],
    )
    if callable(external_fn):
        try:
            return external_fn(
                problem,
                seed=seed,
                pop_size=pop_size,
                iterations=iterations,
                a_mode=a_mode,
                l_mode=l_mode,
                boundary=boundary,
                snapshot_every=snapshot_every,
            )
        except TypeError:
            pass

    rng = random.Random(seed)
    aux_rng = random.Random(seed + 1_000_003)
    lower = [0.0, 0.0, 0.0] * 10
    upper = [100.0, 100.0, float(problem["beacon_max"])] * 10

    population = [
        [lower[j] + rng.random() * (upper[j] - lower[j]) for j in range(30)]
        for _ in range(pop_size)
    ]
    best_overall: dict[str, Any] | None = None
    best_valid: dict[str, Any] | None = None
    best_gate: dict[str, Any] | None = None
    snapshots: list[dict[str, Any]] = []

    for t in range(iterations):
        for i in range(pop_size):
            for j in range(30):
                if population[i][j] < lower[j] or population[i][j] > upper[j]:
                    if boundary == "clip":
                        population[i][j] = max(lower[j], min(upper[j], population[i][j]))
                    elif boundary == "reinit":
                        population[i][j] = lower[j] + rng.random() * (upper[j] - lower[j])
                    else:
                        raise ValueError(f"Chưa hỗ trợ boundary: {boundary}")

            rep = evaluate(population[i], problem)
            if best_overall is None or rep["score"] < best_overall["evaluation"]["score"]:
                best_overall = {"position": population[i].copy(), "evaluation": rep}
            if rep["valid"]:
                if best_valid is None or rep["base_score"] < best_valid["evaluation"]["base_score"]:
                    best_valid = {"position": population[i].copy(), "evaluation": rep}
                if rep["through_gate"]:
                    if best_gate is None or rep["base_score"] < best_gate["evaluation"]["base_score"]:
                        best_gate = {"position": population[i].copy(), "evaluation": rep}

        if t % snapshot_every == 0 or t == iterations - 1:
            chosen = best_valid if best_valid is not None else best_overall
            snapshots.append(
                {
                    "iteration": t,
                    "population": copy.deepcopy(population),
                    "position": chosen["position"].copy(),
                }
            )

        a_val = _a_schedule(t, iterations, a_mode)
        a2_val = -1.0 - (t / max(1, iterations))
        leader = best_overall["position"]

        for i in range(pop_size):
            r1, r2 = rng.random(), rng.random()
            A_coef = 2.0 * a_val * r1 - a_val
            C_coef = 2.0 * r2
            l_shared = (a2_val - 1.0) * rng.random() + 1.0
            p_val = rng.random()

            if p_val < 0.5:
                if abs(A_coef) >= 1.0:
                    for j in range(30):
                        ref_val = population[rng.randrange(pop_size)][j]
                        population[i][j] = ref_val - A_coef * abs(C_coef * ref_val - population[i][j])
                else:
                    for j in range(30):
                        population[i][j] = leader[j] - A_coef * abs(C_coef * leader[j] - population[i][j])
            else:
                for j in range(30):
                    l_j = l_shared if l_mode == "shared_l" else ((a2_val - 1.0) * aux_rng.random() + 1.0)
                    dist_l = abs(leader[j] - population[i][j])
                    population[i][j] = leader[j] + dist_l * math.exp(l_j) * math.cos(2.0 * math.pi * l_j)

    return {
        "problem": problem,
        "settings": {"seed": seed, "population": pop_size, "iterations": iterations},
        "best_overall": best_overall,
        "best_valid": best_valid,
        "best_gate": best_gate,
        "snapshots": snapshots,
        "final_population": population,
    }


def summarize_30_seeds(results: list[dict[str, Any]], cid: str) -> dict[str, Any]:
    external_fn = _try_import_attr(
        ["n8_trang_bui_thong_ke", "thong_ke"],
        ["summarize_30_seeds", "summarize_runs", "tong_hop_30_seed"],
    )
    if callable(external_fn):
        try:
            return external_fn(results, cid)
        except TypeError:
            return external_fn(results)

    valid_runs = [r for r in results if r.get("best_valid") is not None]
    u_vals = [float(r["best_valid"]["evaluation"]["utility_sat"]) for r in valid_runs]
    min_vals = [float(r["best_valid"]["evaluation"]["minimum_service"]) for r in valid_runs]
    return {
        "id": cid,
        "n": len(results),
        "valid_n": len(valid_runs),
        "overall_valid_n": sum(1 for r in results if r["best_overall"]["evaluation"]["valid"]),
        "gate_found_n": sum(1 for r in results if r.get("best_gate") is not None),
        "utility_sat_mean": float(np.mean(u_vals)) if u_vals else None,
        "utility_sat_std": float(np.std(u_vals, ddof=1)) if len(u_vals) > 1 else None,
        "minimum_service_mean": float(np.mean(min_vals)) if min_vals else None,
    }


def export_base_cases(fig_dir: Path, n_seeds: int = 30, iterations: int = 120) -> None:
    specs = [
        ("A_goc", "A · cơ bản"),
        ("B_goc", "B · khe hẹp"),
        ("C_goc", "C · chắn đường"),
    ]
    results_by_id: dict[str, list[dict[str, Any]]] = {}
    summaries_by_id: dict[str, dict[str, Any]] = {}

    for cid, _ in specs:
        prob = get_problem(cid)
        runs = [
            run_woa(prob, seed=s, pop_size=30, iterations=iterations, snapshot_every=max(1, iterations // 6))
            for s in range(1, n_seeds + 1)
        ]
        results_by_id[cid] = runs
        summaries_by_id[cid] = summarize_30_seeds(runs, cid)

    save_figure(
        one_shot(
            [results_by_id[cid][6] for cid, _ in specs],
            [summaries_by_id[cid] for cid, _ in specs],
            [lbl for _, lbl in specs],
            "Ca gốc · ba bài toán (A, B, C)",
            "Bản đồ minh họa seed 7 · Thống kê cột/râu (SD mẫu) và bảng trên đủ 30 seed",
        ),
        fig_dir / "00_ca_goc_tong_hop.png",
    )

    for cid, lbl in specs:
        runs = results_by_id[cid]
        r7 = runs[6]
        save_figure(population_story(r7, evaluate, lbl), fig_dir / f"{cid}_tien_hoa_dan.png")
        save_figure(utility_and_energy(r7, lbl), fig_dir / f"{cid}_pin_va_trai.png")
        save_figure(
            plot_population(r7["problem"], chosen_report(r7), r7.get("final_population"), f"{lbl} · seed 7"),
            fig_dir / f"{cid}_seed_07.png",
        )
        valid_runs = [r for r in runs if r.get("best_valid") is not None]
        ordered = sorted(
            valid_runs if valid_runs else runs,
            key=lambda r: r["best_valid"]["evaluation"]["base_score"]
            if r.get("best_valid") is not None
            else r["best_overall"]["evaluation"]["score"],
        )
        r_best, r_typ, r_worst = ordered[0], ordered[len(ordered) // 2], ordered[-1]
        save_figure(
            plot_seed_triplets(r_best, r_typ, r_worst, f"{lbl} · Seed tốt / tiêu biểu / kém"),
            fig_dir / f"{cid}_ba_seed.png",
        )


def export_variant_comparisons(fig_dir: Path, n_seeds: int = 30, iterations: int = 120) -> None:
    def _batch(prob_fn, **kw):
        runs = [
            run_woa(prob_fn(), seed=s, pop_size=30, iterations=iterations, snapshot_every=max(1, iterations // 6), **kw)
            for s in range(1, n_seeds + 1)
        ]
        return runs, summarize_30_seeds(runs, "variant")

    a_base, s_a_base = _batch(lambda: get_problem("A_goc"), l_mode="shared_l")
    a_lind, s_a_lind = _batch(lambda: get_problem("A_goc"), l_mode="independent_l")
    save_figure(
        one_shot(
            [a_base[6], a_lind[6]],
            [s_a_base, s_a_lind],
            ["l chung", "l độc lập"],
            "Ngách 1 (l chung / độc lập) · Ca A",
            "Map seed 7 · Cột/râu (SD mẫu) và bảng tổng hợp 30 seed",
        ),
        fig_dir / "01_ngach1_l_ca_A_1920x1080.png",
    )

    b_base, s_b_base = _batch(lambda: get_problem("B_goc"), l_mode="shared_l")
    b_lind, s_b_lind = _batch(lambda: get_problem("B_goc"), l_mode="independent_l")
    save_figure(
        one_shot(
            [b_base[6], b_lind[6]],
            [s_b_base, s_b_lind],
            ["l chung", "l độc lập"],
            "Ngách 1 (l chung / độc lập) · Ca B",
            "Map seed 7 · Cột/râu (SD mẫu) và bảng tổng hợp 30 seed",
        ),
        fig_dir / "02_ngach1_l_ca_B_1920x1080.png",
    )

    a_reinit, s_a_reinit = _batch(lambda: get_problem("A_goc"), boundary="reinit")
    save_figure(
        one_shot(
            [a_base[6], a_reinit[6]],
            [s_a_base, s_a_reinit],
            ["Clip", "Re-init"],
            "Ngách 2 (Biên Clip / Re-init) · Ca A",
            "Map seed 7 · Cột/râu (SD mẫu) và bảng tổng hợp 30 seed",
        ),
        fig_dir / "03_ngach2_bien_ca_A_1920x1080.png",
    )

    b_reinit, s_b_reinit = _batch(lambda: get_problem("B_goc"), boundary="reinit")
    save_figure(
        one_shot(
            [b_base[6], b_reinit[6]],
            [s_b_base, s_b_reinit],
            ["Clip", "Re-init"],
            "Ngách 2 (Biên Clip / Re-init) · Ca B",
            "Map seed 7 · Cột/râu (SD mẫu) và bảng tổng hợp 30 seed",
        ),
        fig_dir / "04_ngach2_bien_ca_B_1920x1080.png",
    )

    b_cos, s_b_cos = _batch(lambda: get_problem("B_goc"), a_mode="cosine")
    b_quad, s_b_quad = _batch(lambda: get_problem("B_goc"), a_mode="quadratic")
    save_figure(
        one_shot(
            [b_base[6], b_cos[6], b_quad[6]],
            [s_b_base, s_b_cos, s_b_quad],
            ["Linear", "Cosine", "Quadratic"],
            "Ngách 3 (Lịch giảm a) · Ca B",
            "Map seed 7 · Cột/râu (SD mẫu) và bảng tổng hợp 30 seed",
        ),
        fig_dir / "05_ngach3_lich_a_ca_B_1920x1080.png",
    )

    a_k6, s_a_k6 = _batch(lambda: get_problem("A_goc", active_lights=6))
    a_k8, s_a_k8 = _batch(lambda: get_problem("A_goc", active_lights=8))
    save_figure(
        one_shot(
            [a_k6[6], a_k8[6], a_base[6]],
            [s_a_k6, s_a_k8, s_a_base],
            ["K = 6", "K = 8", "K = 10"],
            "Ngách 4 (Số đèn tối đa K) · Ca A",
            "Map seed 7 · Cột/râu (SD mẫu) và bảng tổng hợp 30 seed",
        ),
        fig_dir / "06_ngach4_so_den_K_ca_A_1920x1080.png",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Xuất bộ ảnh ca gốc trước, sau đó 6 ảnh so sánh 16:9 cho 4 ngách.")
    parser.add_argument("--include-variants", action="store_true", help="Xuất thêm 6 ảnh so sánh 4 ngách.")
    parser.add_argument("--seeds", type=int, default=30, help="Số seed thống kê (mặc định 30).")
    parser.add_argument("--iters", type=int, default=120, help="Số lượt lặp mỗi seed.")
    args = parser.parse_args()

    export_base_cases(FIGURES_DIR, n_seeds=args.seeds, iterations=args.iters)
    if args.include_variants:
        export_variant_comparisons(FIGURES_DIR, n_seeds=args.seeds, iterations=args.iters)
    print(f"Hoàn tất xuất hình 1920x1080 tại: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
