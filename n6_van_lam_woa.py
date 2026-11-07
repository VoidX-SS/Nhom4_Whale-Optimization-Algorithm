"""
n6_van_lam_woa.py - N6 Vân Lâm (Nhóm 2)

File này làm 3 việc:
  1. Chạy vòng lặp WOA chung (hàm woa).
  2. Giữ 3 "sổ" kết quả tốt nhất: best_overall, best_valid, best_gate.
  3. Lưu lại lịch sử (history), ảnh chụp cả đàn (snapshot) và đàn cuối (final_population).

Hàm woa cần 4 hàm do bạn khác viết, được truyền vào qua tham số:
  evaluate(x)  - N3 : chấm một cá voi, trả về dict có 4 khóa
                      score        : điểm J đã cộng phạt (dùng chọn best_overall)
                      base_score   : điểm gốc chưa phạt (dùng cho best_valid, best_gate)
                      valid        : True nếu cá voi hợp lệ
                      through_gate : True nếu cá voi qua cổng
  init_fn      - N5 : khởi tạo đàn
  bounds_fn    - N5 : sửa biên
  update_fn    - N5 : cập nhật vị trí theo 3 nhánh WOA
Nếu không truyền init_fn, bounds_fn, update_fn thì dùng bản dự phòng ngay bên dưới.
"""
import csv
import math
import os

import numpy as np


# ======================================================================
# PHẦN 1: BẢN DỰ PHÒNG (chỉ để file chạy được khi chưa có code của N5)
# ======================================================================
def default_init(rng, n_whales, lower, upper):
    """Tạo đàn ngẫu nhiên: mỗi cá voi là một hàng, mỗi biến nằm trong [lower, upper]."""
    return lower + rng.random((n_whales, len(lower))) * (upper - lower)


def default_bounds(pop, lower, upper):
    """Sửa biên: giá trị nào vượt biên thì kéo về sát biên."""
    return np.clip(pop, lower, upper)


def default_update(pop, leader, a, a2, rng, b=1.0):
    """Cập nhật vị trí theo 3 nhánh WOA (theo bài gốc của Mirjalili và Lewis)."""
    new_pop = pop.copy()
    for i in range(len(pop)):
        whale = pop[i]
        A = 2 * a * rng.random() - a          # hệ số A, nằm trong [-a, a]
        C = 2 * rng.random()                  # hệ số C, nằm trong [0, 2]
        l = (a2 - 1) * rng.random() + 1       # số ngẫu nhiên cho nhánh xoắn ốc
        p = rng.random()

        if p < 0.5:
            if abs(A) >= 1:
                # Nhánh khám phá: bám theo một cá voi ngẫu nhiên
                other = pop[rng.integers(len(pop))]
                new_pop[i] = other - A * np.abs(C * other - whale)
            else:
                # Nhánh bao vây: tiến lại gần cá voi tốt nhất
                new_pop[i] = leader - A * np.abs(C * leader - whale)
        else:
            # Nhánh xoắn ốc: bơi xoắn quanh cá voi tốt nhất
            d = np.abs(leader - whale)
            new_pop[i] = d * math.exp(b * l) * math.cos(2 * math.pi * l) + leader
    return new_pop


# ======================================================================
# PHẦN 2: CÁC HÀM NHỎ DÙNG TRONG VÒNG LẶP
# ======================================================================
def to_record(out):
    """Đổi kết quả evaluate về dạng chuẩn. Nếu N3 đặt tên khóa khác thì chỉ sửa ở đây."""
    return {
        "score": float(out["score"]),
        "base_score": float(out["base_score"]),
        "valid": bool(out["valid"]),
        "through_gate": bool(out["through_gate"]),
    }


def make_entry(x, rec, iteration, whale):
    """Tạo một dòng để ghi vào sổ. x được copy để đàn đổi sau này không làm đổi sổ."""
    entry = dict(rec)
    entry["x"] = x.copy()
    entry["iteration"] = iteration
    entry["whale"] = whale
    return entry


