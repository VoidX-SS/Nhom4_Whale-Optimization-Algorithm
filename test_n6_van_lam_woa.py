"""Kiểm các điều kiện đóng Issue của N6. Chạy: python src/test_n6_van_lam_woa.py"""
import numpy as np
from n6_van_lam_woa import woa

N, T, DIM = 12, 40, 5
LO, HI = np.full(DIM, -5.0), np.full(DIM, 5.0)


def make_logged(fn):
    log = []

    def ev(x):
        out = fn(x)
        log.append((x.copy(), dict(out)))
        return out
    return ev, log


def toy(x):
    base = float(np.sum(x ** 2))
    viol = max(0.0, 1.0 - x[0])
    ok = viol == 0.0
    return {"score": base + 50 * viol, "base_score": base, "valid": ok,
            "through_gate": ok and abs(x[1]) <= 2}


ev, log = make_logged(toy)
res = woa(ev, LO, HI, N, T, seed=3, snapshot_every=10)

# 1. đúng N*T lần chấm
assert len(log) == N * T == res["n_evaluations"]

# 2. best_overall = J thấp nhất trong mọi lần chấm
assert res["best_overall"]["score"] == min(o["score"] for _, o in log)

# 3. best_valid / best_gate = base_score thấp nhất trong nhóm đủ điều kiện
assert res["best_valid"]["base_score"] == min(o["base_score"] for _, o in log if o["valid"])
assert res["best_gate"]["base_score"] == min(o["base_score"] for _, o in log if o["through_gate"])

# 4. snapshot đủ N đường, lượt đầu và cuối đều có, và là bản sao (lượt 1 giữ nguyên đàn đầu)
its = [s["iteration"] for s in res["snapshots"]]
assert its[0] == 1 and its[-1] == T
assert all(s["population"].shape == (N, DIM) for s in res["snapshots"])
first_pop = np.array([x for x, _ in log[:N]])
assert np.array_equal(res["snapshots"][0]["population"], first_pop)
assert not np.array_equal(res["snapshots"][0]["population"], res["snapshots"][-1]["population"])

# 5. sổ lưu bản sao: sửa sổ không đụng snapshot và ngược lại
res["best_overall"]["x"][:] = 0
assert not np.all(res["snapshots"][-1]["population"] == 0)

# 6. final_population là đàn của lượt chấm cuối
last_pop = np.array([x for x, _ in log[-N:]])
assert np.array_equal(res["final_population"]["population"], last_pop)

# 7. history đủ T dòng, số lần chấm tăng đều
assert len(res["history"]) == T
assert [h["n_evaluations"] for h in res["history"]] == [N * (i + 1) for i in range(T)]

# 8. không có nghiệm hợp lệ thì best_valid/best_gate là None, best_overall vẫn có
def never_valid(x):
    return {"score": float(np.sum(x ** 2)), "base_score": float(np.sum(x ** 2)),
            "valid": False, "through_gate": False}


r2 = woa(never_valid, LO, HI, N, T, seed=1)
assert r2["best_valid"] is None and r2["best_gate"] is None and r2["best_overall"] is not None

# 9. cùng seed cho cùng kết quả (tái lập)
r3 = woa(toy, LO, HI, N, T, seed=3, snapshot_every=10)
r4 = woa(toy, LO, HI, N, T, seed=3, snapshot_every=10)
assert r3["best_overall"]["score"] == r4["best_overall"]["score"]

print("Tất cả 9 kiểm tra đều đạt")
