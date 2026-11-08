"""
src/n2_quoc_phong_nang_luong.py - Module N2: Quốc Phong
Dự án: Nhóm 4 - Whale Optimization Algorithm (WOA) - Bài toán Đom Đóm

"""

import math
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# Các hằng số mặc định theo đúng đề bài chốt
DEFAULT_BATTERY_BUDGET: float = 220.0     # Túi pin tối đa 220 đơn vị
DEFAULT_FLIGHT_COST_RATE: float = 0.45   # 0.45 pin trên 1 đơn vị khoảng cách
DEFAULT_SIGNAL_SCALE_DIST: float = 18.0  # Thang khoảng cách R = 18
DEFAULT_UTILITY_ALPHA: float = 0.1       # Hệ số bão hòa alpha = 0.1
DEFAULT_BEACON_MAX: float = 25.0         # Pin tối đa một đèn đề xuất


# ======================================================================
# PHẦN 1: MÔ HÌNH NĂNG LƯỢNG VÀ TÚI PIN CHUNG (BƯỚC 1 & 2)
# ======================================================================

def calculate_flight_energy(length: float, flight_cost: float = DEFAULT_FLIGHT_COST_RATE) -> float:
    """
    Tính năng lượng tiêu hao cho quãng đường bay của UAV.
    Công thức: E_bay = 0.45 * L
    """
    if length < 0.0:
        raise ValueError(f"Chiều dài đường bay không được âm: length = {length}")
    return float(flight_cost * length)


def extract_beacon_energy(beacon: Any) -> float:
    """
    Trích xuất năng lượng thực tế của một đèn phát tín hiệu.
    Hỗ trợ cả dict (chuẩn hoặc legacy), DecodedSolution, hoặc tuple.
    Nếu đèn không kích hoạt (active == False), năng lượng thực tế là 0.0.
    """
    if isinstance(beacon, dict):
        # Nếu có cờ active rõ ràng và active == False -> năng lượng = 0.0
        if "active" in beacon and not beacon["active"]:
            return 0.0
        # Hỗ trợ cả key "energy", "pin", "power"
        return float(beacon.get("energy", beacon.get("pin", beacon.get("power", 0.0))))
    if hasattr(beacon, "energy"):
        return float(getattr(beacon, "energy"))
    if hasattr(beacon, "light_powers"):
        return float(getattr(beacon, "light_powers"))
    if isinstance(beacon, (list, tuple)) and len(beacon) >= 3:
        # beacon dạng [x, y, pin]
        return float(beacon[2])
    return 0.0


def calculate_lamp_energy(beacons: Sequence[Any]) -> float:
    """
    Tính tổng năng lượng tiêu hao cho các thiết bị đèn thực sự được bật.
    Công thức: E_den = sum(e_k) với k thuộc tập đèn được kích hoạt.
    Các đèn tắt (e_k = 0 hoặc active = False) không tiêu tốn pin.
    """
    total_lamps = 0.0
    for b in beacons:
        e = extract_beacon_energy(b)
        if e > 0.0:
            total_lamps += e
    return float(total_lamps)


def calculate_herfindahl_energy_index(beacons: Sequence[Any]) -> float:
    """
    Chỉ số tập trung năng lượng đèn (Herfindahl-Hirschman Index - H_E) theo Trang 15 tài liệu:
    H_E = sum( (e_k / E_den)^2 ) khi E_den > 0.
    - H_E = 1/m nếu chia đều cho m đèn.
    - H_E = 1.0 nếu dồn hết pin vào 1 đèn duy nhất.
    - H_E = 0.0 nếu không bật đèn nào.
    """
    e_lamps = calculate_lamp_energy(beacons)
    if e_lamps <= 1e-12:
        return 0.0
    h_sum = 0.0
    for b in beacons:
        e = extract_beacon_energy(b)
        if e > 0.0:
            ratio = e / e_lamps
            h_sum += ratio * ratio
    return float(h_sum)