def update_ledgers(ledgers, pop, recs, iteration):
    """
    Cập nhật 3 sổ, gọi SAU KHI cả đàn đã được chấm.
      best_overall: J (score) thấp nhất, không cần hợp lệ
      best_valid  : base_score thấp nhất, chỉ xét cá voi valid
      best_gate   : base_score thấp nhất, chỉ xét cá voi through_gate
    Dùng dấu < nên nếu hòa điểm thì giữ dòng có trước.
    """
    for i in range(len(pop)):
        x, r = pop[i], recs[i]

        old = ledgers["best_overall"]
        if old is None or r["score"] < old["score"]:
            ledgers["best_overall"] = make_entry(x, r, iteration, i)

        if r["valid"]:
            old = ledgers["best_valid"]
            if old is None or r["base_score"] < old["base_score"]:
                ledgers["best_valid"] = make_entry(x, r, iteration, i)

        if r["through_gate"]:
            old = ledgers["best_gate"]
            if old is None or r["base_score"] < old["base_score"]:
                ledgers["best_gate"] = make_entry(x, r, iteration, i)


def take_snapshot(iteration, pop, recs):
    """Chụp lại cả đàn tại một lượt. Mọi mảng đều là bản copy."""
    return {
        "iteration": iteration,
        "population": pop.copy(),
        "score": np.array([r["score"] for r in recs]),
        "base_score": np.array([r["base_score"] for r in recs]),
        "valid": np.array([r["valid"] for r in recs]),
        "through_gate": np.array([r["through_gate"] for r in recs]),
    }


def check_population(snap, n_whales, lower, upper):
    """Kiểm đàn cuối: đủ N cá voi, không có số lỗi, không vượt biên. Sai thì báo lỗi."""
    p = snap["population"]
    assert p.shape == (n_whales, len(lower)), "Đàn không đủ N cá voi"
    assert np.all(np.isfinite(p)), "Đàn có số lỗi (NaN hoặc vô cực)"
    assert np.all(p >= lower - 1e-9) and np.all(p <= upper + 1e-9), "Đàn nằm ngoài biên"
    for key in ("score", "base_score", "valid", "through_gate"):
        assert len(snap[key]) == n_whales, "Thiếu kết quả chấm của " + key


