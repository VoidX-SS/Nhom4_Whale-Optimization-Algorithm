"""N6 Vân Lâm: lõi WOA có sổ nghiệm, history và snapshot toàn đàn."""
import csv
import math
import os
import numpy as np


def default_init(rng, n_whales, lower, upper):
    return lower + rng.random((n_whales, len(lower))) * (upper - lower)


def default_bounds(pop, lower, upper):
    return np.clip(pop, lower, upper)


def default_update(pop, leader, a, a2, rng, b=1.0):
    new_pop = pop.copy()
    for i in range(len(pop)):
        whale = pop[i]
        A = 2 * a * rng.random() - a
        C = 2 * rng.random()
        ell = (a2 - 1) * rng.random() + 1
        p = rng.random()
        if p < 0.5:
            if abs(A) >= 1:
                other = pop[rng.integers(len(pop))]
                new_pop[i] = other - A * np.abs(C * other - whale)
            else:
                new_pop[i] = leader - A * np.abs(C * leader - whale)
        else:
            d = np.abs(leader - whale)
            new_pop[i] = d * math.exp(b * ell) * math.cos(2 * math.pi * ell) + leader
    return new_pop


def to_record(out):
    return {"score": float(out["score"]), "base_score": float(out["base_score"]),
            "valid": bool(out["valid"]), "through_gate": bool(out.get("through_gate", False))}


def make_entry(x, rec, iteration, whale):
    entry = dict(rec)
    entry.update({"x": x.copy(), "iteration": iteration, "whale": whale})
    return entry


def update_ledgers(ledgers, pop, recs, iteration):
    for i, (x, r) in enumerate(zip(pop, recs)):
        old = ledgers["best_overall"]
        if old is None or r["score"] < old["score"]:
            ledgers["best_overall"] = make_entry(x, r, iteration, i)
        if r["valid"]:
            old = ledgers["best_valid"]
            if old is None or r["base_score"] < old["base_score"]:
                ledgers["best_valid"] = make_entry(x, r, iteration, i)
        if r["valid"] and r["through_gate"]:
            old = ledgers["best_gate"]
            if old is None or r["base_score"] < old["base_score"]:
                ledgers["best_gate"] = make_entry(x, r, iteration, i)


def take_snapshot(iteration, pop, recs):
    return {"iteration": iteration, "population": pop.copy(),
            "score": np.array([r["score"] for r in recs]),
            "base_score": np.array([r["base_score"] for r in recs]),
            "valid": np.array([r["valid"] for r in recs]),
            "through_gate": np.array([r["through_gate"] for r in recs])}


def check_population(snap, n_whales, lower, upper):
    p = snap["population"]
    assert p.shape == (n_whales, len(lower)), "Đàn không đủ N cá voi"
    assert np.all(np.isfinite(p)), "Đàn có NaN hoặc vô cực"
    assert np.all(p >= lower - 1e-9) and np.all(p <= upper + 1e-9), "Đàn vượt biên"
    for key in ("score", "base_score", "valid", "through_gate"):
        assert len(snap[key]) == n_whales, "Thiếu dữ liệu " + key


def linear_a(k, n_iter):
    return 2 - 2 * k / n_iter


def author_a2(k, n_iter):
    return -1 - k / n_iter


def woa(evaluate, lower, upper, n_whales, n_iter, seed=0, snapshot_every=10, b=1.0,
        init_fn=None, update_fn=None, bounds_fn=None, a_fn=None, a2_fn=None):
    """Mỗi lượt chấm N cá voi; tổng số lần chấm đúng N*T. Lượt đầu chấm đàn khởi tạo."""
    if n_whales < 2 or n_iter < 2:
        raise ValueError("n_whales phải >=2 và n_iter phải >=2")
    init_fn = init_fn or default_init
    update_fn = update_fn or default_update
    bounds_fn = bounds_fn or default_bounds
    a_fn = a_fn or linear_a
    a2_fn = a2_fn or author_a2
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    rng = np.random.default_rng(seed)
    ledgers = {"best_overall": None, "best_valid": None, "best_gate": None}
    history, snapshots = [], []
    n_evaluations = 0
    pop = init_fn(rng, n_whales, lower, upper)
    recs = None
    for t in range(1, n_iter + 1):
        a = a2 = None
        if t > 1:
            k = t - 2
            a, a2 = a_fn(k, n_iter), a2_fn(k, n_iter)
            leader = ledgers["best_overall"]["x"].copy()
            pop = update_fn(pop.copy(), leader, a, a2, rng, b)
        pop = bounds_fn(np.asarray(pop, dtype=float), lower, upper)
        recs = [to_record(evaluate(whale.copy())) for whale in pop]
        n_evaluations += n_whales
        update_ledgers(ledgers, pop, recs, t)
        bo, bv, bg = ledgers["best_overall"], ledgers["best_valid"], ledgers["best_gate"]
        history.append({"iteration": t, "a": a, "a2": a2,
                        "best_overall_score": bo["score"],
                        "best_valid_base": None if bv is None else bv["base_score"],
                        "best_gate_base": None if bg is None else bg["base_score"],
                        "mean_score": float(np.mean([r["score"] for r in recs])),
                        "n_valid": sum(r["valid"] for r in recs),
                        "n_gate": sum(r["through_gate"] for r in recs),
                        "n_evaluations": n_evaluations})
        if t == 1 or t == n_iter or t % snapshot_every == 0:
            snapshots.append(take_snapshot(t, pop, recs))
    final_population = take_snapshot(n_iter, pop, recs)
    check_population(final_population, n_whales, lower, upper)
    assert n_evaluations == n_whales * n_iter
    result = dict(ledgers)
    result.update({"history": history, "snapshots": snapshots,
                   "final_population": final_population, "n_evaluations": n_evaluations})
    return result


def save_history_csv(result, path):
    rows = result["history"]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def toy_evaluate(x):
    base = float(np.sum(x ** 2))
    violation = max(0.0, 1.0 - x[0])
    valid = violation == 0.0
    return {"score": base + 100.0 * violation, "base_score": base,
            "valid": valid, "through_gate": valid and abs(x[1]) <= 2.0}


if __name__ == "__main__":
    n, t, dim = 30, 200, 30
    result = woa(toy_evaluate, np.full(dim, -5.0), np.full(dim, 5.0), n, t,
                 seed=1, snapshot_every=50)
    print("Số lần chấm:", result["n_evaluations"], "(N*T =", n * t, ")")
