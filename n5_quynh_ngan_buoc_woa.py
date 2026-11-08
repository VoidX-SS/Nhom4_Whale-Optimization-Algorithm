
"""
Quy ước:
- Module chỉ di chuyển cá voi: không chấm điểm, không sửa bão, không sửa pin tổng.
- l (chữ thường) là số ngẫu nhiên của xoắn ốc, khác L là độ dài đường bay.
- Cập nhật TẠI CHỖ từng cá voi, không dùng bản chụp đàn cũ; leader cố định trong lượt.
- Sửa biên KHÔNG làm trong update_*; chỉ làm ở đầu lượt kế tiếp (repair_population).

Đối chiếu với WOA.m (kiểm lại số dòng khi rà với file thật):
    r1, r2, A = 2*a*r1 - a, C = 2*r2, l = (a2-1)*rand + 1, p = rand  -> update_whale
    |A| >= 1: chọn cá voi ngẫu nhiên theo từng chiều j               -> search_for_prey
    |A| <  1: D = |C*X*(j) - X(j)|, X(j) = X*(j) - A*D                -> encircle_prey
    p >= 0.5: X(j) = |X*(j)-X(j)| * exp(b*l) * cos(2*pi*l) + X*(j)    -> spiral_update
    kiểm biên ở đầu lượt                                              -> repair_population
"""

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

B_SPIRAL = 1.0
L_MODES = ("shared_l", "independent_l")
BOUNDARY_MODES = ("clip", "reinit")


def make_rngs(seed: int) -> Tuple[random.Random, random.Random]:
    """(rng chính, rng phụ).
    Rng chính: r1, r2, l, p, chọn cá voi tham khảo, re-init (giống hệt ở hai chế độ l).
    Rng phụ (luồng ngẫu nhiên phụ): chỉ sinh các l riêng của independent_l."""
    return random.Random(seed), random.Random(seed + 1_000_003)


# BƯỚC 1. KHỞI TẠO
def initialize_population(
    pop_size: int, lb: Sequence[float], ub: Sequence[float],
    rng: Optional[random.Random] = None, seed: Optional[int] = None,
) -> List[List[float]]:
    """N cá voi, mỗi chiều ngẫu nhiên đều trong [lb[j], ub[j]]. lb, ub có thể âm."""
    if len(lb) != len(ub) or any(lo > hi for lo, hi in zip(lb, ub)):
        raise ValueError("lb, ub phải cùng độ dài và lb <= ub.")
    rng = rng or random.Random(seed)
    return [[lb[j] + rng.random() * (ub[j] - lb[j]) for j in range(len(lb))]
            for _ in range(pop_size)]


# SỬA BIÊN (chỉ đụng ô vượt giới hạn)
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


# BƯỚC 2-3. NHÁNH
def encircle_prey(x, leader, A: float, C: float) -> List[float]:
    """|A| < 1: D = |C.X* - X| theo từng chiều; X' = X* - A.D."""
    return [leader[j] - A * abs(C * leader[j] - x[j]) for j in range(len(x))]


def search_for_prey(x, population, A: float, C: float, rng: random.Random) -> List[float]:
    """|A| >= 1: cá voi tham khảo chọn riêng cho từng chiều; D = |C.Xrand - X|; X' = Xrand - A.D."""
    n = len(population)
    out = []
    for j in range(len(x)):
        x_rand = population[rng.randrange(n)][j]
        out.append(x_rand - A * abs(C * x_rand - x[j]))
    return out


def spiral_update(x, leader, l_values: Sequence[float], b: float = B_SPIRAL) -> List[float]:
    """p >= 0.5: X' = |X* - X| . e^(b.l) . cos(2.pi.l) + X*  (b = 1)."""
    return [abs(leader[j] - x[j]) * math.exp(b * l_values[j]) * math.cos(2.0 * math.pi * l_values[j])
            + leader[j] for j in range(len(x))]


