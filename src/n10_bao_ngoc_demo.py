"""
src/n10_bao_ngoc_demo.py
Lõi giao diện & điều phối demo bài toán Đom Đóm (UAV + WOA) - Bảo Ngọc (N10).
Dùng chung cho:
  1. Chạy dòng lệnh: python src/n10_bao_ngoc_demo.py
  2. Google Colab (demo_colab.ipynb)
  3. Giao diện web Streamlit (app.py)
"""
from __future__ import annotations

import base64
import copy
import io
import json
import math
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np

# Đảm bảo import được các module trong thư mục gốc và thư mục src/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
for _p in (ROOT_DIR, CURRENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# --- Import hàm đánh giá từ N3 (Phúc Khang) nếu có, nếu không dùng bản chuẩn đã đối chiếu ---
try:
    from n3_phuc_khang_danh_gia import evaluate as _n3_evaluate
except Exception:
    _n3_evaluate = None

# --- Import dữ liệu từ N4 (Hoàng Yến) nếu có ---
try:
    from src.n4_hoang_yen_du_lieu import load_problem as _n4_load_problem
except Exception:
    try:
        from n4_hoang_yen_du_lieu import load_problem as _n4_load_problem
    except Exception:
        _n4_load_problem = None

# --- Import các ngách cập nhật/sửa biên từ N5 (Quỳnh Ngân) ---
try:
    from n5_quynh_ngan_buoc_woa import make_woa_hooks as _n5_make_woa_hooks
except Exception:
    try:
        from src.n5_quynh_ngan_buoc_woa import make_woa_hooks as _n5_make_woa_hooks
    except Exception:
        _n5_make_woa_hooks = None

# --- Import hàm woa() chung từ N6 (Vân Lâm) ---
try:
    from src.n6_van_lam_woa import woa as _n6_woa, linear_a, author_a2
except Exception:
    try:
        from n6_van_lam_woa import woa as _n6_woa, linear_a, author_a2
    except Exception:
        _n6_woa = None
        linear_a = None
        author_a2 = None


# ==============================================================================
# 1. DỮ LIỆU 3 CA GỐC (A: CƠ BẢN, B: KHE HẸP, C: CHẮN ĐƯỜNG) & CHỈNH SỬA ĐỀ
# ==============================================================================
CASE_LABELS = {
    "A": "Ca A · Cơ bản (co_ban)",
    "B": "Ca B · Khe hẹp (khe_hep)",
    "C": "Ca C · Chắn đường (chan_duong)",
}


def get_problem_case(case_id: str = "A") -> Dict[str, Any]:
    """Trả về cấu hình chuẩn của 1 trong 3 ca A, B, C (khớp 100% cấu trúc N3/N4/N9)."""
    cid = str(case_id).strip().upper()
    if cid not in ("A", "B", "C"):
        raise ValueError(f"Mã ca phải là 'A', 'B' hoặc 'C', nhận '{case_id}'.")

    # Thử tải qua N4 nếu file JSON đã tồn tại và hợp lệ với chuẩn N3
    if _n4_load_problem is not None:
        alias = {"A": "co_ban", "B": "khe_hep", "C": "chan_duong"}[cid]
        try:
            prob = _n4_load_problem(alias)
            if "target" in prob and "budget" in prob and "safety" in prob:
                return copy.deepcopy(prob)
        except Exception:
            pass

    prob: Dict[str, Any] = {
        "case_id": cid,
        "title": CASE_LABELS[cid],
        "start": [0.0, 50.0],
        "target": [100.0, 50.0],
        "safety": 2.0,
        "budget": 220.0,
        "flight_cost": 0.45,
        "signal_range": 18.0,
        "alpha": 0.1,
        "beacon_max": 25.0,
        "active_lights": 10,
        "length_weight": 0.12,
        "collision_weight": 100.0,
        "battery_weight": 30.0,
        "map_weight": 100.0,
        "camps": [
            {"name": "C1", "x": 12.0, "y": 70.0, "w": 12.0},
            {"name": "C2", "x": 20.0, "y": 25.0, "w": 18.0},
            {"name": "C3", "x": 38.0, "y": 31.0, "w": 15.0},
            {"name": "C4", "x": 43.0, "y": 85.0, "w": 20.0},
            {"name": "C5", "x": 61.0, "y": 43.0, "w": 16.0},
            {"name": "C6", "x": 65.0, "y": 83.0, "w": 12.0},
            {"name": "C7", "x": 84.0, "y": 63.0, "w": 18.0},
            {"name": "C8", "x": 90.0, "y": 22.0, "w": 14.0},
        ],
    }

    if cid == "A":
        # Dữ liệu Ca A trong tài liệu WOA-2.pdf trang 8
        prob["storms"] = [
            {"name": "V1", "x": 28.0, "y": 48.0, "r": 11.0},
            {"name": "V2", "x": 51.0, "y": 66.0, "r": 12.0},
            {"name": "V3", "x": 73.0, "y": 40.0, "r": 11.0},
        ]
    elif cid == "B":
        # Dữ liệu Ca B trong tài liệu WOA-2.pdf trang 13
        prob["storms"] = [
            {"name": "V1", "x": 40.0, "y": 29.0, "r": 16.0},
            {"name": "V2", "x": 40.0, "y": 71.0, "r": 16.0},
            {"name": "V3", "x": 73.0, "y": 50.0, "r": 11.0},
        ]
        prob["gate"] = {"x": 40.0, "y_min": 47.0, "y_max": 53.0}
    elif cid == "C":
        # Dữ liệu Ca C trong tài liệu WOA-2.pdf trang 13
        prob["storms"] = [
            {"name": "V1", "x": 28.0, "y": 50.0, "r": 14.0},
            {"name": "V2", "x": 50.0, "y": 50.0, "r": 14.0},
            {"name": "V3", "x": 72.0, "y": 50.0, "r": 14.0},
        ]
    return prob


def customize_problem(
    base_problem: Dict[str, Any],
    target_xy: Optional[Tuple[float, float]] = None,
    storms_xyr: Optional[List[Tuple[float, float, float]]] = None,
    active_lights: int = 10,
) -> Dict[str, Any]:
    """Tạo bản sao đề bài đã cập nhật điểm đích T, 3 bão (x, y, r) và số đèn tối đa K."""
    prob = copy.deepcopy(base_problem)
    if active_lights not in (6, 8, 10):
        raise ValueError("Số đèn tối đa K phải thuộc {6, 8, 10}.")
    prob["active_lights"] = int(active_lights)

    if target_xy is not None:
        tx, ty = float(target_xy[0]), float(target_xy[1])
        if not (0.0 <= tx <= 100.0 and 0.0 <= ty <= 100.0):
            raise ValueError("Tọa độ điểm đích T phải nằm trong [0, 100].")
        prob["target"] = [tx, ty]

    if storms_xyr is not None:
        if len(storms_xyr) != len(prob["storms"]):
            raise ValueError(f"Cần đủ {len(prob['storms'])} vùng bão.")
        for idx, (sx, sy, sr) in enumerate(storms_xyr):
            sx, sy, sr = float(sx), float(sy), float(sr)
            if not (0.0 <= sx <= 100.0 and 0.0 <= sy <= 100.0):
                raise ValueError(f"Tâm bão V{idx + 1} phải nằm trong [0, 100].")
            if sr <= 0.0 or sr > 50.0:
                raise ValueError(f"Bán kính bão V{idx + 1} phải nằm trong (0, 50].")
            prob["storms"][idx]["x"] = sx
            prob["storms"][idx]["y"] = sy
            prob["storms"][idx]["r"] = sr

    return prob


# ==============================================================================
# 2. HÀM GIẢI MÃ & CHẤM ĐIỂM (GỌI N3 NẾU CÓ, ĐẢM BẢO KHỚP 100% CÔNG THỨC NHÓM)
# ==============================================================================
def decode_beacons(whale: List[float], problem: Dict[str, Any]) -> List[Dict[str, Any]]:
    k_limit = int(problem.get("active_lights", 10))
    beacons = [
        {
            "index": k + 1,
            "x": float(whale[3 * k]),
            "y": float(whale[3 * k + 1]),
            "proposed": float(whale[3 * k + 2]),
            "energy": float(whale[3 * k + 2]),
            "active": False,
        }
        for k in range(10)
    ]
    # Chọn top-K pin đề xuất lớn nhất; hòa pin ưu tiên chỉ số nhỏ hơn
    ranked = sorted(range(10), key=lambda idx: (-beacons[idx]["proposed"], idx))
    for idx in ranked[:k_limit]:
        beacons[idx]["active"] = True
    for b in beacons:
        if not b["active"]:
            b["energy"] = 0.0
    return beacons


def _dist_seg(point: List[float], a: List[float], b: List[float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    sq = dx * dx + dy * dy
    if sq == 0.0:
        return math.hypot(point[0] - a[0], point[1] - a[1])
    tau = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / sq))
    hx, hy = a[0] + tau * dx, a[1] + tau * dy
    return math.hypot(point[0] - hx, point[1] - hy)


def _crosses_gate(points: List[List[float]], problem: Dict[str, Any]) -> bool:
    if "gate" not in problem:
        return False
    gate = problem["gate"]
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        if a[0] < gate["x"] <= b[0] and b[0] != a[0]:
            frac = (gate["x"] - a[0]) / (b[0] - a[0])
            y = a[1] + frac * (b[1] - a[1])
            if gate["y_min"] <= y <= gate["y_max"]:
                return True
    return False


def evaluate_whale(whale: List[float], problem: Dict[str, Any]) -> Dict[str, Any]:
    """Chấm điểm 1 cá voi 30 biến, ưu tiên gọi trực tiếp evaluate() của N3."""
    w_list = [float(v) for v in whale]
    if _n3_evaluate is not None:
        try:
            rep = _n3_evaluate(w_list, problem)
            if "beacons" not in rep:
                rep["beacons"] = decode_beacons(w_list, problem)
            return rep
        except Exception:
            pass

    if len(w_list) != 30:
        raise ValueError("Mỗi cá voi phải có đúng 30 biến.")
    beacons = decode_beacons(w_list, problem)
    points = [list(problem["start"])] + [[b["x"], b["y"]] for b in beacons] + [list(problem["target"])]

    length = 0.0
    collision = 0.0
    clearance = None
    bad_segments = []
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        length += math.hypot(b[0] - a[0], b[1] - a[1])
        seg_bad = False
        for storm in problem["storms"]:
            safe_r = float(storm["r"]) + float(problem["safety"])
            gap = _dist_seg([storm["x"], storm["y"]], a, b) - safe_r
            if clearance is None or gap < clearance:
                clearance = gap
            if gap < -1e-9:
                seg_bad = True
            depth = max(0.0, -gap) / safe_r
            collision += depth * depth
        if seg_bad:
            bad_segments.append(i)

    flight = float(problem["flight_cost"]) * length
    lamps = sum(b["energy"] for b in beacons)
    total_energy = flight + lamps
    over = max(0.0, total_energy - float(problem["budget"])) / float(problem["budget"])

    weighted_sat, weight_sum = 0.0, 0.0
    satisfaction = []
    range_sq = float(problem["signal_range"]) ** 2
    for camp in problem["camps"]:
        lvl = sum(
            b["energy"] / (1.0 + ((b["x"] - camp["x"]) ** 2 + (b["y"] - camp["y"]) ** 2) / range_sq)
            for b in beacons
        )
        sat = 1.0 - math.exp(-float(problem["alpha"]) * lvl)
        satisfaction.append(sat)
        weighted_sat += float(camp["w"]) * sat
        weight_sum += float(camp["w"])
    utility_sat = weighted_sat / weight_sum
    minimum_service = min(satisfaction) if satisfaction else 0.0

    box_ok = all(
        math.isfinite(w_list[3 * k + j]) and 0.0 <= w_list[3 * k + j] <= [100.0, 100.0, float(problem["beacon_max"])][j]
        for k in range(10)
        for j in range(3)
    )
    pmap = sum(
        (max(0.0, -v, v - 100.0) / 100.0) ** 2
        for k in range(10)
        for v in (w_list[3 * k], w_list[3 * k + 1])
    )
    base_score = -utility_sat + float(problem["length_weight"]) * length / 100.0
    penalty = (
        float(problem["collision_weight"]) * collision
        + float(problem["battery_weight"]) * over * over
        + float(problem["map_weight"]) * pmap
    )
    geometry_ok = clearance is None or clearance >= -1e-9
    energy_ok = total_energy <= float(problem["budget"]) + 1e-7
    valid = box_ok and geometry_ok and energy_ok

    return {
        "score": base_score + penalty,
        "base_score": base_score,
        "penalty": penalty,
        "valid": valid,
        "box_ok": box_ok,
        "geometry_ok": geometry_ok,
        "energy_ok": energy_ok,
        "map_violation": pmap,
        "beacons": beacons,
        "points": points,
        "through_gate": valid and _crosses_gate(points, problem),
        "length": length,
        "collision": collision,
        "clearance": clearance,
        "bad_segments": bad_segments,
        "flight": flight,
        "lamps": lamps,
        "total": total_energy,
        "over": over,
        "utility_sat": utility_sat,
        "minimum_service": minimum_service,
        "satisfaction": satisfaction,
    }


# ==============================================================================
# 3. CÁC NGÁCH (LỊCH a, KIỂU l, SỬA BIÊN) & CHẠY QUA HÀM WOA CHUNG CỦA N6
# ==============================================================================
def make_a_schedule(a_mode: str = "linear") -> Callable[[int, int], float]:
    """Ngách 3: Lịch giảm hệ số a ('linear', 'cosine', 'quadratic')."""
    mode = str(a_mode).strip().lower()
    if mode == "linear":
        return lambda k, T: 2.0 * (1.0 - k / T)
    if mode == "cosine":
        return lambda k, T: 1.0 + math.cos(math.pi * (k / T))
    if mode == "quadratic":
        return lambda k, T: 2.0 * ((1.0 - k / T) ** 2)
    raise ValueError(f"Lịch a không hợp lệ: '{a_mode}'. Chọn 'linear', 'cosine' hoặc 'quadratic'.")


def _fallback_woa_hooks(l_mode: str = "shared_l", boundary_mode: str = "clip", seed: int = 0):
    """Dự phòng khi chạy độc lập ngoài repo mà chưa có file n5_quynh_ngan_buoc_woa.py."""
    if _n5_make_woa_hooks is not None:
        return _n5_make_woa_hooks(l_mode=l_mode, boundary_mode=boundary_mode, seed=seed)

    streams = {}

    def _reset():
        streams["aux"] = np.random.default_rng(seed + 1_000_003)
        streams["fix"] = np.random.default_rng(seed + 2_000_029)

    _reset()

    def init_fn(rng, n_whales, lower, upper):
        _reset()
        return lower + rng.random((n_whales, len(lower))) * (upper - lower)

    def update_fn(pop, leader, a, a2, rng, b=1.0):
        work = pop.copy()
        n_whales, dim = work.shape
        for i in range(n_whales):
            r1, r2 = float(rng.random()), float(rng.random())
            A, C = 2.0 * a * r1 - a, 2.0 * r2
            l0 = 1.0 + (a2 - 1.0) * float(rng.random())
            l_vals = np.full(dim, l0) if l_mode == "shared_l" else 1.0 + (a2 - 1.0) * streams["aux"].random(dim)
            p = float(rng.random())
            if p < 0.5:
                if abs(A) >= 1.0:
                    rand_idx = streams["aux"] if False else rng.integers(0, n_whales, size=dim)
                    x_rand = work[rand_idx, np.arange(dim)]
                    work[i] = x_rand - A * np.abs(C * x_rand - work[i])
                else:
                    work[i] = leader - A * np.abs(C * leader - work[i])
            else:
                d_prime = np.abs(leader - work[i])
                work[i] = d_prime * np.exp(b * l_vals) * np.cos(2.0 * np.pi * l_vals) + leader
        return work

    def bounds_fn(pop, lower, upper):
        if boundary_mode == "clip":
            return np.clip(pop, lower, upper)
        out = pop.copy()
        mask = (out < lower) | (out > upper)
        if np.any(mask):
            re_vals = lower + streams["fix"].random(out.shape) * (upper - lower)
            out[mask] = re_vals[mask]
        return out

    return init_fn, update_fn, bounds_fn


def _fallback_woa_core(
    evaluate_fn, lower, upper, n_whales, n_iter, seed=0, snapshot_every=10, b=1.0,
    init_fn=None, update_fn=None, bounds_fn=None, a_fn=None, a2_fn=None
):
    """Chỉ dùng nếu thiếu hẳn file n6_van_lam_woa.py; nếu có N6 thì gọi thẳng N6."""
    if _n6_woa is not None:
        return _n6_woa(
            evaluate_fn, lower, upper, n_whales, n_iter,
            seed=seed, snapshot_every=snapshot_every, b=b,
            init_fn=init_fn, update_fn=update_fn, bounds_fn=bounds_fn,
            a_fn=a_fn, a2_fn=a2_fn,
        )

    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    rng = np.random.default_rng(seed)
    ledgers = {"best_overall": None, "best_valid": None, "best_gate": None}
    history, snapshots = [], []
    pop = init_fn(rng, n_whales, lower, upper)
    n_evals = 0

    for t in range(1, n_iter + 1):
        a, a2 = None, None
        if t > 1:
            k = t - 2
            a = a_fn(k, n_iter)
            a2 = a2_fn(k, n_iter)
            leader = ledgers["best_overall"]["x"].copy()
            pop = update_fn(pop.copy(), leader, a, a2, rng, b)
        pop = bounds_fn(np.asarray(pop, dtype=float), lower, upper)
        recs = [evaluate_fn(w.copy()) for w in pop]
        n_evals += n_whales
        for i, r in enumerate(recs):
            x = pop[i]
            if ledgers["best_overall"] is None or r["score"] < ledgers["best_overall"]["score"]:
                ledgers["best_overall"] = {"x": x.copy(), "score": float(r["score"]), "base_score": float(r["base_score"]), "valid": bool(r["valid"]), "through_gate": bool(r["through_gate"]), "iteration": t, "whale": i}
            if r["valid"]:
                if ledgers["best_valid"] is None or r["base_score"] < ledgers["best_valid"]["base_score"]:
                    ledgers["best_valid"] = {"x": x.copy(), "score": float(r["score"]), "base_score": float(r["base_score"]), "valid": True, "through_gate": bool(r["through_gate"]), "iteration": t, "whale": i}
                if r["through_gate"]:
                    if ledgers["best_gate"] is None or r["base_score"] < ledgers["best_gate"]["base_score"]:
                        ledgers["best_gate"] = {"x": x.copy(), "score": float(r["score"]), "base_score": float(r["base_score"]), "valid": True, "through_gate": True, "iteration": t, "whale": i}
        bo, bv, bg = ledgers["best_overall"], ledgers["best_valid"], ledgers["best_gate"]
        history.append({
            "iteration": t, "a": a, "a2": a2,
            "best_overall_score": bo["score"],
            "best_valid_base": None if bv is None else bv["base_score"],
            "best_gate_base": None if bg is None else bg["base_score"],
            "mean_score": float(np.mean([r["score"] for r in recs])),
            "n_valid": sum(bool(r["valid"]) for r in recs),
            "n_gate": sum(bool(r["through_gate"]) for r in recs),
            "n_evaluations": n_evals,
        })
        if t == 1 or t == n_iter or t % snapshot_every == 0:
            snapshots.append({
                "iteration": t,
                "population": pop.copy(),
                "score": np.array([r["score"] for r in recs]),
                "base_score": np.array([r["base_score"] for r in recs]),
                "valid": np.array([r["valid"] for r in recs]),
                "through_gate": np.array([r["through_gate"] for r in recs]),
            })
    res = dict(ledgers)
    res["history"] = history
    res["snapshots"] = snapshots
    res["final_population"] = snapshots[-1]
    res["n_evaluations"] = n_evals
    return res


def run_demo_experiment(
    case_id: str = "A",
    n_whales: int = 30,
    n_iter: int = 200,
    seed: int = 7,
    a_mode: str = "linear",
    l_mode: str = "shared_l",
    boundary_mode: str = "clip",
    active_lights: int = 10,
    target_xy: Optional[Tuple[float, float]] = None,
    storms_xyr: Optional[List[Tuple[float, float, float]]] = None,
    snapshot_every: int = 5,
) -> Dict[str, Any]:
    """
    Hàm điều phối trung tâm của Bảo Ngọc (N10):
    Gọi đúng lõi woa() của N6 + hook N5 + lịch a N4 + chấm điểm N3.
    """
    base_prob = get_problem_case(case_id)
    problem = customize_problem(
        base_prob,
        target_xy=target_xy,
        storms_xyr=storms_xyr,
        active_lights=active_lights,
    )

    lower = np.array([0.0, 0.0, 0.0] * 10, dtype=float)
    upper = np.array([100.0, 100.0, float(problem["beacon_max"])] * 10, dtype=float)

    init_fn, update_fn, bounds_fn = _fallback_woa_hooks(
        l_mode=l_mode, boundary_mode=boundary_mode, seed=int(seed)
    )
    a_fn = make_a_schedule(a_mode)
    a2_fn = author_a2 if author_a2 is not None else (lambda k, T: -1.0 - k / T)

    raw_res = _fallback_woa_core(
        evaluate_fn=lambda w: evaluate_whale(w, problem),
        lower=lower,
        upper=upper,
        n_whales=int(n_whales),
        n_iter=int(n_iter),
        seed=int(seed),
        snapshot_every=max(1, int(snapshot_every)),
        b=1.0,
        init_fn=init_fn,
        update_fn=update_fn,
        bounds_fn=bounds_fn,
        a_fn=a_fn,
        a2_fn=a2_fn,
    )

    # Bổ sung báo cáo chi tiết cho best_overall, best_valid, best_gate để giao diện không tính lại
    reports = {}
    for key in ("best_overall", "best_valid", "best_gate"):
        entry = raw_res.get(key)
        if entry is not None:
            reports[key] = evaluate_whale(entry["x"], problem)
        else:
            reports[key] = None

    config = {
        "case_id": case_id,
        "n_whales": int(n_whales),
        "n_iter": int(n_iter),
        "seed": int(seed),
        "a_mode": a_mode,
        "l_mode": l_mode,
        "boundary_mode": boundary_mode,
        "active_lights": int(active_lights),
        "snapshot_every": max(1, int(snapshot_every)),
        "b_spiral": 1.0,
        "p_threshold": 0.5,
    }

    return {
        "problem": problem,
        "config": config,
        "best_overall": raw_res["best_overall"],
        "best_valid": raw_res["best_valid"],
        "best_gate": raw_res["best_gate"],
        "reports": reports,
        "history": raw_res["history"],
        "snapshots": raw_res["snapshots"],
        "final_population": raw_res["final_population"],
        "n_evaluations": raw_res["n_evaluations"],
    }


# ==============================================================================
# 4. VẼ BẢN ĐỒ TOÀN ĐÀN & PHÁT LẠI (KHỚP PHONG CÁCH N9 - TRANG NGUYỄN)
# ==============================================================================
def _draw_light_bulb(ax, x: float, y: float, energy: float) -> None:
    scale = 0.7 + 0.03 * energy
    bulb = Circle(
        (x, y), 1.8 * scale,
        facecolor="#f7c75e", edgecolor="#916b18", linewidth=1.2, zorder=10, clip_on=False
    )
    base = plt.Rectangle(
        (x - 0.7 * scale, y - 2.5 * scale), 1.4 * scale, 1.0 * scale,
        facecolor="#b0b0b0", edgecolor="#606060", zorder=9, clip_on=False
    )
    ax.add_patch(bulb)
    ax.add_patch(base)


def select_snapshot_display(
    result: Dict[str, Any],
    snapshot_idx: int = -1,
    view_mode: str = "best_valid",
) -> Tuple[Dict[str, Any], Dict[str, Any], str, bool]:
    """
    Lấy snapshot tại chỉ số `snapshot_idx` và chọn nghiệm hiển thị theo `view_mode`
    ('best_valid' hoặc 'best_overall'). Trả về: (snap, report, badge_text, is_fallback_warning).
    """
    problem = result["problem"]
    snapshots = result["snapshots"]
    idx = max(-len(snapshots), min(len(snapshots) - 1, int(snapshot_idx)))
    snap = snapshots[idx]
    pop = snap["population"]
    valid_mask = snap["valid"]
    scores = snap["score"]
    base_scores = snap["base_score"]

    warning_no_valid = False
    chosen_whale = None

    if view_mode == "best_valid":
        valid_indices = [i for i, ok in enumerate(valid_mask) if bool(ok)]
        if valid_indices:
            best_i = min(valid_indices, key=lambda i: float(base_scores[i]))
            chosen_whale = pop[best_i]
            badge = "Đang xem: Nghiệm HỢP LỆ tốt nhất trong lượt"
        else:
            warning_no_valid = True
            best_i = int(np.argmin(scores))
            chosen_whale = pop[best_i]
            badge = "Cảnh báo: Chưa có nghiệm hợp lệ -> tạm hiện best_overall"
    else:
        best_i = int(np.argmin(scores))
        chosen_whale = pop[best_i]
        badge = "Đang xem: best_overall (J thấp nhất)"

    report = evaluate_whale(chosen_whale, problem)
    return snap, report, badge, warning_no_valid


def render_demo_figure(
    result: Dict[str, Any],
    snapshot_idx: int = -1,
    view_mode: str = "best_valid",
    show_swarm: bool = True,
) -> matplotlib.figure.Figure:
    """Vẽ 2 khung trực quan: (Trái) Bản đồ 100x100 & toàn đàn; (Phải) Đường hội tụ J và f0."""
    problem = result["problem"]
    cfg = result["config"]
    snap, report, badge, warning_no_valid = select_snapshot_display(result, snapshot_idx, view_mode)

    fig, (ax_map, ax_conv) = plt.subplots(1, 2, figsize=(14.5, 6.4), dpi=110, facecolor="#faf9f5")
    ax_map.set_facecolor("#ffffff")
    ax_conv.set_facecolor("#ffffff")

    # 1. Vẽ 3 vùng bão + vòng nét đứt biên an toàn (+2)
    for storm in problem["storms"]:
        center = (storm["x"], storm["y"])
        ax_map.add_patch(Circle(center, storm["r"], facecolor="#f0a6ca", alpha=0.55, zorder=1))
        ax_map.add_patch(
            Circle(center, storm["r"] + problem["safety"], fill=False, edgecolor="#d87a99", linestyle="--", linewidth=1.3, zorder=2)
        )
        ax_map.text(storm["x"], storm["y"], storm["name"], ha="center", va="center", fontsize=9, weight="bold", color="#8b0000", zorder=6)

    # 2. Vẽ cổng khe hẹp (Ca B)
    if "gate" in problem:
        gate = problem["gate"]
        ax_map.plot([gate["x"], gate["x"]], [gate["y_min"], gate["y_max"]], color="#7a3eb1", linewidth=4.2, zorder=7, label="Khe hẹp [47, 53]")

    # 3. Vẽ cả đàn cá voi (các đường màu xám mờ)
    if show_swarm:
        pop = snap["population"]
        for whale in pop:
            xs = [problem["start"][0]] + [whale[3 * k] for k in range(10)] + [problem["target"][0]]
            ys = [problem["start"][1]] + [whale[3 * k + 1] for k in range(10)] + [problem["target"][1]]
            ax_map.plot(xs, ys, color="#646e77", alpha=0.14, linewidth=0.9, zorder=3)

    # 4. Vẽ 8 trại cứu hộ
    for camp in problem["camps"]:
        ax_map.scatter(camp["x"], camp["y"], marker="D", s=34, color="#233848", zorder=8)
        ax_map.text(camp["x"] + 1.4, camp["y"] + 1.4, f"{camp['name']}(w={int(camp['w'])})", fontsize=8, weight="bold", color="#233848", zorder=8)

    # 5. Vẽ đường bay được chọn & 10 điểm đèn (bật = bóng đèn vàng, tắt = chấm trắng viền xanh)
    pts = report["points"]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        seg_color = "#cb3945" if i in report["bad_segments"] else "#126aaf"
        ax_map.plot([a[0], b[0]], [a[1], b[1]], color=seg_color, linewidth=2.4, zorder=9)

    for beacon in report["beacons"]:
        if beacon["energy"] > 0.001:
            _draw_light_bulb(ax_map, beacon["x"], beacon["y"], beacon["energy"])
        else:
            ax_map.scatter(beacon["x"], beacon["y"], s=28, facecolor="white", edgecolor="#126aaf", linewidth=1.2, zorder=10, clip_on=False)

    # 6. Điểm xuất phát S và đích T
    for lbl, pt in [("S", problem["start"]), ("T", problem["target"])]:
        ax_map.scatter(pt[0], pt[1], s=60, color="black", zorder=11, clip_on=False)
        offset = 2.0 if lbl == "S" else -4.5
        ax_map.text(pt[0] + offset, pt[1] + 2.8, lbl, weight="bold", fontsize=10, zorder=11)

    status_str = "HỢP LỆ" if report["valid"] else "CHƯA HỢP LỆ"
    gate_str = " · QUA KHE" if report["through_gate"] else ""
    ax_map.set_xlim(-5, 105)
    ax_map.set_ylim(-5, 105)
    ax_map.set_aspect("equal")
    ax_map.set_xticks([0, 25, 50, 75, 100])
    ax_map.set_yticks([0, 25, 50, 75, 100])
    ax_map.grid(alpha=0.15)
    ax_map.set_title(
        f"Số lượt: {snap['iteration']}/{cfg['n_iter']} · {status_str}{gate_str}\n"
        f"U = {report['utility_sat']:.4f} · u_min = {report['minimum_service']:.3f} · Pin = {report['total']:.1f}/220 · L = {report['length']:.1f}",
        fontsize=10,
        weight="bold",
        color="#8b0000" if warning_no_valid else "#20394b",
        pad=8,
    )
    ax_map.text(
        0.02, 0.02, badge, transform=ax_map.transAxes, fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff3cd" if warning_no_valid else "#e8f4f8", edgecolor="#cccccc")
    )

    # 7. Biểu đồ hội tụ bên phải
    hist = result["history"]
    iters = [h["iteration"] for h in hist]
    j_vals = [h["best_overall_score"] for h in hist]
    f0_vals = [h["best_valid_base"] if h["best_valid_base"] is not None else np.nan for h in hist]

    ax_conv.plot(iters, j_vals, color="#126aaf", linewidth=2.0, label="best_overall (J có phạt)")
    if not all(np.isnan(f0_vals)):
        ax_conv.plot(iters, f0_vals, color="#2e8b57", linewidth=2.0, linestyle="--", label="best_valid (f0 hợp lệ)")
    ax_conv.axvline(snap["iteration"], color="#cb3945", linestyle=":", linewidth=1.6, label=f"Mốc đang xem (lượt {snap['iteration']})")
    ax_conv.set_xlabel("Số lượt chấm (Iteration)", fontsize=10)
    ax_conv.set_ylabel("Giá trị hàm mục tiêu (càng nhỏ càng tốt)", fontsize=10)
    ax_conv.set_title(
        f"Quá trình hội tụ · {problem.get('title', cfg['case_id'])} (seed={cfg['seed']})\n"
        f"Ngách: a={cfg['a_mode']}, l={cfg['l_mode']}, biên={cfg['boundary_mode']}, K={cfg['active_lights']}",
        fontsize=10,
        weight="bold",
        color="#20394b",
        pad=8,
    )
    ax_conv.grid(alpha=0.2)
    ax_conv.legend(loc="upper right", fontsize=8.5)

    fig.tight_layout()
    return fig


# ==============================================================================
# 5. LƯU / MỞ LẠI KẾT QUẢ JSON (KÈM PROBLEM) & XUẤT PNG / HTML DỰ PHÒNG
# ==============================================================================
def _to_json_safe(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, dict):
        return {str(k): _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(v) for v in obj]
    return obj


def serialize_result_json(result: Dict[str, Any]) -> str:
    """Đóng gói trọn vẹn problem + config + ledgers + snapshots ra chuỗi JSON để mở lại."""
    payload = _to_json_safe(result)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def load_result_json(raw_text: str) -> Dict[str, Any]:
    """Đọc lại kết quả đã lưu, khôi phục mảng numpy và giữ nguyên `problem` gốc của file."""
    data = json.loads(raw_text)
    if "problem" not in data or "snapshots" not in data:
        raise ValueError("File JSON không đúng định dạng kết quả demo WOA.")
    for snap in data["snapshots"]:
        snap["population"] = np.asarray(snap["population"], dtype=float)
        snap["score"] = np.asarray(snap["score"], dtype=float)
        snap["base_score"] = np.asarray(snap["base_score"], dtype=float)
        snap["valid"] = np.asarray(snap["valid"], dtype=bool)
        snap["through_gate"] = np.asarray(snap["through_gate"], dtype=bool)
    return data


def export_figure_png_bytes(fig: matplotlib.figure.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    buf.seek(0)
    return buf.read()


def export_backup_html(result: Dict[str, Any]) -> str:
    """Tạo file HTML dự phòng tự chứa ảnh PNG + bảng chỉ số khi trình chiếu offline."""
    fig = render_demo_figure(result, snapshot_idx=-1, view_mode="best_valid", show_swarm=True)
    png_b64 = base64.b64encode(export_figure_png_bytes(fig)).decode("ascii")
    plt.close(fig)

    rep = result["reports"]["best_valid"] or result["reports"]["best_overall"]
    cfg = result["config"]
    status = "HỢP LỆ" if rep["valid"] else "CHƯA HỢP LỆ"
    return f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="utf-8"><title>Demo WOA Đom Đóm - Dự phòng</title>
<style>body{{font-family:sans-serif;background:#faf9f5;color:#20394b;padding:24px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px;margin-bottom:16px}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:8px;text-align:center}}</style>
</head><body>
<h2>Báo cáo dự phòng Demo WOA – Bài toán Đom Đóm</h2>
<div class="card"><b>Cấu hình:</b> Ca {cfg['case_id']} | N={cfg['n_whales']} | Số lượt T={cfg['n_iter']} | seed={cfg['seed']}
| Ngách: a={cfg['a_mode']}, l={cfg['l_mode']}, biên={cfg['boundary_mode']}, K={cfg['active_lights']}</div>
<div class="card"><table>
<tr><th>Trạng thái</th><th>Hữu dụng U</th><th>Trại yếu u_min</th><th>Chiều dài L</th><th>Pin tổng</th><th>Điểm f0</th><th>Điểm J</th></tr>
<tr><td><b>{status}</b></td><td>{rep['utility_sat']:.4f}</td><td>{rep['minimum_service']:.4f}</td>
<td>{rep['length']:.2f}</td><td>{rep['total']:.2f} / 220</td><td>{rep.get('f0', rep['base_score']):.4f}</td><td>{rep['score']:.4f}</td></tr>
</table></div>
<div class="card"><img src="data:image/png;base64,{png_b64}" style="max-width:100%"/></div>
</body></html>"""

def show_notebook_controls():
    """Hàm hiển thị bảng điều khiển tương tác trên Google Colab / Jupyter Notebook."""
    import time
    import ipywidgets as widgets
    from IPython.display import clear_output, display

    state = {"result": None}

    w_case = widgets.Dropdown(options=[(v, k) for k, v in CASE_LABELS.items()], value="A", description="Ca đề:")
    w_n = widgets.IntSlider(value=30, min=10, max=80, step=5, description="Số cá voi N:")
    w_iter = widgets.IntSlider(value=250, min=20, max=1000, step=20, description="Số lượt:")
    w_seed = widgets.IntText(value=7, description="Seed:")
    w_snap = widgets.Dropdown(options=[1, 2, 5, 10, 20], value=5, description="Bước lưu:")

    w_a = widgets.Dropdown(options=["linear", "cosine", "quadratic"], value="linear", description="Lịch a:")
    w_l = widgets.Dropdown(options=["shared_l", "independent_l"], value="shared_l", description="Kiểu l:")
    w_b = widgets.Dropdown(options=["clip", "reinit"], value="clip", description="Sửa biên:")
    w_k = widgets.Dropdown(options=[10, 8, 6], value=10, description="Số đèn K:")

    w_tx = widgets.FloatText(value=100.0, description="Đích T (x):")
    w_ty = widgets.FloatText(value=50.0, description="Đích T (y):")

    storm_widgets = [
        (
            widgets.FloatText(value=28.0, description=f"V{i+1} x:"),
            widgets.FloatText(value=48.0, description=f"V{i+1} y:"),
            widgets.FloatText(value=11.0, description=f"V{i+1} r:"),
        )
        for i in range(3)
    ]

    def sync_map_defaults(_=None):
        p = get_problem_case(w_case.value)
        w_tx.value, w_ty.value = p["target"][0], p["target"][1]
        for i, st_obj in enumerate(p["storms"]):
            storm_widgets[i][0].value = st_obj["x"]
            storm_widgets[i][1].value = st_obj["y"]
            storm_widgets[i][2].value = st_obj["r"]

    w_case.observe(sync_map_defaults, names="value")
    sync_map_defaults()

    w_view = widgets.ToggleButtons(
        options=[("best_valid (Hợp lệ)", "best_valid"), ("best_overall (J thấp nhất)", "best_overall")],
        description="Chế độ xem:",
    )
    w_swarm = widgets.Checkbox(value=True, description="Hiện cả đàn")
    w_slider = widgets.IntSlider(value=0, min=0, max=0, description="Mốc replay:")

    btn_run = widgets.Button(description="Chạy WOA", button_style="primary")
    btn_play = widgets.Button(description="Play / Replay", button_style="info")
    btn_export = widgets.Button(description="Xuất PNG / JSON / HTML", button_style="success")
    out_area = widgets.Output()

    def draw_current(idx=None):
        if state["result"] is None:
            return
        snap_i = w_slider.value if idx is None else idx
        with out_area:
            clear_output(wait=True)
            fig = render_demo_figure(state["result"], snapshot_idx=snap_i, view_mode=w_view.value, show_swarm=w_swarm.value)
            plt.show()
            plt.close(fig)

    def on_run_clicked(_):
        storms_xyr = [(sw[0].value, sw[1].value, sw[2].value) for sw in storm_widgets]
        state["result"] = run_demo_experiment(
            case_id=w_case.value,
            n_whales=w_n.value,
            n_iter=w_iter.value,
            seed=w_seed.value,
            a_mode=w_a.value,
            l_mode=w_l.value,
            boundary_mode=w_b.value,
            active_lights=w_k.value,
            target_xy=(w_tx.value, w_ty.value),
            storms_xyr=storms_xyr,
            snapshot_every=w_snap.value,
        )
        n_snaps = len(state["result"]["snapshots"])
        w_slider.max = max(0, n_snaps - 1)
        w_slider.value = max(0, n_snaps - 1)
        draw_current(w_slider.value)

    def on_play_clicked(_):
        if state["result"] is None:
            return
        for i in range(len(state["result"]["snapshots"])):
            w_slider.value = i
            draw_current(i)
            time.sleep(0.12)

    def on_export_clicked(_):
        if state["result"] is None:
            return
        cfg = state["result"]["config"]
        prefix = f"demo_{cfg['case_id']}_seed{cfg['seed']}_{cfg['a_mode']}"
        fig = render_demo_figure(state["result"], snapshot_idx=w_slider.value, view_mode=w_view.value, show_swarm=w_swarm.value)
        with open(f"{prefix}.png", "wb") as f:
            f.write(export_figure_png_bytes(fig))
        plt.close(fig)
        with open(f"{prefix}.json", "w", encoding="utf-8") as f:
            f.write(serialize_result_json(state["result"]))
        with open(f"{prefix}.html", "w", encoding="utf-8") as f:
            f.write(export_backup_html(state["result"]))
        with out_area:
            print(f"Đã xuất thành công: {prefix}.png, {prefix}.json, {prefix}.html")

    btn_run.on_click(on_run_clicked)
    btn_play.on_click(on_play_clicked)
    btn_export.on_click(on_export_clicked)
    w_slider.observe(lambda _: draw_current(), names="value")
    w_view.observe(lambda _: draw_current(), names="value")
    w_swarm.observe(lambda _: draw_current(), names="value")

    ui = widgets.VBox([
        widgets.HBox([w_case, w_n, w_iter, w_seed, w_snap]),
        widgets.HBox([w_a, w_l, w_b, w_k]),
        widgets.HBox([w_tx, w_ty]),
        widgets.VBox([widgets.HBox(sw) for sw in storm_widgets]),
        widgets.HBox([btn_run, btn_play, btn_export]),
        widgets.HBox([w_view, w_swarm, w_slider]),
        out_area,
    ])
    display(ui)
    on_run_clicked(None)

if __name__ == "__main__":
    # Chạy kiểm tra nhanh trên terminal: python src/n10_bao_ngoc_demo.py
    demo_res = run_demo_experiment(case_id="A", n_whales=30, n_iter=150, seed=7, snapshot_every=15)
    out_dir = os.path.join(ROOT_DIR, "results", "demo_backup")
    os.makedirs(out_dir, exist_ok=True)

    fig = render_demo_figure(demo_res, snapshot_idx=-1, view_mode="best_valid", show_swarm=True)
    png_path = os.path.join(out_dir, "demo_ca_A_seed7.png")
    fig.savefig(png_path, dpi=140, bbox_inches="tight")
    plt.close(fig)

    json_path = os.path.join(out_dir, "demo_ca_A_seed7.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(serialize_result_json(demo_res))

    html_path = os.path.join(out_dir, "demo_ca_A_seed7.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(export_backup_html(demo_res))

    rep_show = demo_res["reports"]["best_valid"] or demo_res["reports"]["best_overall"]
    print("[OK] Đã chạy lõi N10 nối cùng N6:")
    print(f"  - Số lần chấm: {demo_res['n_evaluations']}")
    print(f"  - Hợp lệ: {rep_show['valid']} | U = {rep_show['utility_sat']:.4f} | Pin = {rep_show['total']:.2f}/220")
    print(f"  - Đã xuất bộ dự phòng: {png_path}, {json_path}, {html_path}")