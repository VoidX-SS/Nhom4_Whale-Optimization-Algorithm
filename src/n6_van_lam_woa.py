"""
n6_van_lam_woa.py  -  N6 Vân Lâm (Nhóm 2)

Nhiệm vụ (bước 1-3, hạn 08/11):
  1. Ghép hàm woa chung: sửa biên -> chấm cả đàn -> cập nhật sổ -> a/a2 -> cập nhật vị trí,
     đúng thứ tự, tổng cộng N*T lần chấm.
  2. Lưu BẢN SAO cho 3 sổ: best_overall, best_valid, best_gate.
  3. Lưu history, snapshot cả N cá voi ở các mốc (kể cả lượt đầu/cuối) và final_population.

Hàm woa nhận 4 mảnh ghép từ người khác qua tham số, nên đổi tên module của N3/N5
không làm hỏng file này:
  evaluate(x)  (N3)  -> dict có 4 khóa: score, base_score, valid, through_gate
                        score      = J (đã cộng phạt), dùng để chọn best_overall
                        base_score = điểm gốc chưa phạt, dùng cho best_valid / best_gate
  init_fn      (N5)  -> khởi tạo đàn            (có bản dự phòng bên dưới)
  bounds_fn    (N5)  -> sửa biên                (có bản dự phòng bên dưới)
  update_fn    (N5)  -> ba nhánh cập nhật WOA   (có bản dự phòng bên dưới)

Các bản dự phòng chỉ để file chạy độc lập; khi ghép nhóm thì truyền hàm thật của N5.
Nếu evaluate của N3 đặt tên khóa khác, chỉ cần sửa hàm _to_record.

Quy ước thứ tự (T lượt chấm, mỗi lượt chấm đúng N cá voi => N*T lần chấm):
  Lượt 1      : sửa biên đàn khởi tạo -> chấm -> cập nhật sổ -> lưu
  Lượt 2..T   : tính a, a2 -> cập nhật vị trí -> sửa biên -> chấm -> cập nhật sổ -> lưu
  Kết thúc ngay sau lượt chấm cuối, không có bước cập nhật thừa chưa được chấm.
  a(t) = 2 - 2t/T với t = 1..T-1 là số lần đã cập nhật; a2(t) = -1 - t/T.
  Chỉ best_overall dẫn đàn; best_valid và best_gate chỉ lưu bằng chứng.
"""
import csv
import math
import os

import numpy as np


# ---------------------------------------------------------------- bản dự phòng
def default_init(rng, n_whales, lower, upper):
    """Khởi tạo đàn ngẫu nhiên đều trong [lower, upper]."""
    return lower + rng.random((n_whales, len(lower))) * (upper - lower)


def default_bounds(pop, lower, upper):
    """Sửa biên bằng cách kẹp (clip) về [lower, upper]."""
    return np.clip(pop, lower, upper)


def default_update(pop, leader, a, a2, rng, b=1.0):
    """Ba nhánh WOA theo bài gốc (Mirjalili & Lewis, 2016); A, C là số vô hướng mỗi cá voi."""
    n = len(pop)
    new = pop.copy()
    for i in range(n):
        A = 2 * a * rng.random() - a
        C = 2 * rng.random()
        l = (a2 - 1) * rng.random() + 1
        if rng.random() < 0.5:
            if abs(A) >= 1:                      # khám phá: bám theo cá voi ngẫu nhiên
                x_rand = pop[rng.integers(n)]
                new[i] = x_rand - A * np.abs(C * x_rand - pop[i])
            else:                                # bao vây X*
                new[i] = leader - A * np.abs(C * leader - pop[i])
        else:                                    # xoắn ốc quanh X*
            new[i] = np.abs(leader - pop[i]) * math.exp(b * l) * math.cos(2 * math.pi * l) + leader
    return new


# ---------------------------------------------------------------- hàm phụ
def _to_record(out):
    """Chuẩn hóa kết quả evaluate của N3 về 4 khóa cố định."""
    return {
        "score": float(out["score"]),
        "base_score": float(out["base_score"]),
        "valid": bool(out["valid"]),
        "through_gate": bool(out["through_gate"]),
    }


def _entry(x, rec, iteration, whale):
    """Một dòng trong sổ. x được COPY nên đàn đổi sau đó cũng không làm đổi sổ."""
    e = dict(rec)
    e["x"] = np.array(x, dtype=float).copy()
    e["iteration"] = iteration
    e["whale"] = whale
    return e


def _update_ledgers(ledgers, pop, recs, iteration):
    """Cập nhật 3 sổ sau khi cả đàn ĐÃ được chấm. So sánh '<' nên hòa thì giữ bản có trước."""
    for i, (x, r) in enumerate(zip(pop, recs)):
        bo = ledgers["best_overall"]
        if bo is None or r["score"] < bo["score"]:
            ledgers["best_overall"] = _entry(x, r, iteration, i)
        if r["valid"]:
            bv = ledgers["best_valid"]
            if bv is None or r["base_score"] < bv["base_score"]:
                ledgers["best_valid"] = _entry(x, r, iteration, i)
        if r["through_gate"]:
            bg = ledgers["best_gate"]
            if bg is None or r["base_score"] < bg["base_score"]:
                ledgers["best_gate"] = _entry(x, r, iteration, i)


