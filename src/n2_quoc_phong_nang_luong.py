"""Quốc Phong: tiền pin được chia cho việc bay và cho các đèn.

Một trại đang rất thiếu tín hiệu sẽ quý một ít pin thêm hơn một trại
đã sáng rực. Hàm bão hòa kể lại ý đó: vẫn tăng, nhưng tăng chậm dần.
"""

import math


def energy_metrics(length, beacons, problem):
    flight = problem["flight_cost"] * length
    lamps = 0
    for beacon in beacons:
        lamps += beacon["energy"]
    total = flight + lamps
    over = max(0, total - problem["budget"]) / problem["budget"]
    return {"flight": flight, "lamps": lamps, "total": total, "over": over}


def signal_metrics(beacons, problem):
    levels = []
    satisfaction = []
    weighted_sat = 0
    weight_sum = 0
    range_squared = problem["signal_range"] * problem["signal_range"]

    for camp in problem["camps"]:
        level = 0
        for beacon in beacons:
            dx = beacon["x"] - camp["x"]
            dy = beacon["y"] - camp["y"]
            level += beacon["energy"] / (1 + (dx * dx + dy * dy) / range_squared)
        linear = problem["alpha"] * level
        sat = 1 - math.exp(-linear)
        levels.append(level)
        satisfaction.append(sat)
        weighted_sat += camp["weight"] * sat
        weight_sum += camp["weight"]

    utility_sat = weighted_sat / weight_sum
    return {
        "levels": levels,
        "satisfaction": satisfaction,
        "utility_sat": utility_sat,
        "minimum_service": min(satisfaction),
    }
