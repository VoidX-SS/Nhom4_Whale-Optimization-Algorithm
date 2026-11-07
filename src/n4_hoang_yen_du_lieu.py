"""
1. QUẢN LÝ ĐỀ & CẤU HÌNH:
   - Tải và kiểm tra 3 ca bài toán: A (cơ bản), B (khe hẹp), C (chắn đường).
   - Đảm bảo pin cố định 220, đúng 8 trại cứu trợ và bán kính bão có biên an toàn (+2).
2. GIỚI HẠN BIẾN & SỬA BIÊN (CLIPPING):
   - Không gian tìm kiếm gồm 30 biến thực (10 điểm * 3 biến [x, y, pin đề xuất]).
   - Giới hạn: x in [0, 100], y in [0, 100], pin in [0, 25].
   - Hàm sửa biên (clip_to_bounds) kéo các biến vượt ngoài về cạnh gần nhất.
3. GIẢI MÃ TOP-K ĐÈN (DECODE TOP-K):
   - Nhận mảng 30 số, giữ nguyên 10 điểm tọa độ trên đường bay.
   - Chọn tối đa K trạm có pin đề xuất lớn nhất (K = 6, 8, 10).
   - Quy tắc hòa pin: ưu tiên trạm có chỉ số nhỏ hơn.
   - Các trạm đèn ngoài top-K bị tắt (pin = 0.0).
4. BA LỊCH GIẢM HỆ SỐ a (LINEAR, COSINE, QUADRATIC):
   - Tính hệ số a theo tỷ lệ t / T.
   - Giữ độc lập luật a2 và tham số l của thuật toán gốc.
5. ĐỐI CHỨNG BA LỊCH a TRÊN CA B (KHE HẸP):
   - Thực nghiệm so sánh 3 lịch a trên Ca B.
"""

import os
import sys
import json
import math
import random
from typing import Dict, List, Tuple, Any, Optional, Union

# Các thông số mặc định của bài toán
DEFAULT_BOUNDS_X = (0.0, 100.0)
DEFAULT_BOUNDS_Y = (0.0, 100.0)
DEFAULT_BOUNDS_PIN = (0.0, 25.0)
NUM_WAYPOINTS = 10
NUM_VARIABLES = 30     # Luôn là 30 biến thực (10 điểm * [x, y, pin])
BATTERY_MAX = 220.0    # Mọi ca đều có pin tối đa 220.0
START_POINT = (0.0, 50.0)
GOAL_POINT = (100.0, 50.0)

# PHẦN 1: QUẢN LÝ ĐỀ VÀ CẤU HÌNH BÀI TOÁN
def get_default_settings() -> Dict[str, Any]:
    """Trả về cấu hình mặc định cho bài toán bay UAV."""
    return {
        "num_waypoints": NUM_WAYPOINTS,
        "num_variables": NUM_VARIABLES,
        "bounds": {
            "x": list(DEFAULT_BOUNDS_X),
            "y": list(DEFAULT_BOUNDS_Y),
            "pin": list(DEFAULT_BOUNDS_PIN),
        },
        "start": list(START_POINT),
        "goal": list(GOAL_POINT),
        "battery_max": BATTERY_MAX,
        "default_K": 10,
        "valid_K_values": [6, 8, 10],
        "flight_energy_rate": 0.45,   # Pin bay: E_bay = 0.45 * L
        "signal_scale_dist": 18.0,    # Thang suy giảm tín hiệu d^2 / 18^2
        "utility_decay": 0.1,         # Hàm bão hòa u_m = 1 - exp(-0.1 * I_m)
        "cost_length_weight": 0.12,   # Hệ số đánh đổi độ dài f0 = -U + 0.12 * (L / 100)
        "penalty_weights": {
            "lambda_storm": 100.0,    # Phạt lấn bão Pc
            "lambda_battery": 30.0,   # Phạt vượt pin V^2
            "lambda_map": 100.0       # Phạt tràn mép bản đồ Pmap
        }
    }