def _population_dict(iteration, pop, recs):
    """Ảnh chụp cả đàn: đủ N dòng, mọi mảng đều là bản sao."""
    return {
        "iteration": iteration,
        "population": np.array(pop, dtype=float).copy(),
        "score": np.array([r["score"] for r in recs]),
        "base_score": np.array([r["base_score"] for r in recs]),
        "valid": np.array([r["valid"] for r in recs]),
        "through_gate": np.array([r["through_gate"] for r in recs]),
    }


def check_population(snap, n_whales, lower, upper):
    """Kiểm final_population: đủ N, không NaN/inf, nằm trong biên. Sai thì báo lỗi."""
    p = snap["population"]
    assert p.shape == (n_whales, len(lower)), "Đàn không đủ N cá voi"
    assert np.all(np.isfinite(p)), "Đàn có NaN/inf"
    assert np.all(p >= lower - 1e-9) and np.all(p <= upper + 1e-9), "Đàn nằm ngoài biên"
    for k in ("score", "base_score", "valid", "through_gate"):
        assert len(snap[k]) == n_whales, "Thiếu kết quả chấm của " + k
    return True


# ---------------------------------------------------------------- hàm chính
def woa(evaluate, lower, upper, n_whales, n_iter, seed=0, snapshot_every=10, b=1.0,
        init_fn=None, update_fn=None, bounds_fn=None):
    """
    Chạy WOA, trả về dict:
      best_overall, best_valid, best_gate : dòng sổ (dict có x, score, base_score, ...) hoặc None
      history          : list n_iter dòng, mỗi lượt một dòng
      snapshots        : list ảnh chụp cả đàn ở lượt 1, mỗi snapshot_every lượt, và lượt cuối
      final_population : ảnh chụp đàn của lượt chấm cuối (đã qua check_population)
      n_evaluations    : đúng n_whales * n_iter
    """
    init_fn = init_fn or default_init
    update_fn = update_fn or default_update
    bounds_fn = bounds_fn or default_bounds
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    rng = np.random.default_rng(seed)

    ledgers = {"best_overall": None, "best_valid": None, "best_gate": None}
    history, snapshots = [], []
    n_eval = 0
    pop = init_fn(rng, n_whales, lower, upper)

    for t in range(1, n_iter + 1):
        # --- a, a2 và cập nhật vị trí (bỏ qua ở lượt 1: đàn vừa khởi tạo) ---
        a = a2 = None
        if t > 1:
            u = t - 1                                    # số lần đã cập nhật
            a = 2 - 2 * u / n_iter
            a2 = -1 - u / n_iter
            leader = ledgers["best_overall"]["x"].copy()  # chỉ best_overall dẫn đàn
            pop = update_fn(pop.copy(), leader, a, a2, rng, b)

        # --- sửa biên rồi mới chấm ---
        pop = bounds_fn(np.asarray(pop, dtype=float), lower, upper)

        # --- chấm cả đàn: đúng N lần ---
        recs = [_to_record(evaluate(x.copy())) for x in pop]
        n_eval += n_whales

        # --- cập nhật sổ chỉ SAU khi đã chấm ---
        _update_ledgers(ledgers, pop, recs, t)

        # --- history ---
        bo, bv, bg = ledgers["best_overall"], ledgers["best_valid"], ledgers["best_gate"]
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
            "n_evaluations": n_eval,
        })

        # --- snapshot ở lượt đầu, lượt cuối và mỗi snapshot_every lượt ---
        if t == 1 or t == n_iter or t % snapshot_every == 0:
            snapshots.append(_population_dict(t, pop, recs))

    final_population = _population_dict(n_iter, pop, recs)
    check_population(final_population, n_whales, lower, upper)
    assert n_eval == n_whales * n_iter, "Số lần chấm khác N*T"

    return {**ledgers, "history": history, "snapshots": snapshots,
            "final_population": final_population, "n_evaluations": n_eval}


def save_history_csv(result, path):
    """Ghi history ra CSV để đưa vào slide hoặc replay."""
    rows = result["history"]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- chạy thử
def _toy_evaluate(x):
    """BÀI TOÁN GIẢ chỉ để thử khung (KHÔNG phải bài UAV): 30 biến, tối ưu cho x0 >= 1.
    base_score = tổng bình phương; score = base + phạt; through_gate khi x0 hợp lệ và |x1| <= 2."""
    base = float(np.sum(x ** 2))
    viol = max(0.0, 1.0 - x[0])
    valid = viol == 0.0
    return {"score": base + 100.0 * viol, "base_score": base,
            "valid": valid, "through_gate": valid and abs(x[1]) <= 2.0}


if __name__ == "__main__":
    N, T, DIM = 30, 200, 30
    lo, hi = np.full(DIM, -5.0), np.full(DIM, 5.0)
    res = woa(_toy_evaluate, lo, hi, n_whales=N, n_iter=T, seed=1, snapshot_every=50)

    print("Số lần chấm:", res["n_evaluations"], "(N*T =", N * T, ")")
    print("Số dòng history:", len(res["history"]))
    print("Các lượt có snapshot:", [s["iteration"] for s in res["snapshots"]])
    print("Mỗi snapshot có", res["snapshots"][0]["population"].shape[0], "cá voi")
    for name in ("best_overall", "best_valid", "best_gate"):
        e = res[name]
        print(name, "->", "None" if e is None else
              "score=%.6f base=%.6f (lượt %d, cá voi %d)" % (e["score"], e["base_score"], e["iteration"], e["whale"]))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "n6_demo_history.csv")
    save_history_csv(res, out)
    print("Đã ghi", os.path.normpath(out))