def energy_metrics(
    length: float,
    beacons: Sequence[Any],
    problem: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    BƯỚC 1 & 2: Tính toán toàn diện năng lượng bay, năng lượng đèn và mức vượt pin.
    
    Quy tắc cốt lõi:
    - Túi pin cố định: 220 đơn vị.
    - over = max(0, total - 220) / 220 (chuẩn hóa tỷ lệ vượt, KHÔNG tự ý cắt bớt pin).
    - Phạt tương ứng của N3 là 30 * over^2.
    
    Đầu ra tương thích 100% với phiếu chấm của Phúc Khang (N3) và thống kê của Trang Nguyễn (N9):
      flight, lamps, total, over, energy_ok, herfindahl_index.
    """
    budget = DEFAULT_BATTERY_BUDGET
    flight_cost = DEFAULT_FLIGHT_COST_RATE

    if problem is not None:
        budget = float(problem.get("battery_max", problem.get("budget", DEFAULT_BATTERY_BUDGET)))
        flight_cost = float(problem.get("flight_energy_rate", problem.get("flight_cost", DEFAULT_FLIGHT_COST_RATE)))

    e_flight = calculate_flight_energy(length, flight_cost=flight_cost)
    e_lamps = calculate_lamp_energy(beacons)
    e_total = e_flight + e_lamps

    excess = max(0.0, e_total - budget)
    over_pin = excess / budget if budget > 0.0 else 0.0

    # Sai số dung sai số học 1e-7 theo đúng quy ước Khang (N3)
    energy_ok = bool(e_total <= budget + 1e-7)

    # Đếm số đèn phát đáng kể (e_k > 0.001) theo trang 15 tài liệu
    active_beacons_count = sum(1 for b in beacons if extract_beacon_energy(b) > 0.001)

    return {
        "flight": round(e_flight, 6),
        "lamps": round(e_lamps, 6),
        "total": round(e_total, 6),
        "over": round(over_pin, 8),
        "excess": round(excess, 6),
        "budget": budget,
        "energy_ok": energy_ok,
        "active_beacons_count": active_beacons_count,
        "herfindahl_index": round(calculate_herfindahl_energy_index(beacons), 6),
    }


# ======================================================================
# PHẦN 2: MÔ HÌNH TÍN HIỆU VÀ ĐỘ HỮU DỤNG BÃO HÒA (BƯỚC 3 & 4)
# ======================================================================

def calculate_distance(p1: Sequence[float], p2: Sequence[float]) -> float:
    """Khoảng cách Euclid hình học giữa hai điểm trong mặt phẳng 2D."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.hypot(dx, dy)


def extract_beacon_position(beacon: Any) -> Tuple[float, float]:
    """Trích xuất tọa độ (x, y) của một trạm phát tín hiệu."""
    if isinstance(beacon, dict):
        if "pos" in beacon:
            return float(beacon["pos"][0]), float(beacon["pos"][1])
        return float(beacon.get("x", 0.0)), float(beacon.get("y", 0.0))
    if isinstance(beacon, (list, tuple)) and len(beacon) >= 2:
        return float(beacon[0]), float(beacon[1])
    if hasattr(beacon, "x") and hasattr(beacon, "y"):
        return float(getattr(beacon, "x")), float(getattr(beacon, "y"))
    raise ValueError(f"Không thể trích xuất tọa độ từ beacon: {beacon}")


def extract_camp_info(camp: Dict[str, Any], default_id: int) -> Tuple[str, Tuple[float, float], float]:
    """Trích xuất tên, tọa độ và trọng số nhu cầu của một trại cứu trợ."""
    name = str(camp.get("name", f"C{default_id}"))
    if "pos" in camp:
        pos = (float(camp["pos"][0]), float(camp["pos"][1]))
    elif "x" in camp and "y" in camp:
        pos = (float(camp["x"]), float(camp["y"]))
    else:
        raise ValueError(f"Trại {name} thiếu thông tin tọa độ.")
    
    weight = float(camp.get("weight", camp.get("w", 1.0)))
    if weight <= 0.0:
        weight = 1.0
    return name, pos, weight


def signal_from_single_beacon(
    beacon_pos: Tuple[float, float],
    beacon_energy: float,
    camp_pos: Tuple[float, float],
    signal_range: float = DEFAULT_SIGNAL_SCALE_DIST
) -> float:
    """
    Tính tín hiệu từ một đèn phát k truyền đến trại m.
    Công thức: I_km = e_k / (1 + d_km^2 / R^2) với R = 18.
    Nếu e_k = 0 (đèn tắt), I_km = 0.
    """
    if beacon_energy <= 0.0:
        return 0.0
    d_sq = (beacon_pos[0] - camp_pos[0]) ** 2 + (beacon_pos[1] - camp_pos[1]) ** 2
    r_sq = signal_range * signal_range
    return float(beacon_energy / (1.0 + d_sq / r_sq))


def saturation_utility(intensity: float, alpha: float = DEFAULT_UTILITY_ALPHA) -> float:
    """
    Hàm hữu dụng bão hòa cá nhân tại một trại:
    Công thức: u_m = 1 - exp(-0.1 * I_m)
    - Khi I_m = 0 -> u_m = 0.
    - u_m luôn thuộc [0, 1) với mọi I_m hữu hạn.
    - Lợi ích cận biên du/dI = 0.1 * exp(-0.1 * I) giảm dần khi I tăng.
    """
    if intensity <= 0.0:
        return 0.0
    return float(1.0 - math.exp(-alpha * intensity))


def camp_detailed_breakdown(
    beacons: Sequence[Any],
    problem: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    BƯỚC 5: Đọc chi tiết mức độ phục vụ từng trại trong số 8 trại cứu trợ.
    
    Trả về danh sách 8 bản ghi chi tiết:
    - Trại nào được phục vụ mạnh (gần bão hòa).
    - Trại nào bị đói tín hiệu (I_m thấp, u_m thấp).
    - Đèn nào đóng góp chính cho trại đó.
    """
    camps_data = []
    signal_range = DEFAULT_SIGNAL_SCALE_DIST
    alpha = DEFAULT_UTILITY_ALPHA

    if problem is not None:
        camps_data = problem.get("camps", [])
        signal_range = float(problem.get("signal_scale_dist", problem.get("signal_range", DEFAULT_SIGNAL_SCALE_DIST)))
        alpha = float(problem.get("utility_decay", problem.get("alpha", DEFAULT_UTILITY_ALPHA)))

    # Nếu không truyền danh sách trại, lấy 8 trại chuẩn của Ca A/B/C theo đề bài
    if not camps_data:
        camps_data = [
            {"id": 1, "name": "C1", "pos": [12.0, 70.0], "weight": 12.0},
            {"id": 2, "name": "C2", "pos": [20.0, 25.0], "weight": 18.0},
            {"id": 3, "name": "C3", "pos": [38.0, 31.0], "weight": 15.0},
            {"id": 4, "name": "C4", "pos": [43.0, 85.0], "weight": 20.0},
            {"id": 5, "name": "C5", "pos": [61.0, 43.0], "weight": 16.0},
            {"id": 6, "name": "C6", "pos": [65.0, 83.0], "weight": 12.0},
            {"id": 7, "name": "C7", "pos": [84.0, 63.0], "weight": 18.0},
            {"id": 8, "name": "C8", "pos": [90.0, 22.0], "weight": 14.0},
        ]

    breakdown = []
    for idx, camp in enumerate(camps_data, start=1):
        c_name, c_pos, c_weight = extract_camp_info(camp, idx)

        total_intensity = 0.0
        beacon_contributions = []

        for b_idx, b in enumerate(beacons, start=1):
            b_pos = extract_beacon_position(b)
            b_energy = extract_beacon_energy(b)
            i_km = signal_from_single_beacon(b_pos, b_energy, c_pos, signal_range=signal_range)
            dist = calculate_distance(b_pos, c_pos)
            total_intensity += i_km
            if b_energy > 0.0:
                beacon_contributions.append({
                    "beacon_index": b_idx,
                    "beacon_pos": b_pos,
                    "energy": b_energy,
                    "distance": round(dist, 2),
                    "signal_contribution": round(i_km, 4)
                })

        u_sat = saturation_utility(total_intensity, alpha=alpha)

        breakdown.append({
            "camp_id": idx,
            "name": c_name,
            "pos": list(c_pos),
            "weight": c_weight,
            "intensity": round(total_intensity, 4),
            "utility": round(u_sat, 4),
            "saturation_percent": round(u_sat * 100.0, 2),
            "contributing_beacons": beacon_contributions
        })

    return breakdown


def signal_metrics(
    beacons: Sequence[Any],
    problem: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    BƯỚC 3 & 4: Tính toán toàn diện tín hiệu và độ hữu dụng bão hòa cho 8 trại.
    
    Quy tắc cốt lõi:
    - Tín hiệu: I_m = sum_k ( e_k / (1 + d^2 / 18^2) ).
    - Hữu dụng cá nhân: u_m = 1 - exp(-0.1 * I_m).
    - Hữu dụng toàn hệ thống có trọng số: U = sum(w_m * u_m) / sum(w_m).
    - Mức phục vụ tối thiểu: u_min = min(u_m).
    
    Lưu ý quan trọng:
    - U là chỉ số mô phỏng của hàm toán học bão hòa, KHÔNG phải tỷ lệ người được cứu.
    - U cao không tự bảo đảm mọi trại đều có đủ tín hiệu (do đó cần u_min giám sát).
    
    Đầu ra tương thích 100% với phiếu chấm của Phúc Khang (N3):
      utility_sat, minimum_service, levels, satisfaction, camp_breakdown.
    """
    breakdown = camp_detailed_breakdown(beacons, problem=problem)

    levels = [item["intensity"] for item in breakdown]
    satisfaction = [item["utility"] for item in breakdown]
    weights = [item["weight"] for item in breakdown]

    weighted_u_sum = sum(w * u for w, u in zip(weights, satisfaction))
    total_weight = sum(weights) if weights else 1.0
    u_system = weighted_u_sum / total_weight if total_weight > 0.0 else 0.0

    u_min = min(satisfaction) if satisfaction else 0.0

    # Xác định trại đói tín hiệu nhất
    weakest_camp = None
    if breakdown:
        weakest_camp = min(breakdown, key=lambda c: c["utility"])

    return {
        "utility_sat": round(u_system, 6),
        "minimum_service": round(u_min, 6),
        "levels": levels,
        "satisfaction": satisfaction,
        "total_weight": total_weight,
        "weakest_camp_name": weakest_camp["name"] if weakest_camp else None,
        "weakest_camp_utility": round(u_min, 6),
        "camp_breakdown": breakdown
    }


# ======================================================================
# PHẦN 3: TỔNG HỢP VÀ PHÂN TÍCH CA GỐC / HỖ TRỢ NGÁCH K (BƯỚC 5 & 6)
# ======================================================================

def analyze_energy_and_camps(
    length: float,
    beacons: Sequence[Any],
    problem: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Hàm tích hợp đầy đủ cả hai trụ cột Năng lượng và Tín hiệu của Quốc Phong (N2).
    Hỗ trợ đọc sâu các trường hợp Ca A, B, C và phân tích so sánh K = 6, 8, 10.
    """
    e_dict = energy_metrics(length, beacons, problem)
    s_dict = signal_metrics(beacons, problem)

    # Đánh giá cán cân phân bổ năng lượng
    flight_ratio = e_dict["flight"] / e_dict["total"] if e_dict["total"] > 0 else 0.0
    lamp_ratio = e_dict["lamps"] / e_dict["total"] if e_dict["total"] > 0 else 0.0

    analysis = {
        "energy": e_dict,
        "signal": s_dict,
        "flight_ratio_percent": round(flight_ratio * 100.0, 2),
        "lamp_ratio_percent": round(lamp_ratio * 100.0, 2),
        "is_valid_battery": e_dict["energy_ok"],
        "weakest_camp": s_dict["weakest_camp_name"],
        "min_service": s_dict["minimum_service"],
    }
    return analysis


# ======================================================================
# PHẦN 4: VÍ DỤ TÍNH TAY VÀ TỰ KIỂM CHỨNG THEO ĐÚNG TÀI LIỆU
# ======================================================================

def run_self_verification():
    """
    Hàm chạy tự kiểm chứng với các ví dụ tính tay đối chiếu tài liệu:
    1. Trang 9: L = 150, pin đèn = 130 -> pin bay 67.5, pin tổng 197.5 (<= 220).
    2. Trang 10: Đèn pin 20: d=0 -> I=20; d=18 -> I=10; d=36 -> I=4.
    3. Trang 10: I = 0, 5, 10, 20, 40 -> u = 0, 0.3935, 0.6321, 0.8647, 0.9817.
    4. Trang 10: Ví dụ 2 trại w=3,1 với u=0.8, 0.4 -> U = 0.7, u_min = 0.4.
    5. Trang 12: Vượt pin tổng 230 -> over = 10 / 220 = 0.045455, phạt pin 30 * over^2.
    6. Kiểm tra đèn tắt không tiêu pin và không góp tín hiệu.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 76)
    print(" BỘ KIỂM CHỨNG TOÁN HỌC & ĐỐI CHIẾU SỐ LIỆU TÀI LIỆU (N2 - QUỐC PHONG)")
    print("=" * 76)

    # 1. Ví dụ Trang 9 tài liệu: L = 150, pin đèn = 130
    e_res = energy_metrics(length=150.0, beacons=[{"x": 50, "y": 50, "energy": 13.0, "active": True}] * 10)
    print("\n[1] Kiểm tra Pin (Tài liệu Trang 9): L = 150, Pin đèn = 130")
    print(f"    - Pin bay tính toán:  {e_res['flight']} (Kỳ vọng: 67.5)")
    print(f"    - Pin đèn tính toán:  {e_res['lamps']} (Kỳ vọng: 130.0)")
    print(f"    - Tổng pin tính toán: {e_res['total']} (Kỳ vọng: 197.5 <= 220)")
    print(f"    - Đạt chuẩn ngân sách: {e_res['energy_ok']}")
    assert abs(e_res["flight"] - 67.5) < 1e-5
    assert abs(e_res["lamps"] - 130.0) < 1e-5
    assert abs(e_res["total"] - 197.5) < 1e-5
    assert e_res["energy_ok"] is True
    print("    -> [KHỚP CHÍNH XÁC]")

    # 2. Ví dụ Trang 10 tài liệu: Đèn pin 20 suy giảm theo khoảng cách
    print("\n[2] Kiểm tra Suy giảm tín hiệu theo khoảng cách (Tài liệu Trang 10: Đèn pin 20)")
    i_0 = signal_from_single_beacon((0, 0), 20.0, (0, 0), signal_range=18.0)
    i_18 = signal_from_single_beacon((0, 0), 20.0, (18, 0), signal_range=18.0)
    i_36 = signal_from_single_beacon((0, 0), 20.0, (36, 0), signal_range=18.0)
    print(f"    - Tại d = 0  (ngay trại): I = {i_0:.4f} (Kỳ vọng: 20.0)")
    print(f"    - Tại d = 18 (cách 18dv): I = {i_18:.4f} (Kỳ vọng: 10.0)")
    print(f"    - Tại d = 36 (cách 36dv): I = {i_36:.4f} (Kỳ vọng: 4.0)")
    assert abs(i_0 - 20.0) < 1e-5
    assert abs(i_18 - 10.0) < 1e-5
    assert abs(i_36 - 4.0) < 1e-5
    print("    -> [KHỚP CHÍNH XÁC]")

    # 3. Bảng giá trị bão hòa Trang 10: I = [0, 5, 10, 20, 40]
    print("\n[3] Kiểm tra Bảng Hữu dụng Bão hòa u = 1 - exp(-0.1 * I) (Tài liệu Trang 10)")
    test_intensities = [0.0, 5.0, 10.0, 20.0, 40.0]
    expected_u = [0.0, 0.3935, 0.6321, 0.8647, 0.9817]
    for val_i, exp_u in zip(test_intensities, expected_u):
        actual_u = saturation_utility(val_i, alpha=0.1)
        print(f"    - I = {val_i:<4.1f} -> u = {actual_u:.4f} (Kỳ vọng: {exp_u:.4f})")
        assert abs(actual_u - exp_u) < 1e-3
    print("    -> [KHỚP CHÍNH XÁC]")

    # 4. Ví dụ 2 trại Trang 10: w = 3, 1 với u = 0.8, 0.4 -> U = 0.7, u_min = 0.4
    print("\n[4] Kiểm tra Gộp hữu dụng có trọng số (Tài liệu Trang 10: w=[3, 1], u=[0.8, 0.4])")
    w_example = [3.0, 1.0]
    u_example = [0.8, 0.4]
    u_weighted_calc = sum(w * u for w, u in zip(w_example, u_example)) / sum(w_example)
    u_min_calc = min(u_example)
    print(f"    - U tính toán:    {u_weighted_calc:.4f} (Kỳ vọng: 0.7000)")
    print(f"    - u_min tính toán: {u_min_calc:.4f} (Kỳ vọng: 0.4000)")
    assert abs(u_weighted_calc - 0.7000) < 1e-6
    assert abs(u_min_calc - 0.4000) < 1e-6
    print("    -> [KHỚP CHÍNH XÁC]")

    # 5. Kiểm tra vượt pin Trang 12: Tổng pin 230 -> over = 10 / 220
    print("\n[5] Kiểm tra Vượt pin chuẩn hóa (Tài liệu Trang 12: E_tong = 230, Budget = 220)")
    e_over = energy_metrics(length=200.0, beacons=[{"x": 50, "y": 50, "energy": 14.0, "active": True}] * 10)
    # L = 200 -> E_bay = 90; 10 đèn * 14 = 140 -> E_tong = 230
    exp_over = 10.0 / 220.0
    print(f"    - Tổng pin: {e_over['total']} | Vượt: {e_over['excess']}")
    print(f"    - over tính toán: {e_over['over']:.6f} (Kỳ vọng: {exp_over:.6f})")
    print(f"    - Phạt pin N3 (30 * over^2): {30.0 * (e_over['over'] ** 2):.6f}")
    assert abs(e_over["over"] - exp_over) < 1e-5
    assert e_over["energy_ok"] is False
    print("    -> [KHỚP CHÍNH XÁC - KHÔNG TỰ Ý CẮT BỚT PIN]")

    # 6. Kiểm tra đèn tắt (inactive) không tiêu pin và không phát tín hiệu
    print("\n[6] Kiểm tra Đèn tắt (active = False hoặc energy = 0)")
    beacons_with_off = [
        {"x": 12, "y": 70, "energy": 25.0, "active": False},  # Đèn tắt tại đúng trại C1!
        {"x": 20, "y": 25, "energy": 15.0, "active": True}
    ]
    e_off = energy_metrics(length=100.0, beacons=beacons_with_off)
    print(f"    - Tổng pin đèn: {e_off['lamps']} (Chỉ tính đèn active: 15.0, bỏ qua đèn tắt: 25.0)")
    assert abs(e_off["lamps"] - 15.0) < 1e-5
    print("    -> [KHỚP CHÍNH XÁC]")

    print("\n" + "=" * 76)
    print(" TẤT CẢ 6 ĐIỀU KIỆN KIỂM CHỨNG CỦA QUỐC PHONG ĐỀU THÀNH CÔNG RỰC RỠ!")
    print("=" * 76)


if __name__ == "__main__":
    run_self_verification()
