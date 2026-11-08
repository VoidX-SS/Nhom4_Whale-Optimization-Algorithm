"""
Quy ước:
- Module chỉ di chuyển cá voi. Chấm điểm, cập nhật leader và gọi repair_population
  ở đầu lượt kế tiếp là việc của N6 (hàm woa chung).
- l (chữ thường) là số ngẫu nhiên của xoắn ốc, khác L là độ dài đường bay của N1/N4.
- Cập nhật TẠI CHỖ, không dùng bản chụp đàn cũ.
"""

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple
 
B_SPIRAL = 1.0
L_MODES = ("shared_l", "independent_l")
BOUNDARY_MODES = ("clip", "reinit")
 
 
def make_rngs(seed: int) -> Tuple[random.Random, random.Random]:
    """(rng chính, rng phụ). Rng phụ chỉ sinh các l riêng của independent_l,
    nên luồng chính (r1, r2, l, p, chọn cá voi tham khảo) của hai chế độ giống hệt nhau."""
    return random.Random(seed), random.Random(seed + 1_000_003)
 
 
#KHỞI TẠO
def init_population(
    pop_size: int, lb: Sequence[float], ub: Sequence[float],
    rng: Optional[random.Random] = None, seed: Optional[int] = None,
) -> List[List[float]]:
    """N cá voi, mỗi chiều ngẫu nhiên đều trong [lb[j], ub[j]] (lb, ub có thể âm)."""
    if len(lb) != len(ub) or any(l > u for l, u in zip(lb, ub)):
        raise ValueError("lb, ub phải cùng độ dài và lb <= ub.")
    rng = rng or random.Random(seed)
    return [[lb[j] + rng.random() * (ub[j] - lb[j]) for j in range(len(lb))]
            for _ in range(pop_size)]
 
 
# BIÊN
def repair_boundary(
    x: Sequence[float], lb: Sequence[float], ub: Sequence[float],
    mode: str = "clip", rng: Optional[random.Random] = None,
) -> List[float]:
    """clip: kéo ô vượt biên về cạnh gần nhất. reinit: sinh lại ô vượt biên trong [lb, ub]."""
    if mode == "clip":
        return [min(max(float(x[j]), lb[j]), ub[j]) for j in range(len(x))]
    if mode == "reinit":
        rng = rng or random.Random()
        return [float(x[j]) if lb[j] <= x[j] <= ub[j]
                else lb[j] + rng.random() * (ub[j] - lb[j]) for j in range(len(x))]
    raise ValueError(f"boundary mode phải thuộc {BOUNDARY_MODES}, nhận '{mode}'.")
 
 
def repair_population(
    population: List[List[float]], lb: Sequence[float], ub: Sequence[float],
    mode: str = "clip", rng: Optional[random.Random] = None,
) -> None:
    """Sửa biên tại chỗ cho cả đàn. N6 gọi ở ĐẦU mỗi lượt, trước khi chấm điểm."""
    for i in range(len(population)):
        population[i] = repair_boundary(population[i], lb, ub, mode, rng)
 
 
# NHÁNH
def encircle_prey(x, leader, A: float, C: float) -> List[float]:
    """|A| < 1: D = |C.X* - X|; X' = X* - A.D (theo từng chiều)."""
    return [leader[j] - A * abs(C * leader[j] - x[j]) for j in range(len(x))]
 
 
def search_for_prey(x, population, A: float, C: float, rng: random.Random) -> List[float]:
    """|A| >= 1: cá voi tham khảo chọn riêng cho từng chiều (như WOA.m)."""
    n = len(population)
    out = []
    for j in range(len(x)):
        x_rand = population[rng.randrange(n)][j]
        out.append(x_rand - A * abs(C * x_rand - x[j]))
    return out
 
 
def spiral_update(x, leader, l_values: Sequence[float], b: float = B_SPIRAL) -> List[float]:
    """p >= 0.5: X' = |X* - X|.e^(b.l).cos(2.pi.l) + X*."""
    return [abs(leader[j] - x[j]) * math.exp(b * l_values[j]) * math.cos(2.0 * math.pi * l_values[j])
            + leader[j] for j in range(len(x))]
 
 