# BƯỚC 5. NGÁCH shared_l 
def draw_l(a2: float, rng: random.Random, mode: str = "shared_l",
           dim: int = 30, aux_rng: Optional[random.Random] = None) -> List[float]:
    """l = 1 + (a2 - 1) * rand, với a2 = -1 - t/T. Luôn rút 1 số từ rng chính (đúng thứ tự WOA.m).
    shared_l: dùng số đó cho mọi chiều (đúng mã tác giả).
    independent_l: bỏ số đó, rút `dim` số l riêng từ aux_rng (luồng ngẫu nhiên phụ)."""
    l0 = 1.0 + (a2 - 1.0) * rng.random()
    if mode == "shared_l":
        return [l0] * dim
    if mode == "independent_l":
        if aux_rng is None:
            raise ValueError("independent_l cần aux_rng (xem make_rngs).")
        return [1.0 + (a2 - 1.0) * aux_rng.random() for _ in range(dim)]
    raise ValueError(f"l_mode phải thuộc {L_MODES}, nhận '{mode}'.")


# CẬP NHẬT
def update_whale(i, population, leader, a: float, a2: float, rng: random.Random,
                 l_mode: str = "shared_l", aux_rng: Optional[random.Random] = None,
                 b: float = B_SPIRAL) -> Tuple[List[float], str]:
    """Thứ tự sinh số như WOA.m: r1, r2, l, p. Trả về (vị trí mới, tên nhánh)."""
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


# BƯỚC 6. VÍ DỤ SỐ ĐI QUA ĐỦ BA NHÁNH
class _ScriptedRng:
    """Bộ sinh số có kịch bản, để ví dụ tính tay lặp lại được từng con số."""
    def __init__(self, randoms, indices=()):
        self.r, self.i = list(randoms), list(indices)
    def random(self):
        return self.r.pop(0)
    def randrange(self, n):
        return self.i.pop(0)


def vi_du_so() -> None:
    """Đàn 3 cá voi, 2 chiều. Cá voi 0 X=(3,4); leader X*=(5,2); T=100.
    Thứ tự số ngẫu nhiên mỗi cá voi: r1, r2, l, p."""
    pop = [[3.0, 4.0], [7.0, 9.0], [8.0, 1.0]]
    leader = [5.0, 2.0]
    close = lambda u, v: all(abs(p - q) < 1e-9 for p, q in zip(u, v))
    f = math.exp(-0.5)   # e^(b.l) với b = 1, l = -0.5; cos(2.pi.l) = cos(-pi) = -1

    print("\nVÍ DỤ SỐ: X = (3, 4), X* = (5, 2), b = 1")
    print("-" * 78)
    rows = []

    # Nhánh 1: t = 50 -> a = 1.0, r1 = 0.75 -> A = 0.5; r2 = 0.5 -> C = 1; p = 0.3 < 0.5, |A| < 1
    # D = (|1*5-3|, |1*2-4|) = (2, 2); X' = (5-0.5*2, 2-0.5*2) = (4, 1)
    new, br = update_whale(0, pop, leader, 1.0, -1.5, _ScriptedRng([0.75, 0.5, 0.6, 0.3]))
    assert br == "encircle" and close(new, [4.0, 1.0])
    rows.append(("1 Bao vây", "(4, 1)", new))

    # Nhánh 2: t = 25 -> a = 1.5, r1 = 0.9 -> A = 1.2; C = 1; p = 0.3, |A| >= 1
    # Tham khảo: chiều 0 lấy cá voi 1 (7), chiều 1 lấy cá voi 2 (1)
    # D = (|7-3|, |1-4|) = (4, 3); X' = (7-1.2*4, 1-1.2*3) = (2.2, -2.6)
    new, br = update_whale(0, pop, leader, 1.5, -1.25,
                           _ScriptedRng([0.9, 0.5, 0.6, 0.3], indices=[1, 2]))
    assert br == "search" and close(new, [2.2, -2.6])
    rows.append(("2 Tham khảo", "(2.2, -2.6)", new))

    # Nhánh 3 (shared_l): t = 50 -> a2 = -1.5; rand = 0.6 -> l = 1 + (-2.5)*0.6 = -0.5; p = 0.7
    # D' = (2, 2); hệ số = e^-0.5 * cos(-pi) = -0.60653; X' = (2*(-0.60653)+5, 2*(-0.60653)+2)
    new, br = update_whale(0, pop, leader, 1.0, -1.5, _ScriptedRng([0.75, 0.5, 0.6, 0.7]))
    exp3 = [-2 * f + 5, -2 * f + 2]
    assert br == "spiral" and close(new, exp3)
    rows.append(("3 Xoắn shared_l", "(3.7869, 0.7869)", new))

    # Nhánh 3 (independent_l): l riêng = (-0.5, 0.0) vì rand phụ = (0.6, 0.4)
    # chiều 1: l = 0 -> hệ số = e^0 * cos(0) = 1 -> X'(1) = 2*1+2 = 4
    new, br = update_whale(0, pop, leader, 1.0, -1.5, _ScriptedRng([0.75, 0.5, 0.6, 0.7]),
                           "independent_l", _ScriptedRng([0.6, 0.4]))
    assert br == "spiral" and close(new, [-2 * f + 5, 4.0])
    rows.append(("3 Xoắn independent_l", "(3.7869, 4)", new))

    print(f"{'Nhánh':<24}{'Tính tay':<20}{'Code'}")
    for name, hand, got in rows:
        print(f"{name:<24}{hand:<20}({got[0]:.4f}, {got[1]:.4f})")
    print("-" * 78)
    print("[OK] ví dụ số: code khớp tính tay ở cả ba nhánh và cả hai chế độ l")


