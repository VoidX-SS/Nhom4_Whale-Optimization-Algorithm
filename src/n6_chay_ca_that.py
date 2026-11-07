"""
n6_chay_ca_that.py - chạy hàm woa chung của N6 trên ca thật của nhóm.

Chạy từ THƯ MỤC GỐC của repo (không phải trong src):
    python -m src.n6_chay_ca_that khe_hep

Cần có sẵn trong repo: src/n3_phuc_khang_danh_gia.py (N3) và src/n4_hoang_yen_du_lieu.py (N4).
Bản dự phòng default_init, default_bounds, default_update vẫn được dùng cho đến khi có hàm của N5.
"""
import sys

import numpy as np

from src.n3_phuc_khang_danh_gia import evaluate
from src.n4_hoang_yen_du_lieu import load_problem
from src.n6_van_lam_woa import woa, save_history_csv


def main(name="khe_hep", n_whales=30, n_iter=200, seed=1):
    problem = load_problem(name)

    # 30 biến theo thứ tự (x1, y1, pin1, ..., x10, y10, pin10): x, y trong [0,100], pin trong [0,25]
    lower = np.array([0.0, 0.0, 0.0] * 10)
    upper = np.array([100.0, 100.0, 25.0] * 10)

    # evaluate của N3 nhận (whale, problem), còn woa chỉ gọi evaluate(x) nên phải bọc lại
    res = woa(lambda x: evaluate(x, problem), lower, upper,
              n_whales=n_whales, n_iter=n_iter, seed=seed, snapshot_every=20)

    print("Ca:", name, "| N =", n_whales, "| T =", n_iter, "| seed =", seed)
    print("Số lần chấm:", res["n_evaluations"], "(N*T =", n_whales * n_iter, ")")
    for key in ("best_overall", "best_valid", "best_gate"):
        e = res[key]
        if e is None:
            print(key, "-> chưa có nghiệm hợp lệ")      # không ghi "vô nghiệm"
        else:
            print(key, "-> score J = %.4f, base_score f0 = %.4f (lượt %d, cá voi %d)"
                  % (e["score"], e["base_score"], e["iteration"], e["whale"]))

    save_history_csv(res, "results/n6_%s_history.csv" % name)
    print("Đã ghi results/n6_%s_history.csv" % name)
    return res


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "khe_hep")
