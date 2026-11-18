"""
Kiểm thử tự động cho các hàm xử lý dữ liệu và thuật toán WOA.
"""

import unittest
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from n4_hoang_yen_du_lieu import (
    load_problem,
    get_bounds,
    validate_solution_vector,
    clip_to_bounds,
    decode_solution,
    get_a_value,
    get_a2_author,
    NUM_VARIABLES,
    NUM_WAYPOINTS,
    BATTERY_MAX
)


class TestDelivery(unittest.TestCase):

    def test_01_json_problems(self):
        """Kiểm tra cả 3 ca A, B, C đúng nhãn, pin 220, 8 trại và khe hẹp ở B."""
        for case in ["A", "B", "C"]:
            prob = load_problem(case)
            self.assertEqual(prob["battery_max"], 220.0, f"Ca {case} phải có pin đúng 220.0")
            self.assertEqual(len(prob["camps"]), 8, f"Ca {case} phải có đúng 8 trại cứu trợ")
            self.assertTrue(len(prob["storms"]) > 0, f"Ca {case} phải có danh sách bão")
            if case == "B":
                self.assertIsNotNone(prob.get("narrow_gate"), "Ca B bắt buộc phải có cổng khe narrow_gate")
                self.assertIn("center", prob["narrow_gate"])
                self.assertIn("width", prob["narrow_gate"])

    def test_02_bounds_and_clipping(self):
        """Kiểm tra giới hạn biến [0, 100] cho x/y, [0, 25] cho pin và hàm sửa biên."""
        lb, ub = get_bounds(30)
        self.assertEqual(len(lb), 30)
        self.assertEqual(len(ub), 30)
        for i in range(10):
            self.assertEqual(lb[3 * i], 0.0)
            self.assertEqual(ub[3 * i], 100.0)
            self.assertEqual(lb[3 * i + 1], 0.0)
            self.assertEqual(ub[3 * i + 1], 100.0)
            self.assertEqual(lb[3 * i + 2], 0.0)
            self.assertEqual(ub[3 * i + 2], 25.0)

        # Kiểm tra clip
        out_vec = [-50.0, 150.0, 99.0] * 10
        clipped = clip_to_bounds(out_vec)
        for i in range(10):
            self.assertEqual(clipped[3 * i], 0.0)
            self.assertEqual(clipped[3 * i + 1], 100.0)
            self.assertEqual(clipped[3 * i + 2], 25.0)

    def test_03_decode_top_k_and_tie_breaking(self):
        """
        Kiểm tra giải mã Top-K (K=6, 8, 10):
        - 10 điểm giữ nguyên.
        - Tắt đèn ngoài top-K (pin = 0).
        - Hòa pin ưu tiên chỉ số nhỏ hơn.
        """
        vec = [
            10, 10, 5.0,    # Điểm 0: pin = 5.0
            20, 20, 20.0,   # Điểm 1: pin = 20.0 (hòa với điểm 3)
            30, 30, 10.0,   # Điểm 2: pin = 10.0
            40, 40, 20.0,   # Điểm 3: pin = 20.0 (hòa với điểm 1, nhưng chỉ số 3 > 1)
            50, 50, 15.0,   # Điểm 4: pin = 15.0 (hòa với điểm 7)
            60, 60, 8.0,    # Điểm 5: pin = 8.0
            70, 70, 25.0,   # Điểm 6: pin = 25.0 (lớn nhất)
            80, 80, 15.0,   # Điểm 7: pin = 15.0 (hòa với điểm 4, nhưng chỉ số 7 > 4)
            90, 90, 2.0,    # Điểm 8: pin = 2.0
            95, 95, 12.0    # Điểm 9: pin = 12.0
        ]
        # Xếp hạng giảm dần pin kèm ưu tiên chỉ số:
        # Top-6 gồm [6, 1, 3, 4, 7, 9]. Tắt [0, 2, 5, 8]
        dec6 = decode_solution(vec, K=6)
        self.assertEqual(len(dec6.waypoints), 10, "10 điểm tọa độ luôn được giữ nguyên")
        self.assertEqual(len(dec6.full_path), 12, "Đường bay đủ 12 điểm [Start, 10 wp, Goal]")
        self.assertEqual(dec6.active_light_indices, [1, 3, 4, 6, 7, 9])
        self.assertEqual(dec6.disabled_light_indices, [0, 2, 5, 8])

        for idx in [0, 2, 5, 8]:
            self.assertEqual(dec6.light_powers[idx], 0.0)

        dec8 = decode_solution(vec, K=8)
        self.assertEqual(dec8.disabled_light_indices, [0, 8])
        self.assertEqual(dec8.light_powers[0], 0.0)
        self.assertEqual(dec8.light_powers[8], 0.0)

        dec10 = decode_solution(vec, K=10)
        self.assertEqual(len(dec10.disabled_light_indices), 0)

    def test_04_a_schedules_and_a2_isolation(self):
        """Kiểm tra 3 lịch a tại đầu, giữa, cuối và tính độc lập của a2."""
        T = 600
        self.assertAlmostEqual(get_a_value(0, T, "linear"), 2.0)
        self.assertAlmostEqual(get_a_value(0, T, "cosine"), 2.0)
        self.assertAlmostEqual(get_a_value(0, T, "quadratic"), 2.0)
        self.assertAlmostEqual(get_a2_author(0, T), -1.0)

        self.assertAlmostEqual(get_a_value(300, T, "linear"), 1.0)
        self.assertAlmostEqual(get_a_value(300, T, "cosine"), 1.0)
        self.assertAlmostEqual(get_a_value(300, T, "quadratic"), 0.5)
        self.assertAlmostEqual(get_a2_author(300, T), -1.5)

        self.assertAlmostEqual(get_a_value(600, T, "linear"), 0.0)
        self.assertAlmostEqual(get_a_value(600, T, "cosine"), 0.0)
        self.assertAlmostEqual(get_a_value(600, T, "quadratic"), 0.0)
        self.assertAlmostEqual(get_a2_author(600, T), -2.0)


if __name__ == "__main__":
    unittest.main()
