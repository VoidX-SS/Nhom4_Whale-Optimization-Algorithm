"""
n6_kiem_nhung_K.py - N6 Vân Lâm, bước 5: kiểm nhúng nghiệm K6 vào K10.

Ý tưởng: một nghiệm K6 chỉ bật 6 đèn (6 đèn có pin cao nhất). Nếu cho pin của 4 đèn không
được chọn về 0 rồi chấm lại như K10 thì đường bay, tổng pin, U và base_score phải KHÔNG ĐỔI.
Nếu có chỗ đổi nghĩa là mô hình K6 và K10 chưa khớp nhau.

Mỗi seed chạy woa ở K nhỏ trên ca A, lấy best_valid của seed đó (nếu có) để kiểm nhúng.
Đây chỉ là bài kiểm chứng mô hình. KHÔNG đưa nghiệm đã nhúng vào đàn đo chính của K10.

File này không tự import code của người khác. Mọi thứ phụ thuộc vào N3 và N4 đi qua 2 hàm
bạn truyền vào:
  evaluate_K(vector, K) -> dict chuẩn gồm:
        score, base_score, valid, through_gate   (để chạy woa)
        path        : danh sách điểm (x, y) của đường bay đầy đủ (Start, các điểm, Goal)
        pin_total   : tổng pin các đèn đang bật
        U           : hữu dụng trung bình có trọng số
  active_fn(vector, K) -> danh sách chỉ số (0..9) các đèn được chọn khi giải mã top-K
"""
import csv
import os

SLOTS = 10
TOL = 1e-9


def nhung_vao_k_lon(vector, active_idx):
    """Cho pin các đèn KHÔNG được chọn về 0. Giữ nguyên toạ độ và pin các đèn được chọn."""
    out = [float(v) for v in vector]
    chon = set(active_idx)
    for i in range(SLOTS):
        if i not in chon:
            out[3 * i + 2] = 0.0
    return out


def so_sanh(goc, nhung, tol=TOL):
    """So kết quả chấm của nghiệm gốc (K nhỏ) với nghiệm đã nhúng (K lớn)."""
    path_same = len(goc["path"]) == len(nhung["path"]) and all(
        abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol
        for p, q in zip(goc["path"], nhung["path"]))
    d_pin = abs(goc["pin_total"] - nhung["pin_total"])
    d_u = abs(goc["U"] - nhung["U"])
    d_base = abs(goc["base_score"] - nhung["base_score"])
    ok = (path_same and d_pin <= tol and d_u <= tol and d_base <= tol
          and bool(goc["valid"]) == bool(nhung["valid"]))
    return {
        "path_same": path_same,
        "pin_total_goc": goc["pin_total"], "pin_total_nhung": nhung["pin_total"],
        "U_goc": goc["U"], "U_nhung": nhung["U"],
        "base_score_goc": goc["base_score"], "base_score_nhung": nhung["base_score"],
        "valid_goc": bool(goc["valid"]), "valid_nhung": bool(nhung["valid"]),
        "ok": ok,
    }


def kiem_nhung(solutions, evaluate_K, active_fn, k_goc=6, k_nhung=10, tol=TOL):
    """solutions: danh sách (tên, vector 30 số) của các nghiệm K nhỏ. Trả về danh sách dòng kết quả."""
    rows = []
    for ten, vec in solutions:
        goc = evaluate_K(vec, k_goc)
        vec_nhung = nhung_vao_k_lon(vec, active_fn(vec, k_goc))
        nhung = evaluate_K(vec_nhung, k_nhung)
        row = {"nghiem": ten, "k_goc": k_goc, "k_nhung": k_nhung}
        row.update(so_sanh(goc, nhung, tol))
        rows.append(row)
    return rows


def save_csv(rows, path):
    """Ghi results/K_embedding_check.csv."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def chay_kiem_nhung(woa_fn, evaluate_K, active_fn, lower, upper, n_whales=30, n_iter=800,
                    seeds=range(1, 31), k_goc=6, k_nhung=10, hooks_fn=None,
                    csv_path="results/K_embedding_check.csv"):
    """
    Với mỗi seed: chạy woa ở K nhỏ, lấy best_valid của seed đó, kiểm nhúng vào K lớn, ghi CSV.
    woa_fn   : hàm woa của N6.
    hooks_fn : tùy chọn, hooks_fn(seed) -> dict gồm init_fn, update_fn, bounds_fn (ví dụ từ
               make_woa_hooks của N5; phải tạo mới theo từng seed để luồng ngẫu nhiên phụ đúng seed).
    """
    solutions, khong_co = [], []
    for seed in seeds:
        kwargs = hooks_fn(seed) if hooks_fn else {}
        res = woa_fn(lambda x: evaluate_K(x, k_goc), lower, upper, n_whales, n_iter,
                     seed=seed, **kwargs)
        if res["best_valid"] is None:
            khong_co.append(seed)
        else:
            solutions.append(("seed_%d" % seed, [float(v) for v in res["best_valid"]["x"]]))

    tong = len(list(seeds))
    print("K = %d: %d/%d seed có nghiệm hợp lệ." % (k_goc, len(solutions), tong))
    if khong_co:
        print("Seed chưa có nghiệm hợp lệ (không phải vô nghiệm):", khong_co)
    if not solutions:
        return []

    rows = kiem_nhung(solutions, evaluate_K, active_fn, k_goc, k_nhung)
    save_csv(rows, csv_path)
    print("Kiểm nhúng K%d vào K%d: %d/%d nghiệm không đổi. Đã ghi %s"
          % (k_goc, k_nhung, sum(1 for r in rows if r["ok"]), len(rows), csv_path))
    return rows
