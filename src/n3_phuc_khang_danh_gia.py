"""Phúc Khang: chấm đúng đề và kiểm xem đường đã đủ điều kiện chưa.

Bỏ phạt gấp khúc. Giữ pin 220, phạt bão 100, pin 30, ra map 100.
Biên còn được clip/re-init ở lõi; phạt map là kiểm tra bổ sung, không
phải một ngách để tiếp tục xoay nút nữa nhé.
"""
import math
from src.n1_hoang_tuan_hinh_hoc import path_metrics
from src.n2_quoc_phong_nang_luong import energy_metrics, signal_metrics
from src.n4_hoang_yen_du_lieu import decode


def crosses_gate(points, problem):
    if "gate" not in problem:
        return False
    gate = problem["gate"]
    for i in range(len(points) - 1):
        a = points[i]
        b = points[i + 1]
        if a[0] < gate["x"] <= b[0]:
            fraction = (gate["x"] - a[0]) / (b[0] - a[0])
            y = a[1] + fraction * (b[1] - a[1])
            if gate["y_min"] <= y <= gate["y_max"]:
                return True
    return False


def evaluate(whale, problem):
    if len(whale) != 30:
        raise ValueError("Bài nhóm giữ 30 biến: 10 bộ x, y, pin.")
    beacons = decode(whale, problem)
    points = [problem["start"]]
    box_ok = True
    map_violation = 0
    for k in range(10):
        beacon = beacons[k]
        points.append([beacon["x"], beacon["y"]])
        for value, limit in [[whale[3 * k], 100], [whale[3 * k + 1], 100],
                             [whale[3 * k + 2], problem["beacon_max"]]]:
            if not math.isfinite(value) or value < 0 or value > limit:
                box_ok = False
        for value in [beacon["x"], beacon["y"]]:
            excess = max(0, -value, value - 100) / 100
            map_violation += excess * excess
    points.append(problem["target"])
    path = path_metrics(points, problem["storms"], problem["safety"])
    energy = energy_metrics(path["length"], beacons, problem)
    signal = signal_metrics(beacons, problem)
    base_score = -signal["utility_sat"] + problem["length_weight"] * path["length"] / 100
    penalty = problem["collision_weight"] * path["collision"]
    penalty += problem["battery_weight"] * energy["over"] * energy["over"]
    penalty += problem["map_weight"] * map_violation
    geometry_ok = path["clearance"] is None or path["clearance"] >= -0.000000001
    energy_ok = energy["total"] <= problem["budget"] + 0.0000001
    valid = box_ok and geometry_ok and energy_ok
    result = {"score": base_score + penalty, "base_score": base_score,
              "penalty": penalty, "valid": valid, "box_ok": box_ok,
              "geometry_ok": geometry_ok, "energy_ok": energy_ok,
              "map_violation": map_violation, "beacons": beacons, "points": points,
              "through_gate": valid and crosses_gate(points, problem)}
    result.update(path)
    result.update(energy)
    result.update(signal)
    return result


def evaluate_benchmark(whale, problem):
    # whale đã ở miền thật [-100,100] hay [-5.12,5.12]. Đọc thẳng nhé.
    score = 0
    if problem["function"] == "quadratic":
        score = (whale[0] - 7) * (whale[0] - 7)
    elif problem["function"] == "sphere":
        for value in whale:
            score += value * value
    else:
        for value in whale:
            score += value * value - 10 * math.cos(2 * math.pi * value) + 10
    return {"score": score, "base_score": score, "valid": True, "values": whale.copy()}