# CẦU NỐI VỚI woa() CỦA N6
class _GeneratorAdapter:
    """Cho numpy Generator của N6 nói cùng "ngôn ngữ" với lõi (random, randrange)."""
    def __init__(self, gen):
        self.gen = gen
    def random(self):
        return float(self.gen.random())
    def randrange(self, n):
        return int(self.gen.integers(n))


def make_woa_hooks(l_mode: str = "shared_l", boundary_mode: str = "clip", seed: int = 0):
    """Trả về (init_fn, update_fn, bounds_fn) đúng chữ ký hook của woa() N6:
        init_fn(rng, n_whales, lower, upper) -> mảng (N, dim)
        update_fn(pop, leader, a, a2, rng, b) -> mảng (N, dim)   (pop là bản copy của N6)
        bounds_fn(pop, lower, upper)          -> mảng (N, dim)
    Luồng ngẫu nhiên phụ của independent_l và luồng re-init được đặt lại mỗi lần woa()
    gọi init_fn, nên chạy lại cùng seed cho cùng kết quả. Luồng chính vẫn là rng của woa()."""
    import numpy as np
    if l_mode not in L_MODES:
        raise ValueError(f"l_mode phải thuộc {L_MODES}, nhận '{l_mode}'.")
    if boundary_mode not in BOUNDARY_MODES:
        raise ValueError(f"boundary_mode phải thuộc {BOUNDARY_MODES}, nhận '{boundary_mode}'.")
    streams = {}

    def _reset():
        streams["aux"] = _GeneratorAdapter(np.random.default_rng(seed + 1_000_003))
        streams["fix"] = _GeneratorAdapter(np.random.default_rng(seed + 2_000_029))

    _reset()

    def init_fn(rng, n_whales, lower, upper):
        _reset()
        return np.array(initialize_population(
            n_whales, list(map(float, lower)), list(map(float, upper)), rng=_GeneratorAdapter(rng)))

    def update_fn(pop, leader, a, a2, rng, b=B_SPIRAL):
        work = np.asarray(pop, dtype=float).tolist()
        update_population(work, np.asarray(leader, dtype=float).tolist(), a, a2,
                          _GeneratorAdapter(rng), l_mode, streams["aux"], b)
        return np.array(work)

    def bounds_fn(pop, lower, upper):
        work = np.asarray(pop, dtype=float).tolist()
        repair_population(work, list(map(float, lower)), list(map(float, upper)),
                          boundary_mode, streams["fix"])
        return np.array(work)

    return init_fn, update_fn, bounds_fn


