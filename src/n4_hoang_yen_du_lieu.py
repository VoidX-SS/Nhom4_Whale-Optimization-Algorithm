"""Hoàng Yến: đề bài, 30 ô số và ba lịch giảm a.

Mình giữ 10 điểm trung gian. Mỗi điểm có x, y, pin, thành 30 biến.
Ngách số đèn chỉ đổi số thiết bị được bật, không đổi số ô trên tờ giấy.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_problem(name="co_ban"):
    with open(ROOT / "data" / (name + ".json"), encoding="utf-8") as file:
        return json.load(file)


def default_settings():
    return {"population": 30, "iterations": 800, "seed": 7,
            "a_mode": "linear", "l_mode": "shared_l", "boundary": "clip",
            "b": 1.0, "snapshot_every": 10}


def bounds(problem):
    # Benchmark dùng miền GỐC, có thể có số âm. Không dời đáy về 0.5.
    if "dimensions" in problem:
        lower = [problem["lower"]] * problem["dimensions"]
        upper = [problem["upper"]] * problem["dimensions"]
        return lower, upper
    lower = []
    upper = []
    for k in range(10):
        lower.extend([0, 0, 0])
        upper.extend([100, 100, problem["beacon_max"]])
    return lower, upper


def decode(whale, problem):
    beacons = []
    for k in range(10):
        i = 3 * k
        beacons.append({"x": whale[i], "y": whale[i + 1],
                        "energy": whale[i + 2], "active": False})
    if problem["active_lights"] == 10:
        for beacon in beacons:
            beacon["active"] = True
        return beacons
    # Chọn tối đa K đèn có mức pin đề xuất lớn nhất. Viết vòng for
    # thay vì mẹo sắp xếp để mình dễ lần theo từng lần chọn nhé.
    for pick in range(problem["active_lights"]):
        chosen = -1
        for k in range(10):
            if not beacons[k]["active"]:
                if chosen == -1 or beacons[k]["energy"] > beacons[chosen]["energy"]:
                    chosen = k
        beacons[chosen]["active"] = True
    for beacon in beacons:
        if not beacon["active"]:
            beacon["energy"] = 0
    return beacons


def a_value(t, total, mode):
    # Mẫu số total giữ đúng WOA.m của tác giả: vòng cuối gần 0,
    # không ép bằng 0 như bản cũ. t bắt đầu từ 0.
    progress = t / total
    if mode == "linear":
        return 2 - 2 * progress
    if mode == "cosine":
        return 1 + math.cos(math.pi * progress)
    if mode == "quadratic":
        return 2 * (1 - progress) * (1 - progress)
    raise ValueError("Chọn linear, cosine hoặc quadratic nhé.")


def validate_inputs(problem, settings):
    if settings["population"] < 2 or settings["iterations"] < 2:
        raise ValueError("Mình cần ít nhất 2 cá voi và 2 lượt chấm đàn.")
    if settings["a_mode"] not in ["linear", "cosine", "quadratic"]:
        raise ValueError("Kiểu a chưa đúng.")
    if settings["l_mode"] not in ["shared_l", "independent_l"]:
        raise ValueError("Kiểu l chưa đúng.")
    if settings["boundary"] not in ["clip", "reinit"]:
        raise ValueError("Chọn clip hoặc reinit nhé.")
    if settings["snapshot_every"] < 1:
        raise ValueError("Khoảng lưu khung phải từ 1 trở lên.")
    if "dimensions" not in problem:
        if problem["slots"] != 10 or problem["budget"] != 220:
            raise ValueError("Bản nhóm chốt 10 điểm, 30 biến và 220 pin.")
        if not 1 <= problem["active_lights"] <= 10:
            raise ValueError("Số đèn hoạt động cần nằm trong 1..10.")
        for storm in problem["storms"]:
            if storm["r"] <= 0:
                raise ValueError("Bán kính bão phải dương.")
