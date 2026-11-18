"""Vân Lâm: vòng lặp bám WOA.m, thêm sổ hợp lệ và ảnh cả đàn.

T lượt chấm đàn, mỗi lượt N phương án: tổng cộng N*T lần chấm.
Những sổ và ảnh là phần ghi nhận, không đổi phương trình dẫn đàn.
"""
import copy
import random
import time
from src.n4_hoang_yen_du_lieu import bounds, a_value, validate_inputs
from src.n5_quynh_ngan_buoc_woa import initialize_population, repair_population, update_population


def woa(evaluate, problem, settings, keep_populations=False, on_snapshot=None):
    validate_inputs(problem, settings)
    started = time.perf_counter()
    rng = random.Random(settings["seed"])
    boundary_rng = random.Random(settings["seed"] + 1000003)
    l_rng = random.Random(settings["seed"] + 2000003)
    lower, upper = bounds(problem)
    population = initialize_population(settings["population"], lower, upper, rng)
    best_overall = None
    best_valid = None
    best_gate = None
    first_valid = None
    history = []
    snapshots = []
    totals = {"search": 0, "encircle": 0, "spiral": 0, "boundary_changes": 0}
    total = settings["iterations"]

    for t in range(total):
        totals["boundary_changes"] += repair_population(population, lower, upper, settings["boundary"], boundary_rng)
        valid_in_population = 0
        for whale in population:
            report = evaluate(whale, problem)
            if best_overall is None or report["score"] < best_overall["evaluation"]["score"]:
                best_overall = {"position": whale.copy(), "evaluation": report}
            if report["valid"]:
                valid_in_population += 1
                if first_valid is None:
                    first_valid = t
                if best_valid is None or report["base_score"] < best_valid["evaluation"]["base_score"]:
                    best_valid = {"position": whale.copy(), "evaluation": report}
                if report.get("through_gate", False):
                    if best_gate is None or report["base_score"] < best_gate["evaluation"]["base_score"]:
                        best_gate = {"position": whale.copy(), "evaluation": report}

        row = {"iteration": t, "evaluations": (t + 1) * settings["population"],
               "best_score": best_overall["evaluation"]["score"],
               "valid_found": best_valid is not None, "utility_sat": None,
               "valid_in_population": valid_in_population}
        if best_valid is not None:
            row["utility_sat"] = best_valid["evaluation"].get("utility_sat")
        history.append(row)
        if (keep_populations or on_snapshot is not None) and (t % settings["snapshot_every"] == 0 or t == total - 1):
            chosen = best_valid
            if chosen is None:
                chosen = best_overall
            snapshot = {"iteration": t, "population": copy.deepcopy(population),
                        "position": chosen["position"].copy(), "valid": best_valid is not None,
                        "overall_position": best_overall["position"].copy()}
            if keep_populations:
                snapshots.append(snapshot)
            if on_snapshot is not None:
                # Chỉ gửi một ảnh chụp cho giao diện; không nhờ nó sửa đàn.
                on_snapshot(snapshot, best_overall, best_valid)
        if t == total - 1:
            final_population = copy.deepcopy(population)

        a = a_value(t, total, settings["a_mode"])
        a2 = -1 - t / total
        counts = update_population(population, best_overall["position"], a, a2, settings, rng, l_rng)
        for key in counts:
            totals[key] += counts[key]
    # Giống WOA.m: bước sửa cuối chưa được chấm; snapshot cuối là đàn
    # đã CHẤM, không đem đàn mới chưa kiểm tra ra làm kết quả.
    return {"problem": copy.deepcopy(problem), "settings": settings.copy(),
            "best_overall": best_overall, "best_valid": best_valid,
            "best_gate": best_gate,
            "first_valid_iteration": first_valid, "history": history,
            "snapshots": snapshots, "counts": totals,
            "final_population": final_population,
            "evaluations": total * settings["population"],
            "elapsed_seconds": time.perf_counter() - started,
            "core_version": "matlab-author-translation-v2"}
