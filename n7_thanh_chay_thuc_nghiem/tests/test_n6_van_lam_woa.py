"""Kiểm thử lõi N6 theo các điều kiện của PR #15."""
import math
import numpy as np
from src.n6_van_lam_woa import woa, toy_evaluate

N, T, DIM = 12, 40, 5
LO, HI = np.full(DIM, -5.0), np.full(DIM, 5.0)


def make_logged(fn):
    log = []
    def ev(x):
        out = fn(x)
        log.append((x.copy(), dict(out)))
        return out
    return ev, log


def test_n6_all_contracts():
    ev, log = make_logged(toy_evaluate)
    r = woa(ev, LO, HI, N, T, seed=3, snapshot_every=10)
    assert len(log) == N * T == r["n_evaluations"]
    assert r["best_overall"]["score"] == min(o["score"] for _, o in log)
    assert r["best_valid"]["base_score"] == min(o["base_score"] for _, o in log if o["valid"])
    assert r["best_gate"]["base_score"] == min(o["base_score"] for _, o in log if o["valid"] and o["through_gate"])
    its = [s["iteration"] for s in r["snapshots"]]
    assert its[0] == 1 and its[-1] == T
    assert all(s["population"].shape == (N, DIM) for s in r["snapshots"])
    first_pop = np.array([x for x, _ in log[:N]])
    assert np.array_equal(r["snapshots"][0]["population"], first_pop)
    assert not np.array_equal(r["snapshots"][0]["population"], r["snapshots"][-1]["population"])
    r["best_overall"]["x"][:] = 0
    assert not np.all(r["snapshots"][-1]["population"] == 0)
    last_pop = np.array([x for x, _ in log[-N:]])
    assert np.array_equal(r["final_population"]["population"], last_pop)
    assert len(r["history"]) == T
    assert [h["n_evaluations"] for h in r["history"]] == [N * (i + 1) for i in range(T)]

    def never_valid(x):
        v = float(np.sum(x ** 2))
        return {"score": v, "base_score": v, "valid": False, "through_gate": False}
    r2 = woa(never_valid, LO, HI, N, T, seed=1)
    assert r2["best_valid"] is None and r2["best_gate"] is None and r2["best_overall"] is not None

    r3 = woa(toy_evaluate, LO, HI, N, T, seed=3, snapshot_every=10)
    r4 = woa(toy_evaluate, LO, HI, N, T, seed=3, snapshot_every=10)
    assert r3["best_overall"]["score"] == r4["best_overall"]["score"]

    def gate_but_not_valid(x):
        v = float(np.sum(x ** 2))
        return {"score": v, "base_score": v, "valid": False, "through_gate": True}
    r5 = woa(gate_but_not_valid, LO, HI, N, T, seed=1)
    assert r5["best_gate"] is None and r5["best_valid"] is None

    cos_a = lambda k, t: 1.0 + math.cos(math.pi * k / t)
    r6 = woa(toy_evaluate, LO, HI, N, T, seed=3, a_fn=cos_a)
    assert all(abs(h["a"] - cos_a(h["iteration"] - 2, T)) < 1e-12 for h in r6["history"][1:])
    r7 = woa(toy_evaluate, LO, HI, N, T, seed=3)
    assert all(abs(h["a"] - (2 - 2 * (h["iteration"] - 2) / T)) < 1e-12 for h in r7["history"][1:])
    assert r7["history"][1]["a"] == 2.0
    assert r7["history"][1]["a2"] == -1.0
    assert r7["best_overall"]["score"] == r3["best_overall"]["score"]