# ======================================================================
# PHẦN 3: HÀM WOA CHÍNH
# ======================================================================
def woa(evaluate, lower, upper, n_whales, n_iter, seed=0, snapshot_every=10, b=1.0,
        init_fn=None, update_fn=None, bounds_fn=None):
    """
    Chạy WOA với n_whales cá voi trong n_iter lượt chấm (tổng N*T lần chấm).

    Mỗi lượt gồm các bước theo thứ tự:
      (từ lượt 2) tính a, a2  ->  cập nhật vị trí
      sửa biên  ->  chấm cả đàn  ->  cập nhật 3 sổ  ->  ghi history  ->  chụp snapshot
    Lượt 1 chấm luôn đàn vừa khởi tạo. Chạy xong lượt chấm cuối là dừng.

    Trả về dict gồm: best_overall, best_valid, best_gate, history, snapshots,
                     final_population, n_evaluations.
    """
    # Nếu không truyền hàm thì dùng bản dự phòng
    init_fn = init_fn or default_init
    update_fn = update_fn or default_update
    bounds_fn = bounds_fn or default_bounds

    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    rng = np.random.default_rng(seed)

    ledgers = {"best_overall": None, "best_valid": None, "best_gate": None}
    history = []
    snapshots = []
    n_evaluations = 0

    pop = init_fn(rng, n_whales, lower, upper)      # đàn ban đầu

    for t in range(1, n_iter + 1):

        # --- Bước 1: cập nhật vị trí (lượt 1 bỏ qua vì đàn vừa khởi tạo) ---
        a, a2 = None, None
        if t > 1:
            k = t - 1                                # đây là lần cập nhật thứ k
            a = 2 - 2 * k / n_iter                   # a giảm đều từ 2 về gần 0
            a2 = -1 - k / n_iter                     # a2 giảm đều từ -1 về -2
            leader = ledgers["best_overall"]["x"].copy()   # chỉ best_overall dẫn đàn
            pop = update_fn(pop.copy(), leader, a, a2, rng, b)

        # --- Bước 2: sửa biên rồi mới chấm ---
        pop = bounds_fn(np.asarray(pop, dtype=float), lower, upper)

        # --- Bước 3: chấm cả đàn, mỗi cá voi một lần ---
        recs = []
        for whale in pop:
            recs.append(to_record(evaluate(whale.copy())))
        n_evaluations += n_whales

        # --- Bước 4: cập nhật sổ (chỉ làm sau khi đã chấm xong) ---
        update_ledgers(ledgers, pop, recs, t)

        # --- Bước 5: ghi history của lượt này ---
        bo = ledgers["best_overall"]
        bv = ledgers["best_valid"]
        bg = ledgers["best_gate"]
        history.append({
            "iteration": t,
            "a": a,
            "a2": a2,
            "best_overall_score": bo["score"],
            "best_valid_base": None if bv is None else bv["base_score"],
            "best_gate_base": None if bg is None else bg["base_score"],
            "mean_score": float(np.mean([r["score"] for r in recs])),
            "n_valid": sum(r["valid"] for r in recs),
            "n_gate": sum(r["through_gate"] for r in recs),
            "n_evaluations": n_evaluations,
        })

        # --- Bước 6: chụp snapshot ở lượt đầu, lượt cuối và mỗi snapshot_every lượt ---
        if t == 1 or t == n_iter or t % snapshot_every == 0:
            snapshots.append(take_snapshot(t, pop, recs))

    # Đàn của lượt chấm cuối chính là final_population
    final_population = take_snapshot(n_iter, pop, recs)
    check_population(final_population, n_whales, lower, upper)
    assert n_evaluations == n_whales * n_iter, "Số lần chấm khác N*T"

    result = dict(ledgers)
    result["history"] = history
    result["snapshots"] = snapshots
    result["final_population"] = final_population
    result["n_evaluations"] = n_evaluations
    return result


def save_history_csv(result, path):
    """Ghi history ra file CSV để làm slide hoặc xem lại."""
    rows = result["history"]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ======================================================================
# PHẦN 4: CHẠY THỬ (python n6_van_lam_woa.py)
# ======================================================================
def toy_evaluate(x):
    """
    BÀI TOÁN GIẢ để thử khung, KHÔNG phải bài UAV.
    base_score = tổng bình phương các biến (càng nhỏ càng tốt).
    Ràng buộc: x[0] phải >= 1, vi phạm thì bị phạt 100 điểm cho mỗi đơn vị.
    Qua cổng: hợp lệ và |x[1]| <= 2.
    """
    base = float(np.sum(x ** 2))
    violation = max(0.0, 1.0 - x[0])
    valid = violation == 0.0
    return {
        "score": base + 100.0 * violation,
        "base_score": base,
        "valid": valid,
        "through_gate": valid and abs(x[1]) <= 2.0,
    }


if __name__ == "__main__":
    N, T, DIM = 30, 200, 30
    lower = np.full(DIM, -5.0)
    upper = np.full(DIM, 5.0)
    res = woa(toy_evaluate, lower, upper, n_whales=N, n_iter=T, seed=1, snapshot_every=50)

    print("Số lần chấm:", res["n_evaluations"], "(N*T =", N * T, ")")
    print("Số dòng history:", len(res["history"]))
    print("Các lượt có snapshot:", [s["iteration"] for s in res["snapshots"]])
    print("Mỗi snapshot có", res["snapshots"][0]["population"].shape[0], "cá voi")
    for name in ("best_overall", "best_valid", "best_gate"):
        e = res[name]
        if e is None:
            print(name, "-> None")
        else:
            print(name, "-> score=%.6f base=%.6f (lượt %d, cá voi %d)"
                  % (e["score"], e["base_score"], e["iteration"], e["whale"]))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "n6_demo_history.csv")
    save_history_csv(res, out)
    print("Đã ghi", os.path.normpath(out))