# 4. NGÁCH 
def draw_l(a2: float, rng: random.Random, mode: str = "shared_l",
           dim: int = 30, aux_rng: Optional[random.Random] = None) -> List[float]:
    """l = (a2 - 1).rand + 1. Luôn rút 1 số từ rng chính (đúng thứ tự WOA.m).
    shared_l: dùng số đó cho mọi chiều.
    independent_l: bỏ số đó, rút `dim` số l riêng từ aux_rng."""
    l0 = (a2 - 1.0) * rng.random() + 1.0
    if mode == "shared_l":
        return [l0] * dim
    if mode == "independent_l":
        if aux_rng is None:
            raise ValueError("independent_l cần aux_rng (xem make_rngs).")
        return [(a2 - 1.0) * aux_rng.random() + 1.0 for _ in range(dim)]
    raise ValueError(f"l_mode phải thuộc {L_MODES}, nhận '{mode}'.")
 
 
# 5. CẬP NHẬT 
def update_whale(i, population, leader, a: float, a2: float, rng: random.Random,
                 l_mode: str = "shared_l", aux_rng: Optional[random.Random] = None,
                 b: float = B_SPIRAL) -> Tuple[List[float], str]:
    """Thứ tự sinh số như WOA.m: r1, r2, l, p."""
    x = population[i]
    r1, r2 = rng.random(), rng.random()
    A, C = 2.0 * a * r1 - a, 2.0 * r2
    l_values = draw_l(a2, rng, l_mode, len(x), aux_rng)
    p = rng.random()
    if p < 0.5:
        if abs(A) >= 1.0:
            return search_for_prey(x, population, A, C, rng), "search"
        return encircle_prey(x, leader, A, C), "encircle"
    return spiral_update(x, leader, l_values, b), "spiral"
 
 
def update_population(population, leader, a, a2, rng, l_mode="shared_l",
                      aux_rng=None, b=B_SPIRAL) -> Dict[str, int]:
    """Cập nhật tại chỗ từng cá voi, leader cố định trong lượt. Trả về số lần dùng mỗi nhánh."""
    counts = {"encircle": 0, "search": 0, "spiral": 0}
    for i in range(len(population)):
        new, branch = update_whale(i, population, leader, a, a2, rng, l_mode, aux_rng, b)
        population[i] = new
        counts[branch] += 1
    return counts
 
 
#Test
def _run(mode, seed, lb, ub, f, N=25, T=100):
    main, aux = make_rngs(seed)
    pop = init_population(N, lb, ub, rng=main)
    leader, counts_log = None, []
    for t in range(T):
        repair_population(pop, lb, ub, "clip")
        best = min(pop, key=f)
        if leader is None or f(best) < f(leader):
            leader = list(best)
        a, a2 = 2.0 * (1 - t / T), -1.0 - t / T
        counts_log.append(update_population(pop, leader, a, a2, main, mode, aux))
    repair_population(pop, lb, ub, "clip")
    best = min(pop, key=f)
    return (best if f(best) < f(leader) else leader), counts_log
 
 
if __name__ == "__main__":
    rng = random.Random(1)
    lb, ub = [-100.0] * 30, [100.0] * 30
    pop = init_population(20, lb, ub, seed=3)
    assert all(lb[j] <= w[j] <= ub[j] for w in pop for j in range(30))
    assert any(v < 0 for w in pop for v in w) and pop == init_population(20, lb, ub, seed=3)
    print("[OK] init: trong biên âm/dương, cùng seed cho cùng đàn")
 
    x = [-150.0, 0.0, 150.0]
    assert repair_boundary(x, [-100] * 3, [100] * 3, "clip") == [-100.0, 0.0, 100.0]
    r = repair_boundary(x, [-100] * 3, [100] * 3, "reinit", rng)
    assert r[1] == 0.0 and all(-100 <= v <= 100 for v in r)
    print("[OK] clip và reinit chỉ đổi ô vượt biên")
 
    assert encircle_prey([3.0], [5.0], 0.5, 1.0) == [4.0]
    assert spiral_update([3.0], [5.0], [0.0]) == [7.0]
    print("[OK] công thức bao vây, xoắn khớp tính tay")
 
    m, au = make_rngs(5)
    ls, li = draw_l(-1.5, m, "shared_l"), draw_l(-1.5, m, "independent_l", 30, au)
    assert len(set(ls)) == 1 and len(set(li)) > 1 and all(-1.5 <= v <= 1.0 for v in ls + li)
    print("[OK] l nằm trong [a2, 1]; shared 1 giá trị, independent 30 giá trị")
 
    f = lambda v: sum(t * t for t in v)
    res = {m: _run(m, 11, lb, ub, f) for m in L_MODES}
    assert res["shared_l"][1] == res["independent_l"][1]
    print("[OK] luồng chính trùng: số lần dùng mỗi nhánh giống hệt giữa hai chế độ")
    for m in L_MODES:
        print(f"     {m}: f = {f(res[m][0]):.4f}")
 