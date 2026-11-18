"""Chấm lại bộ đã kèm và kiểm hình học bằng cách khác: python kiem_tra_ket_qua.py"""
import json
import math
from src.n4_hoang_yen_du_lieu import ROOT, bounds
from src.n3_phuc_khang_danh_gia import evaluate, evaluate_benchmark
from src.n8_trang_bui_thong_ke import load_runs


def circle_check(points, storms, safety):
    # Tìm khoảng t của đoạn a+t*(b-a) nằm trong vòng tròn bằng phương
    # trình bậc hai. Khác cách chiếu tâm xuống đoạn trong n1.
    for i in range(len(points) - 1):
        ax, ay = points[i]
        bx, by = points[i + 1]
        dx = bx - ax
        dy = by - ay
        A = dx * dx + dy * dy
        for storm in storms:
            px = ax - storm["x"]
            py = ay - storm["y"]
            radius = storm["r"] + safety - 0.00000001
            C = px * px + py * py - radius * radius
            assert C >= -0.000001
            if A < 0.000000000000000001:
                continue
            B = 2 * (px * dx + py * dy)
            discriminant = B * B - 4 * A * C
            if discriminant > 0.0000001:
                left = (-B - math.sqrt(discriminant)) / (2 * A)
                right = (-B + math.sqrt(discriminant)) / (2 * A)
                assert min(1, right) - max(0, left) < 0.0000001


def main():
    runs = load_runs(ROOT / "results")
    assert len(runs) == 330
    groups = {}
    valid_count = 0
    for result in runs:
        name = result["experiment"]["id"]
        if name not in groups:
            groups[name] = []
        groups[name].append(result["settings"]["seed"])
        assert result["evaluations"] == 24000
        assert result["problem"]["budget"] == 220
        lower, upper = bounds(result["problem"])
        for whale in result["final_population"]:
            assert len(whale) == 30
            for j in range(30):
                assert lower[j] <= whale[j] <= upper[j]
            score = evaluate(whale, result["problem"])["score"]
            assert result["best_overall"]["evaluation"]["score"] <= score + 0.000000001
        for key in ["best_overall", "best_valid", "best_gate"]:
            item = result[key]
            if item is None:
                continue
            fresh = evaluate(item["position"], result["problem"])
            for metric in ["score", "base_score", "utility_sat", "total", "length"]:
                assert math.isclose(fresh[metric], item["evaluation"][metric], abs_tol=0.000000001)
            assert fresh["valid"] == item["evaluation"]["valid"]
            if key in ["best_valid", "best_gate"]:
                assert fresh["valid"]
                circle_check(fresh["points"], result["problem"]["storms"], result["problem"]["safety"])
            if key == "best_gate":
                assert fresh["through_gate"]
        if result["best_valid"] is not None:
            valid_count += 1
    assert len(groups) == 11
    for name in groups:
        assert sorted(groups[name]) == list(range(1, 31))
    benchmark_count = 0
    for path in (ROOT / "results" / "benchmarks").glob("*/seed_*.json"):
        result = json.loads(path.read_text())
        fresh = evaluate_benchmark(result["best_overall"]["position"], result["problem"])
        assert math.isclose(fresh["score"], result["best_overall"]["evaluation"]["score"], abs_tol=0.000000001)
        assert fresh["score"] <= result["problem"]["target"]
        assert result["evaluations"] == 15000
        benchmark_count += 1
    assert benchmark_count == 90
    print("Đã kiểm 330 lượt ứng dụng;", valid_count, "lượt có best_valid; các đường qua kiểm hình học độc lập.")
    print("Đàn cuối là 30 mảng 30 biến trong miền; 90 benchmark đạt ngưỡng; số lượt chấm đúng.")


if __name__ == "__main__":
    main()
