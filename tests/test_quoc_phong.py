"""
tests/test_quoc_phong.py - Kiểm thử tự động cho Module N2: Quốc Phong
Dự án: Nhóm 4 - Whale Optimization Algorithm (WOA) - Bài toán Đom Đóm
"""

import unittest
import math
import os
import sys

# Đảm bảo import được từ thư mục gốc và thư mục src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.n2_quoc_phong_nang_luong import (
    calculate_flight_energy,
    calculate_lamp_energy,
    energy_metrics,
    signal_from_single_beacon,
    saturation_utility,
    camp_detailed_breakdown,
    signal_metrics,
    DEFAULT_BATTERY_BUDGET,
    DEFAULT_FLIGHT_COST_RATE,
    DEFAULT_SIGNAL_SCALE_DIST,
    DEFAULT_UTILITY_ALPHA,
)
from src.n4_hoang_yen_du_lieu import load_problem


class TestQuocPhongEnergyAndUtility(unittest.TestCase):

    def setUp(self):
        self.problem_A = load_problem("A")
        self.problem_B = load_problem("B")
        self.problem_C = load_problem("C")

    def test_01_flight_and_lamp_energy(self):
        """Kiểm tra pin bay = 0.45 * L và tổng pin đèn từ các đèn thật sự bật."""
        # L = 150 -> flight = 67.5
        flight_e = calculate_flight_energy(150.0, flight_cost=0.45)
        self.assertAlmostEqual(flight_e, 67.5, places=5)

        # 10 đèn với mức pin khác nhau, một số đèn bị tắt (active = False hoặc pin = 0)
        beacons = [
            {"x": 10, "y": 20, "energy": 12.0, "active": True},
            {"x": 20, "y": 30, "energy": 15.0, "active": True},
            {"x": 30, "y": 40, "energy": 25.0, "active": False},  # Đèn tắt, không tính
            {"x": 40, "y": 50, "energy": 0.0,  "active": True},   # Pin = 0
            {"x": 50, "y": 60, "energy": 18.0, "active": True},
        ]
        lamp_e = calculate_lamp_energy(beacons)
        # Kỳ vọng: 12 + 15 + 0 + 0 + 18 = 45.0
        self.assertAlmostEqual(lamp_e, 45.0, places=5)

    def test_02_battery_budget_and_over_normalization(self):
        """
        Kiểm tra ngân sách pin 220:
        - Đúng công thức over = max(0, total - 220) / 220.
        - KHÔNG tự ý cắt bớt pin cho vừa 220.
        """
        # Trường hợp 1: Không vượt pin (L = 100, pin đèn = 100 -> tổng 145 <= 220)
        beacons_ok = [{"x": 10 * i, "y": 50, "energy": 10.0, "active": True} for i in range(10)]
        res_ok = energy_metrics(length=100.0, beacons=beacons_ok)
        self.assertAlmostEqual(res_ok["flight"], 45.0, places=5)
        self.assertAlmostEqual(res_ok["lamps"], 100.0, places=5)
        self.assertAlmostEqual(res_ok["total"], 145.0, places=5)
        self.assertAlmostEqual(res_ok["over"], 0.0, places=7)
        self.assertTrue(res_ok["energy_ok"])

        # Trường hợp 2: Vượt pin (Ví dụ Trang 12: Tổng 230 -> vượt 10 -> over = 10 / 220)
        beacons_heavy = [{"x": 10 * i, "y": 50, "energy": 14.0, "active": True} for i in range(10)]
        res_heavy = energy_metrics(length=200.0, beacons=beacons_heavy)
        # L = 200 -> flight = 90; lamps = 140 -> total = 230
        self.assertAlmostEqual(res_heavy["flight"], 90.0, places=5)
        self.assertAlmostEqual(res_heavy["lamps"], 140.0, places=5)
        self.assertAlmostEqual(res_heavy["total"], 230.0, places=5)
        self.assertAlmostEqual(res_heavy["excess"], 10.0, places=5)
        self.assertAlmostEqual(res_heavy["over"], 10.0 / 220.0, places=6)
        self.assertFalse(res_heavy["energy_ok"])
        # Đảm bảo tổng pin vẫn giữ nguyên 230.0, không bị gọt về 220.0
        self.assertEqual(res_heavy["total"], 230.0)

    def test_03_signal_attenuation_by_distance(self):
        """
        Kiểm tra tín hiệu suy giảm theo khoảng cách: I = e / (1 + d^2 / 18^2).
        Đối chiếu ví dụ Trang 10: Đèn pin 20: d=0 -> 20; d=18 -> 10; d=36 -> 4.
        """
        camp = (50.0, 50.0)
        # d = 0
        i0 = signal_from_single_beacon((50.0, 50.0), 20.0, camp, signal_range=18.0)
        self.assertAlmostEqual(i0, 20.0, places=5)

        # d = 18
        i18 = signal_from_single_beacon((50.0 + 18.0, 50.0), 20.0, camp, signal_range=18.0)
        self.assertAlmostEqual(i18, 10.0, places=5)

        # d = 36
        i36 = signal_from_single_beacon((50.0, 50.0 + 36.0), 20.0, camp, signal_range=18.0)
        self.assertAlmostEqual(i36, 4.0, places=5)

        # Đèn tắt (energy = 0) thì dù ở ngay trên trại cũng cho tín hiệu = 0
        i_off = signal_from_single_beacon((50.0, 50.0), 0.0, camp, signal_range=18.0)
        self.assertEqual(i_off, 0.0)

    def test_04_saturation_utility_properties(self):
        """
        Kiểm tra hàm hữu dụng bão hòa u = 1 - exp(-0.1 * I):
        - Bảng giá trị chuẩn Trang 10 tài liệu.
        - Tính đơn điệu tăng và tính chất lợi ích biên giảm dần.
        """
        # Bảng Trang 10
        test_cases = [
            (0.0, 0.0),
            (5.0, 0.3935),
            (10.0, 0.6321),
            (20.0, 0.8647),
            (40.0, 0.9817),
        ]
        for val_i, exp_u in test_cases:
            u_calc = saturation_utility(val_i, alpha=0.1)
            self.assertAlmostEqual(u_calc, exp_u, places=3)

        # Kiểm tra tính chất lợi ích biên giảm dần (concave curve)
        u0 = saturation_utility(0.0)
        u10 = saturation_utility(10.0)
        u20 = saturation_utility(20.0)
        u30 = saturation_utility(30.0)
        gain_1 = u10 - u0
        gain_2 = u20 - u10
        gain_3 = u30 - u20
        self.assertTrue(gain_1 > gain_2 > gain_3, "Lợi ích tăng thêm phải nhỏ dần khi tín hiệu tăng")

    def test_05_camp_breakdown_and_weakest_camp(self):
        """
        Kiểm tra đọc chi tiết 8 trại:
        - Tính đúng tín hiệu và hữu dụng từng trại.
        - Tìm đúng trại có u_min (trại yếu nhất / đói tín hiệu nhất).
        - Gộp đúng U có trọng số.
        """
        # Đặt 3 đèn ở góc tây nam (gần C1, C2, C3)
        beacons = [
            {"x": 15, "y": 70, "energy": 20.0, "active": True},
            {"x": 22, "y": 25, "energy": 20.0, "active": True},
            {"x": 40, "y": 30, "energy": 20.0, "active": True},
        ]
        breakdown = camp_detailed_breakdown(beacons, problem=self.problem_A)
        self.assertEqual(len(breakdown), 8, "Phải có đúng 8 trại được phân tích")

        # C8 ở (90, 22) rất xa 3 đèn này nên phải nhận ít tín hiệu nhất
        c8_info = next(c for c in breakdown if c["name"] == "C8")
        c2_info = next(c for c in breakdown if c["name"] == "C2")
        self.assertTrue(c2_info["utility"] > c8_info["utility"])

        # Kiểm tra signal_metrics
        s_res = signal_metrics(beacons, problem=self.problem_A)
        self.assertIn("utility_sat", s_res)
        self.assertIn("minimum_service", s_res)
        self.assertEqual(len(s_res["levels"]), 8)
        self.assertEqual(len(s_res["satisfaction"]), 8)
        self.assertEqual(s_res["weakest_camp_name"], "C8")
        self.assertEqual(s_res["minimum_service"], c8_info["utility"])

    def test_06_active_beacons_count(self):
        """Kiểm tra đếm số đèn phát đáng kể (> 0.001)."""
        beacons = [
            {"x": 10, "y": 10, "energy": 15.0, "active": True},
            {"x": 20, "y": 20, "energy": 0.0005, "active": True}, # Quá nhỏ
            {"x": 30, "y": 30, "energy": 10.0, "active": False}, # Tắt
            {"x": 40, "y": 40, "energy": 20.0, "active": True},
        ]
        res = energy_metrics(100.0, beacons)
        # Chỉ có beacon 0 và beacon 3 là active và > 0.001
        self.assertEqual(res["active_beacons_count"], 2)

    def test_07_full_compatibility_with_n3_khang_interface(self):
        """
        Kiểm tra sự tích hợp liền mạch với Phúc Khang (N3):
        n3_phuc_khang_danh_gia.py yêu cầu các trường:
        - energy: total, over, flight, lamps
        - signal: utility_sat, minimum_service
        """
        beacons = [{"x": 10 * i, "y": 50, "energy": 15.0, "active": True} for i in range(10)]
        e_dict = energy_metrics(120.0, beacons, self.problem_A)
        s_dict = signal_metrics(beacons, self.problem_A)

        self.assertIn("total", e_dict)
        self.assertIn("over", e_dict)
        self.assertIn("flight", e_dict)
        self.assertIn("lamps", e_dict)

        self.assertIn("utility_sat", s_dict)
        self.assertIn("minimum_service", s_dict)

        # Tính điểm mục tiêu base_score và phạt đúng như Khang (N3)
        base_score = -s_dict["utility_sat"] + 0.12 * 120.0 / 100.0
        battery_penalty = 30.0 * (e_dict["over"] ** 2)
        self.assertTrue(math.isfinite(base_score))
        self.assertTrue(math.isfinite(battery_penalty))


if __name__ == "__main__":
    unittest.main()