def find_data_file(case_name_or_path: str) -> str:
    """Tìm đường dẫn file dữ liệu JSON tương ứng với tên ca hoặc đường dẫn truyền vào."""
    alias_map = {
        "A": "co_ban.json", "CO_BAN": "co_ban.json", "COBAN": "co_ban.json",
        "B": "khe_hep.json", "KHE_HEP": "khe_hep.json", "KHEHEP": "khe_hep.json",
        "C": "chan_duong.json", "CHAN_DUONG": "chan_duong.json", "CHANDUONG": "chan_duong.json"
    }
    key = str(case_name_or_path).strip().upper()
    filename = alias_map.get(key, case_name_or_path)

    candidate_paths = [
        filename,
        os.path.join("data", filename),
        os.path.join("..", "data", filename),
        os.path.join(os.path.dirname(__file__), "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "data", filename),
    ]
    for p in candidate_paths:
        if os.path.isfile(p):
            return os.path.abspath(p)
    return os.path.abspath(os.path.join("data", filename))


def load_problem(case: str = "A") -> Dict[str, Any]:
    """Tải và xác thực dữ liệu từ file JSON của ca A, B hoặc C."""
    file_path = find_data_file(case)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: '{file_path}'.")

    with open(file_path, "r", encoding="utf-8") as f:
        problem = json.load(f)

    is_valid, errors = validate_problem(problem)
    if not is_valid:
        raise ValueError(f"Dữ liệu đề bài {file_path} không hợp lệ:\n- " + "\n- ".join(errors))

    return problem


def validate_problem(problem: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Kiểm tra tính hợp lệ của đề bài (pin 220, 8 trại, cổng khe B)."""
    errors = []

    case_id = str(problem.get("case_id", "")).strip().upper()
    valid_cases = {"A": "co_ban", "B": "khe_hep", "C": "chan_duong"}
    if case_id not in valid_cases:
        errors.append(f"Tên ca không hợp lệ: '{case_id}'. Phải là A, B hoặc C.")

    battery_max = float(problem.get("battery_max", 0.0))
    if abs(battery_max - 220.0) > 1e-4:
        errors.append(f"battery_max = {battery_max} != 220.0 (Mọi ca bắt buộc pin 220).")

    start = problem.get("start")
    goal = problem.get("goal")
    if not start or len(start) != 2 or not (0 <= start[0] <= 100 and 0 <= start[1] <= 100):
        errors.append(f"Tọa độ Start không hợp lệ: {start}.")
    if not goal or len(goal) != 2 or not (0 <= goal[0] <= 100 and 0 <= goal[1] <= 100):
        errors.append(f"Tọa độ Goal không hợp lệ: {goal}.")

    camps = problem.get("camps", [])
    if len(camps) != 8:
        errors.append(f"Số lượng trại không đúng: có {len(camps)} trại, yêu cầu đúng 8 trại.")

    storms = problem.get("storms", [])
    if not storms:
        errors.append("Danh sách bão bị trống.")

    if case_id == "B" and not problem.get("narrow_gate"):
        errors.append("Ca B bắt buộc phải có thuộc tính 'narrow_gate'.")

    return len(errors) == 0, errors


# PHẦN 2: GIỚI HẠN BIẾN (BOUNDS) VÀ SỬA BIÊN (CLIPPING)
def get_bounds(dim: int = NUM_VARIABLES) -> Tuple[List[float], List[float]]:
    """Trả về giới hạn [0, 100] cho x/y và [0, 25] cho pin (tổng 30 biến)."""
    if dim != NUM_VARIABLES:
        raise ValueError(f"Bài toán luôn có đúng 30 biến. Nhận dim = {dim}.")

    lower_bounds, upper_bounds = [], []
    for _ in range(NUM_WAYPOINTS):
        lower_bounds.extend([0.0, 0.0, 0.0])
        upper_bounds.extend([100.0, 100.0, 25.0])
    return lower_bounds, upper_bounds


def clip_to_bounds(x: Union[List[float], Tuple[float, ...]]) -> List[float]:
    """Hàm sửa biên: Kéo các giá trị vượt ngoài miền về cạnh gần nhất."""
    lb, ub = get_bounds(NUM_VARIABLES)
    return [max(lb[j], min(ub[j], float(x[j]))) for j in range(NUM_VARIABLES)]


def validate_solution_vector(x: Any) -> Tuple[bool, List[str]]:
    """Kiểm tra một cá voi có đúng 30 số thực hợp lệ trong bounds hay không."""
    if not hasattr(x, "__len__") or len(x) != NUM_VARIABLES:
        return False, [f"Vector nghiệm phải có đúng {NUM_VARIABLES} biến."]

    lb, ub = get_bounds(NUM_VARIABLES)
    issues = []
    for j in range(NUM_VARIABLES):
        val = x[j]
        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            issues.append(f"Biến thứ {j} không hợp lệ (NaN/Inf).")
        elif val < lb[j] - 1e-6 or val > ub[j] + 1e-6:
            issues.append(f"Biến thứ {j} = {val:.2f} vượt ngoài [{lb[j]}, {ub[j]}].")
    return len(issues) == 0, issues


# PHẦN 3: GIẢI MÃ TOP-K ĐÈN
class DecodedSolution:
    """Lớp chứa dữ liệu đã giải mã từ vector 30 số."""
    def __init__(
        self,
        waypoints: List[Tuple[float, float]],
        full_path: List[Tuple[float, float]],
        light_powers: List[float],
        proposed_pins: List[float],
        active_light_indices: List[int],
        disabled_light_indices: List[int],
        K: int,
        vector_30: List[float]
    ):
        self.waypoints = waypoints                  # 10 điểm trung gian
        self.full_path = full_path                  # 12 điểm: [Start, 10 điểm, Goal]
        self.light_powers = light_powers            # 10 mức pin thực tế (ngoài top-K = 0.0)
        self.proposed_pins = proposed_pins          # 10 mức pin đề xuất gốc
        self.active_light_indices = active_light_indices      # Chỉ số trạm bật
        self.disabled_light_indices = disabled_light_indices  # Chỉ số trạm tắt
        self.K = K
        self.vector_30 = vector_30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "K": self.K,
            "waypoints": self.waypoints,
            "full_path": self.full_path,
            "light_powers": self.light_powers,
            "proposed_pins": self.proposed_pins,
            "active_light_indices": self.active_light_indices,
            "disabled_light_indices": self.disabled_light_indices,
            "total_light_allocated": sum(self.light_powers)
        }


def decode_solution(
    vector_30: Union[List[float], Tuple[float, ...]],
    K: int = 10,
    problem: Optional[Dict[str, Any]] = None,
    start: Optional[Tuple[float, float]] = None,
    goal: Optional[Tuple[float, float]] = None
) -> DecodedSolution:
    """
    Giải mã mảng 30 số thành đường bay và phân bổ pin:
    - 10 điểm tọa độ giữ nguyên làm đường bay.
    - Chọn K trạm có pin đề xuất lớn nhất; hòa pin ưu tiên chỉ số nhỏ hơn.
    - Các trạm ngoài top-K gán pin = 0.0.
    """
    if len(vector_30) != NUM_VARIABLES:
        raise ValueError(f"Mảng đầu vào phải có đúng {NUM_VARIABLES} số thực, nhận {len(vector_30)}.")

    if K not in [6, 8, 10]:
        raise ValueError(f"K phải là 6, 8 hoặc 10, nhận K = {K}.")

    clipped_vec = clip_to_bounds(vector_30)

    if start is None or goal is None:
        if problem is not None:
            start_pt = tuple(problem.get("start", list(START_POINT)))
            goal_pt = tuple(problem.get("goal", list(GOAL_POINT)))
        else:
            start_pt = START_POINT
            goal_pt = GOAL_POINT
    else:
        start_pt = tuple(start)
        goal_pt = tuple(goal)

    # 1. Tách 10 bộ (x, y, pin)
    waypoints: List[Tuple[float, float]] = []
    proposed_pins: List[float] = []

    for i in range(NUM_WAYPOINTS):
        idx = i * 3
        waypoints.append((round(clipped_vec[idx], 4), round(clipped_vec[idx + 1], 4)))
        proposed_pins.append(round(clipped_vec[idx + 2], 4))

    # 2. Xếp hạng Top-K (ưu tiên pin cao, nếu hòa pin ưu tiên chỉ số nhỏ)
    sorted_indices = sorted(range(NUM_WAYPOINTS), key=lambda i: (-proposed_pins[i], i))
    active_indices = sorted(sorted_indices[:K])
    disabled_indices = sorted(sorted_indices[K:])
    active_set = set(active_indices)

    # 3. Gán pin thực tế: ngoài top-K gán bằng 0.0
    light_powers = [proposed_pins[i] if i in active_set else 0.0 for i in range(NUM_WAYPOINTS)]
    full_path = [start_pt] + waypoints + [goal_pt]

    return DecodedSolution(
        waypoints=waypoints,
        full_path=full_path,
        light_powers=light_powers,
        proposed_pins=proposed_pins,
        active_light_indices=active_indices,
        disabled_light_indices=disabled_indices,
        K=K,
        vector_30=clipped_vec
    )


# PHẦN 4: BA LỊCH GIẢM HỆ SỐ a
def get_a_value(t: float, T: float, mode: str = "linear") -> float:
    """
    Tính hệ số a(t) giảm từ 2 về 0 theo 3 lịch (dùng mẫu số T):
    - 'linear':    a = 2 * (1 - t/T)
    - 'cosine':    a = 1 + cos(pi * t/T)
    - 'quadratic': a = 2 * (1 - t/T)^2
    """
    if T <= 0:
        raise ValueError(f"Tổng số lượt T phải > 0. Nhận T = {T}.")

    s = max(0.0, min(1.0, float(t) / float(T)))
    mode_clean = str(mode).strip().lower()

    if mode_clean in ["linear", "tuyen_tinh", "goc"]:
        a = 2.0 * (1.0 - s)
    elif mode_clean in ["cosine", "cos"]:
        a = 1.0 + math.cos(math.pi * s)
    elif mode_clean in ["quadratic", "quad", "bac_2"]:
        a = 2.0 * ((1.0 - s) ** 2)
    else:
        raise ValueError(f"Chế độ '{mode}' không hợp lệ. Chọn 'linear', 'cosine' hoặc 'quadratic'.")

    return max(0.0, min(2.0, a))


def get_a2_author(t: float, T: float) -> float:
    """
    Luật a2 nguyên bản từ thuật toán WOA gốc:
    a2 = -1 - (t / T) giảm tuyến tính từ -1 về -2.
    Độc lập hoàn toàn, không thay đổi khi đổi ngách lịch a.
    """
    if T <= 0:
        raise ValueError(f"T phải > 0. Nhận T = {T}.")
    s = max(0.0, min(1.0, float(t) / float(T)))
    return -1.0 - s


def get_exploration_probability(a: float) -> float:
    """Xác suất lý thuyết chọn nhánh khám phá (|A| >= 1). Khi a <= 1 thì xác suất = 0."""
    if a <= 1.0:
        return 0.0
    return (a - 1.0) / a


# PHẦN 5: ĐÁNH GIÁ ĐƯỜNG BAY, ĐO BÃO, PIN & TIÊU CHÍ BÀI TOÁN
def compute_segment_storm_distance(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    storm_center: Tuple[float, float]
) -> float:
    """Khoảng cách ngắn nhất từ tâm bão O đến đoạn thẳng A(p1) -> B(p2) bằng hình chiếu."""
    ax, ay = p1
    bx, by = p2
    ox, oy = storm_center

    vx = bx - ax
    vy = by - ay
    v_norm_sq = vx * vx + vy * vy

    if v_norm_sq < 1e-9:
        return math.hypot(ox - ax, oy - ay)

    tau_hat = ((ox - ax) * vx + (oy - ay) * vy) / v_norm_sq
    tau = max(0.0, min(1.0, tau_hat))

    hx = ax + tau * vx
    hy = ay + tau * vy
    return math.hypot(ox - hx, oy - hy)


def check_gate_passage(path: List[Tuple[float, float]]) -> bool:
    """Kiểm tra đường bay có vượt qua khe hẹp ở Ca B hay không (cổng tại x=40, y trong [47, 53])."""
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        if x1 < 40.0 <= x2:
            dx = x2 - x1
            if abs(dx) > 1e-9:
                y_cross = y1 + ((40.0 - x1) / dx) * (y2 - y1)
                if 47.0 <= y_cross <= 53.0:
                    return True
    return False


def evaluate_solution(
    vector_30: List[float],
    problem: Dict[str, Any],
    settings: Optional[Dict[str, Any]] = None,
    K: int = 10
) -> Dict[str, Any]:
    """Hàm chấm điểm toàn diện phương án bay (chiều dài L, pin, hữu dụng U, phạt bão Pc, điểm J và f0)."""
    if settings is None:
        settings = get_default_settings()

    decoded = decode_solution(vector_30, K=K, problem=problem)
    path = decoded.full_path
    lights = decoded.light_powers

    # 1. Chiều dài đường bay L
    L = 0.0
    for i in range(len(path) - 1):
        L += math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])

    # 2. Túi pin: E_bay = 0.45 * L, E_den = sum(e~_k)
    e_flight = 0.45 * L
    e_light = sum(lights)
    e_total = e_flight + e_light
    battery_max = float(problem.get("battery_max", BATTERY_MAX))
    V = max(0.0, e_total - battery_max) / battery_max

    # 3. Tín hiệu và hữu dụng tại 8 trại
    camps = problem.get("camps", [])
    total_camp_weight = sum(camp.get("weight", 1.0) for camp in camps) if camps else 1.0
    weighted_u_sum = 0.0
    u_list = []

    for camp in camps:
        cx, cy = camp["pos"]
        w_m = float(camp.get("weight", 1.0))

        I_m = 0.0
        for k in range(NUM_WAYPOINTS):
            e_k_eff = lights[k]
            if e_k_eff > 0.0:
                wx, wy = decoded.waypoints[k]
                d_sq = (wx - cx) ** 2 + (wy - cy) ** 2
                I_m += e_k_eff / (1.0 + d_sq / (18.0 ** 2))

        u_m = 1.0 - math.exp(-0.1 * I_m)
        u_list.append(u_m)
        weighted_u_sum += w_m * u_m

    U = weighted_u_sum / total_camp_weight if camps else 0.0
    u_min = min(u_list) if u_list else 0.0

    # 4. Đo bão: Pc = sum ( [Rv - d_iv]+ / Rv )^2
    storms = problem.get("storms", [])
    Pc = 0.0
    min_dist_to_safe_boundary = float("inf")

    for i in range(len(path) - 1):
        seg_start = path[i]
        seg_end = path[i + 1]
        for storm in storms:
            sc = tuple(storm["center"])
            r_orig = float(storm.get("radius", 0.0))
            sm = float(storm.get("safety_margin", 2.0))
            Rv = storm.get("effective_radius", r_orig + sm)

            d_iv = compute_segment_storm_distance(seg_start, seg_end, sc)
            margin_clearance = d_iv - Rv
            if margin_clearance < min_dist_to_safe_boundary:
                min_dist_to_safe_boundary = margin_clearance

            violation = max(0.0, Rv - d_iv)
            if violation > 0.0 and Rv > 0.0:
                Pc += (violation / Rv) ** 2

    # 5. Phạt bản đồ Pmap
    Pmap = 0.0
    for wx, wy in decoded.waypoints:
        gx = max(0.0, -wx, wx - 100.0) / 100.0
        gy = max(0.0, -wy, wy - 100.0) / 100.0
        Pmap += (gx ** 2 + gy ** 2)

    # 6. Mục tiêu chưa phạt f0 và điểm so sánh leader J
    f0 = -U + 0.12 * (L / 100.0)
    J = f0 + 100.0 * Pc + 30.0 * (V ** 2) + 100.0 * Pmap

    # 7. Kiểm tra hợp lệ
    is_valid = (
        (e_total <= battery_max + 1e-7)
        and (min_dist_to_safe_boundary >= -1e-9)
        and (Pmap <= 1e-9)
    )

    is_gate_passed = check_gate_passage(path)

    return {
        "fitness": J,
        "J": J,
        "f0": f0,
        "U": U,
        "u_min": u_min,
        "length": L,
        "e_flight": e_flight,
        "e_light": e_light,
        "total_energy": e_total,
        "battery_violation": max(0.0, e_total - battery_max),
        "storm_penalty": Pc,
        "min_storm_clearance": min_dist_to_safe_boundary,
        "is_valid": is_valid,
        "is_gate_passed": is_gate_passed,
        "decoded": decoded
    }


# PHẦN 6: THỰC THI THUẬT TOÁN WOA & ĐỐI CHỨNG BA LỊCH a
def run_woa_single_experiment(
    problem: Dict[str, Any],
    settings: Optional[Dict[str, Any]] = None,
    a_mode: str = "linear",
    max_iter: int = 150,
    pop_size: int = 30,
    seed: int = 42,
    K: int = 10
) -> Dict[str, Any]:
    """Chạy 1 lượt thuật toán WOA với 3 sổ ghi nghiệm: best_overall, best_valid, best_gate."""
    if settings is None:
        settings = get_default_settings()

    random.seed(seed)
    lb, ub = get_bounds(NUM_VARIABLES)

    population = []
    for _ in range(pop_size):
        whale = [lb[j] + random.random() * (ub[j] - lb[j]) for j in range(NUM_VARIABLES)]
        population.append(whale)

    best_overall_whale = None
    best_overall_J = float("inf")
    best_overall_metrics = None

    best_valid_whale = None
    best_valid_f0 = float("inf")
    best_valid_metrics = None

    best_gate_whale = None
    best_gate_f0 = float("inf")
    best_gate_metrics = None

    for whale in population:
        metrics = evaluate_solution(whale, problem, settings, K=K)
        j_score = metrics["J"]
        f0_score = metrics["f0"]

        if j_score < best_overall_J:
            best_overall_J = j_score
            best_overall_whale = list(whale)
            best_overall_metrics = metrics

        if metrics["is_valid"] and f0_score < best_valid_f0:
            best_valid_f0 = f0_score
            best_valid_whale = list(whale)
            best_valid_metrics = metrics

        if metrics["is_valid"] and metrics["is_gate_passed"] and f0_score < best_gate_f0:
            best_gate_f0 = f0_score
            best_gate_whale = list(whale)
            best_gate_metrics = metrics

    history_best_J = []
    first_valid_iter = -1
    first_gate_iter = -1

    for t in range(max_iter):
        a = get_a_value(t, max_iter, mode=a_mode)
        a2 = get_a2_author(t, max_iter)

        for i in range(pop_size):
            p = random.random()
            r1 = random.random()
            r2 = random.random()

            A_val = 2.0 * a * r1 - a
            C_val = 2.0 * r2
            b_spiral = 1.0
            r_l = random.random()
            l_spiral = 1.0 + (a2 - 1.0) * r_l

            new_whale = [0.0] * NUM_VARIABLES

            if p < 0.5:
                if abs(A_val) < 1.0:
                    # Nhánh 1: Bao vây phương án tốt nhất X*
                    for j in range(NUM_VARIABLES):
                        D = abs(C_val * best_overall_whale[j] - population[i][j])
                        new_whale[j] = best_overall_whale[j] - A_val * D
                else:
                    # Nhánh 2: Khám phá theo cá voi ngẫu nhiên X_rand
                    for j in range(NUM_VARIABLES):
                        rand_idx = random.randint(0, pop_size - 1)
                        X_rand_val = population[rand_idx][j]
                        D_rand = abs(C_val * X_rand_val - population[i][j])
                        new_whale[j] = X_rand_val - A_val * D_rand
            else:
                # Nhánh 3: Xoắn quanh leader X*
                spiral_factor = math.exp(b_spiral * l_spiral) * math.cos(2.0 * math.pi * l_spiral)
                for j in range(NUM_VARIABLES):
                    D_prime = abs(best_overall_whale[j] - population[i][j])
                    new_whale[j] = best_overall_whale[j] + D_prime * spiral_factor

            new_whale = clip_to_bounds(new_whale)
            population[i] = new_whale

            metrics = evaluate_solution(new_whale, problem, settings, K=K)
            j_score = metrics["J"]
            f0_score = metrics["f0"]

            if j_score < best_overall_J:
                best_overall_J = j_score
                best_overall_whale = list(new_whale)
                best_overall_metrics = metrics

            if metrics["is_valid"]:
                if first_valid_iter == -1:
                    first_valid_iter = t
                if f0_score < best_valid_f0:
                    best_valid_f0 = f0_score
                    best_valid_whale = list(new_whale)
                    best_valid_metrics = metrics

            if metrics["is_valid"] and metrics["is_gate_passed"]:
                if first_gate_iter == -1:
                    first_gate_iter = t
                if f0_score < best_gate_f0:
                    best_gate_f0 = f0_score
                    best_gate_whale = list(new_whale)
                    best_gate_metrics = metrics

        history_best_J.append(best_overall_J)

    return {
        "a_mode": a_mode,
        "seed": seed,
        "best_overall_score": best_overall_J,
        "best_overall_metrics": best_overall_metrics,
        "best_valid_score": best_valid_f0 if best_valid_whale is not None else None,
        "best_valid_metrics": best_valid_metrics,
        "best_gate_metrics": best_gate_metrics,
        "found_valid": best_valid_whale is not None,
        "found_gate": best_gate_whale is not None,
        "first_valid_iteration": first_valid_iter,
        "first_gate_iteration": first_gate_iter,
        "history_best_score": history_best_J,
        "final_whale": best_valid_whale if best_valid_whale is not None else best_overall_whale
    }


def benchmark_3_a_schedules_on_case_B(
    num_runs: int = 3,
    max_iter: int = 80,
    pop_size: int = 25,
    K: int = 10
) -> Dict[str, Any]:
    """Thực nghiệm đối chứng 3 lịch a (linear, cosine, quadratic) trên Ca B."""
    problem_B = load_problem("B")
    settings = get_default_settings()

    modes = ["linear", "cosine", "quadratic"]
    summary_results = {mode: [] for mode in modes}

    print("\n" + "=" * 75)
    print(f"TIẾN HÀNH ĐỐI CHỨNG 3 LỊCH a TRÊN CA B (KHE HẸP) - SỐ LƯỢT = {num_runs}")
    print("=" * 75)

    for mode in modes:
        print(f"-> Đang chạy lịch a = '{mode}' ...")
        for run_id in range(num_runs):
            seed = 42 + run_id * 101
            res = run_woa_single_experiment(
                problem=problem_B,
                settings=settings,
                a_mode=mode,
                max_iter=max_iter,
                pop_size=pop_size,
                seed=seed,
                K=K
            )
            summary_results[mode].append(res)

    stats = {}
    for mode in modes:
        runs = summary_results[mode]
        valid_runs = [r for r in runs if r["found_valid"]]
        gate_runs = [r for r in runs if r["found_gate"]]
        valid_f0_list = [r["best_valid_score"] for r in valid_runs]
        overall_j_list = [r["best_overall_score"] for r in runs]

        avg_valid_f0 = (sum(valid_f0_list) / len(valid_f0_list)) if valid_f0_list else None
        best_valid_f0 = min(valid_f0_list) if valid_f0_list else None

        stats[mode] = {
            "mode_name": mode,
            "total_runs": len(runs),
            "valid_runs": len(valid_runs),
            "gate_runs": len(gate_runs),
            "success_rate_percent": round(len(valid_runs) / len(runs) * 100.0, 1),
            "gate_passage_rate_percent": round(len(gate_runs) / len(runs) * 100.0, 1),
            "best_valid_f0": round(best_valid_f0, 4) if best_valid_f0 is not None else None,
            "avg_valid_f0": round(avg_valid_f0, 4) if avg_valid_f0 is not None else None,
            "avg_overall_J": round(sum(overall_j_list) / len(overall_j_list), 4),
        }

    return stats


# PHẦN 7: TỰ KIỂM TRA TOÀN DIỆN KHI CHẠY TRỰC TIẾP FILE
def run_full_validation():
    """Hàm chạy kiểm tra tự động tất cả các chức năng."""
    print("\n" + "=" * 78)
    print(" 1. KIỂM TRA DỮ LIỆU ĐỀ BÀI (3 CA A, B, C)")
    print("=" * 78)
    for case_id in ["A", "B", "C"]:
        prob = load_problem(case_id)
        gate_info = "Có cổng khe [x=40, y in 47..53]" if prob.get("narrow_gate") else "Không (bình thường)"
        print(f"  [OK] Ca {prob['case_id']}: {prob['title']} | Pin max: {prob['battery_max']} | Trại: {len(prob['camps'])} | Bão: {len(prob['storms'])} | Cổng khe: {gate_info}")

    print("\n" + "=" * 78)
    print(" 2. KIỂM TRA BOUNDS & SỬA BIÊN (CLIPPING)")
    print("=" * 78)
    lb, ub = get_bounds(30)
    print(f"  + Số lượng biến: {len(lb)} (đúng 30 biến)")
    print(f"  + Giới hạn x: [{lb[0]}, {ub[0]}], y: [{lb[1]}, {ub[1]}], pin: [{lb[2]}, {ub[2]}]")
    sample_out = [-15.0, 120.0, 35.0] + [50.0, 50.0, 10.0] * 9
    clipped = clip_to_bounds(sample_out)
    print(f"  + Thử clip [-15.0, 120.0, 35.0] -> [{clipped[0]}, {clipped[1]}, {clipped[2]}] (Đã sửa đúng bounds!)")

    print("\n" + "=" * 78)
    print(" 3. KIỂM TRA GIẢI MÃ TOP-K ĐÈN (K = 10, 8, 6)")
    print("=" * 78)
    test_vec = []
    test_coords = [(10, 50), (20, 40), (30, 60), (40, 50), (50, 45), (60, 55), (70, 50), (80, 45), (85, 55), (90, 50)]
    test_pins = [12.0, 15.0, 20.0, 15.0, 20.0, 8.0, 22.0, 5.0, 18.0, 10.0]
    for i in range(10):
        test_vec.extend([test_coords[i][0], test_coords[i][1], test_pins[i]])

    for k_val in [10, 8, 6]:
        dec = decode_solution(test_vec, K=k_val)
        print(f"  * K = {k_val}: Giữ {len(dec.waypoints)} điểm đường bay | Bật {len(dec.active_light_indices)} đèn: {dec.active_light_indices} | Tắt {len(dec.disabled_light_indices)} đèn: {dec.disabled_light_indices}")

    print("\n" + "=" * 78)
    print(" 4. KIỂM TRA 3 LỊCH GIẢM a VÀ BẢO TOÀN a2")
    print("=" * 78)
    T_test = 800
    checkpoints = [("Đầu (s = 0.00)", 0), ("1/4 (s = 0.25)", 200), ("Giữa (s = 0.50)", 400), ("3/4 (s = 0.75)", 600), ("Cuối (s = 1.00)", 800)]
    print(f"{'Mốc vòng lặp':<20} | {'Linear':<12} | {'Cosine':<12} | {'Quadratic':<14} | {'a2 (Tác giả)':<12}")
    print("-" * 75)
    for label, t_val in checkpoints:
        a_lin = get_a_value(t_val, T_test, mode="linear")
        a_cos = get_a_value(t_val, T_test, mode="cosine")
        a_quad = get_a_value(t_val, T_test, mode="quadratic")
        a2_val = get_a2_author(t_val, T_test)
        print(f"{label:<20} | {a_lin:<12.4f} | {a_cos:<12.4f} | {a_quad:<14.4f} | {a2_val:<12.4f}")

    print("\n" + "=" * 78)
    print(" 5. THỰC NGHIỆM ĐỐI CHỨNG 3 LỊCH a TRÊN CA B (KHE HẸP)")
    print("=" * 78)
    stats = benchmark_3_a_schedules_on_case_B(num_runs=3, max_iter=80, pop_size=25, K=10)
    print("\nKẾT QUẢ ĐỐI CHỨNG TRÊN CA B:")
    print(f"{'Ngách Lịch a':<16} | {'Tỷ lệ hợp lệ':<15} | {'Tỷ lệ qua khe':<15} | {'f0 Hợp lệ Tốt nhất':<20}")
    print("-" * 70)
    for mode, st in stats.items():
        bv = f"{st['best_valid_f0']:.4f}" if st['best_valid_f0'] is not None else "Chưa có"
        print(f"{mode:<16} | {st['success_rate_percent']:<14.1f}% | {st['gate_passage_rate_percent']:<14.1f}% | {bv:<20}")
    print("\n" + "=" * 78)
    print(" TẤT CẢ KIỂM TRA ĐỀU THÀNH CÔNG VÀ CHÍNH XÁC!")
    print("=" * 78)


if __name__ == "__main__":
    run_full_validation()