def demo_tich_hop() -> None:
    """Chạy woa() thật của N6 với hook của N5, hai chế độ l. Bài toán giả toy_evaluate của N6."""
    try:
        import numpy as np
        from n6_van_lam_woa import woa, toy_evaluate, default_init
    except ImportError as err:
        print(f"[BỎ QUA] tích hợp N6: chưa có n6_van_lam_woa hoặc numpy ({err}).")
        return
    N, T, DIM, seed = 30, 100, 30, 1
    lower, upper = np.full(DIM, -5.0), np.full(DIM, 5.0)

    init_fn, _, _ = make_woa_hooks(seed=seed)
    same = np.allclose(init_fn(np.random.default_rng(seed), N, lower, upper),
                       default_init(np.random.default_rng(seed), N, lower, upper))
    assert same
    print("[OK] tích hợp: khởi tạo của N5 trùng bản dự phòng của N6 (cùng seed)")

    print("\nTÍCH HỢP woa() CỦA N6 (bài giả toy_evaluate, N=30, T=100)")
    for md in L_MODES:
        hooks = make_woa_hooks(md, "clip", seed)
        kw = dict(seed=seed, snapshot_every=50, init_fn=hooks[0], update_fn=hooks[1], bounds_fn=hooks[2])
        r1 = woa(toy_evaluate, lower, upper, N, T, **kw)
        r2 = woa(toy_evaluate, lower, upper, N, T, **kw)
        assert r1["n_evaluations"] == N * T
        assert r1["best_overall"]["score"] == r2["best_overall"]["score"]
        bv = r1["best_valid"]
        print(f"  {md:<14} số lần chấm = {r1['n_evaluations']}, best_overall = "
              f"{r1['best_overall']['score']:.6f}, best_valid = "
              f"{'chưa có' if bv is None else format(bv['base_score'], '.6f')}")
    print("[OK] tích hợp: chạy đủ N*T lần chấm, đàn trong biên, chạy lại cùng seed cho cùng kết quả")


# TỰ KIỂM TRA
def _run(mode, seed, lb, ub, f, N=25, T=100):
    main, aux = make_rngs(seed)
    pop = initialize_population(N, lb, ub, rng=main)
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
    lb, ub = [-100.0] * 30, [100.0] * 30
    pop = initialize_population(20, lb, ub, seed=3)
    assert all(lb[j] <= w[j] <= ub[j] for w in pop for j in range(30))
    assert any(v < 0 for w in pop for v in w) and pop == initialize_population(20, lb, ub, seed=3)
    print("[OK] khởi tạo: trong biên có giá trị âm, cùng seed cho cùng đàn")

    x = [-150.0, 0.0, 150.0]
    assert repair_boundary(x, [-100] * 3, [100] * 3, "clip") == [-100.0, 0.0, 100.0]
    r = repair_boundary(x, [-100] * 3, [100] * 3, "reinit", random.Random(1))
    assert r[1] == 0.0 and all(-100 <= v <= 100 for v in r)
    print("[OK] clip và reinit chỉ đổi ô vượt biên")

    m, au = make_rngs(5)
    ls, li = draw_l(-1.5, m, "shared_l"), draw_l(-1.5, m, "independent_l", 30, au)
    assert len(set(ls)) == 1 and len(set(li)) > 1 and all(-1.5 <= v <= 1.0 for v in ls + li)
    print("[OK] l nằm trong [a2, 1]; shared 1 giá trị, independent 30 giá trị")

    sphere = lambda v: sum(t * t for t in v)
    res = {md: _run(md, 11, lb, ub, sphere) for md in L_MODES}
    assert res["shared_l"][1] == res["independent_l"][1]
    print("[OK] luồng chính trùng: số lần dùng mỗi nhánh giống hệt giữa hai chế độ l")
    for md in L_MODES:
        print(f"     {md}: f = {sphere(res[md][0]):.4f}")

    vi_du_so()
    demo_tich_hop()
