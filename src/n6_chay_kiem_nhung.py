"""
n6_chay_kiem_nhung.py - N6 Vân Lâm, bước 5: chạy kiểm nhúng K6 -> K10 trên ca A thật.

Chạy từ THƯ MỤC GỐC của repo:
    python -m src.n6_chay_kiem_nhung            # đủ: 30 seed, N = 30, T = 800
    python -m src.n6_chay_kiem_nhung 3 40       # chạy thử nhanh: 3 seed, T = 40

Dùng hàm chấm của Yến (evaluate_solution, decode_solution trong n4_hoang_yen_du_lieu.py)
nên KHÔNG cần file của Khang. Nếu có file của Ngân (n5_quynh_ngan_buoc_woa.py) thì dùng,
chưa có thì dùng bước cập nhật dự phòng trong n6_van_lam_woa.py (ghi rõ trong đầu ra).
Ghi: results/K_embedding_check.csv
"""
import sys

import numpy as np

from src.n4_hoang_yen_du_lieu import load_problem, evaluate_solution, decode_solution, get_bounds
from src.n6_van_lam_woa import woa
from src.n6_kiem_nhung_K import chay_kiem_nhung


def make_adapters(problem):
    """Đổi kết quả của Yến sang dạng woa và phép kiểm nhúng cần."""
    def evaluate_K(vec, K):
        r = evaluate_solution(list(vec), problem, K=K)
        d = r["decoded"]
        return {
            "score": r["J"], "base_score": r["f0"],
            "valid": r["is_valid"], "through_gate": r["is_gate_passed"],
            "path": d.full_path, "pin_total": sum(d.light_powers), "U": r["U"],
        }

    def active_fn(vec, K):
        return decode_solution(list(vec), K=K, problem=problem).active_light_indices

    return evaluate_K, active_fn


def main(n_seeds=30, n_iter=800, n_whales=30, case="A"):
    problem = load_problem(case)
    evaluate_K, active_fn = make_adapters(problem)
    lb, ub = get_bounds(30)
    lower, upper = np.array(lb), np.array(ub)

    try:
        from src.n5_quynh_ngan_buoc_woa import make_woa_hooks
        def hooks_fn(seed):
            init_fn, update_fn, bounds_fn = make_woa_hooks("shared_l", "clip", seed)
            return {"init_fn": init_fn, "update_fn": update_fn, "bounds_fn": bounds_fn}
        print("Dùng hàm cập nhật của N5 (Ngân).")
    except ImportError:
        hooks_fn = None
        print("CHƯA có file N5 trên src: dùng bước cập nhật dự phòng (chỉ để thử, chạy lại khi có N5).")

    return chay_kiem_nhung(woa, evaluate_K, active_fn, lower, upper,
                           n_whales=n_whales, n_iter=n_iter, seeds=range(1, n_seeds + 1),
                           k_goc=6, k_nhung=10, hooks_fn=hooks_fn,
                           csv_path="results/K_embedding_check.csv")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]) if a else 30, int(a[1]) if len(a) > 1 else 800)
