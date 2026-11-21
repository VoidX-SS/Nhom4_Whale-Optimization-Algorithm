"""Tạo ảnh 16:9 và báo cáo ngoại tuyến: python tao_bao_cao.py

Phần ca gốc đứng trước; bốn ngách ở sau. Không chọn seed đẹp cho đối chứng.
"""
import html
import json
import math
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.n4_hoang_yen_du_lieu import ROOT
from src.n3_phuc_khang_danh_gia import evaluate
from src.n6_van_lam_woa import woa
from src.n7_ngoc_thanh_thuc_nghiem import study_groups, save_json
from src.n8_trang_bui_thong_ke import load_runs, read_trials, summarize_rows, summarize_folder, representative_seeds
from src.n9_trang_nguyen_ve_hinh import one_shot, population_story, draw_map, chosen_report, utility_and_energy


def find_run(results, name, seed):
    for result in results:
        if result["experiment"]["id"] == name and result["settings"]["seed"] == seed:
            return result
    raise ValueError("Chưa có lượt " + name + " seed " + str(seed))


def save_figure(fig, path):
    # Ghi xong ảnh tạm rồi mới đưa ra tệp đích để không lấy nhầm ảnh dở.
    temporary = path.with_name(path.name + ".tmp")
    fig.savefig(temporary, format="png", dpi=120, facecolor=fig.get_facecolor())
    temporary.replace(path)
    plt.close(fig)


def build(output=None):
    if output is None:
        output = ROOT / "results"
    output = Path(output).resolve()
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    summarize_folder(output)
    results = load_runs(output)
    if len(results) != 330:
        raise ValueError("Bộ ảnh seminar cần đủ 11 cấu hình × 30 seed. Bộ thử nhanh chỉ dùng để kiểm code/CSV.")
    for result in results:
        if result["settings"]["population"] != 30 or result["settings"]["iterations"] != 800:
            raise ValueError("Các nhãn ảnh seminar chốt N=30,T=800; dữ liệu đang dùng ngân sách khác.")
    summary = summarize_rows(read_trials(output))
    lookup = {}
    for row in summary:
        lookup[row["id"]] = row
    cases = ["A_goc", "B_goc", "C_goc"]
    case_labels = ["A · cơ bản", "B · khe hẹp", "C · chắn đường"]
    representatives = {}
    original_results = []
    original_summary = []
    original_subtitle = "N=30 · T=800 · seed gần trung vị phần mục tiêu · 30 biến · pin 220 · q=0.5 · b=1"
    sections = []

    for i in range(3):
        name = cases[i]
        chosen = representative_seeds(results, name)
        representatives[name] = chosen
        result = find_run(results, name, chosen["typical"])
        original_results.append(result)
        original_summary.append(lookup[name])
        trace = woa(evaluate, result["problem"], result["settings"], keep_populations=True)
        assert math.isclose(trace["best_overall"]["evaluation"]["score"], result["best_overall"]["evaluation"]["score"], abs_tol=1e-7)
        trace["experiment"] = result["experiment"]
        save_json(output / "demos" / (name + "_typical.json"), trace)
        filename = name + "_dan_theo_thoi_gian.png"
        save_figure(population_story(trace), figures / filename)
        sections.append((name + " · xem cả đàn qua các lượt", filename,
                         "Seed gần trung vị: " + str(chosen["typical"]) + ". Tất cả đường xám là phương án thật, có thể còn vi phạm."))

        fig, axes = plt.subplots(1, 3, figsize=(16, 6))
        for j, key in enumerate(["best", "typical", "worst"]):
            seed = chosen[key]
            if seed is None:
                axes[j].axis("off")
                continue
            sample = find_run(results, name, seed)
            label = {"best": "Phần mục tiêu thấp nhất", "typical": "Gần trung vị", "worst": "Phần mục tiêu cao nhất"}[key]
            draw_map(axes[j], sample["problem"], chosen_report(sample), sample["final_population"], label + " · seed " + str(seed))
        fig.suptitle("Ca gốc " + name + " · ba ví dụ lấy theo quy tắc công bố trước", fontsize=16)
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        filename = name + "_ba_seed.png"
        fig.savefig(figures / filename, dpi=120, bbox_inches="tight")
        plt.close(fig)
        sections.append((name + " · tốt, điển hình, kém trong các lượt hợp lệ", filename,
                         "Xếp theo phần mục tiêu -U + 0.12*L/100, không chỉ theo U. Lượt thất bại vẫn ở bảng 30 seed."))
        save_figure(utility_and_energy(trace), figures / (name + "_pin_va_trai.png"))
        sections.append((name + " · từng trại và túi pin", name + "_pin_va_trai.png", "Các đại lượng đều dùng đơn vị mô phỏng."))

    save_json(output / "representatives.json", representatives)
    fig = one_shot(original_results, original_summary, case_labels,
                   "THỰC NGHIỆM CA GỐC · WOA theo mã tác giả", original_subtitle)
    save_figure(fig, figures / "00_case_goc_tong_hop.png")

    labels = {"A_goc": "Cơ sở", "B_goc": "Cơ sở", "A_l_independent": "l độc lập", "B_l_independent": "l độc lập",
              "A_reinit": "Re-init", "B_reinit": "Re-init", "B_a_cosine": "Cosine", "B_a_quadratic": "Quadratic",
              "A_den_6": "Tối đa 6", "A_den_8": "Tối đa 8"}
    niche_sections = []
    for group in study_groups():
        samples = []
        stats = []
        names = []
        for name in group[2]:
            samples.append(find_run(results, name, 7))
            stats.append(lookup[name])
            names.append(labels[name])
        subtitle = "Ví dụ map: seed 7 cố định · Cột/bảng: 30 seed · N=30 · T=800 · 30 biến · B=220 · q=0.5 · b=1"
        filename = group[0] + "_ONE_SHOT.png"
        save_figure(one_shot(samples, stats, names, group[1], subtitle), figures / filename)
        niche_sections.append((group[1], filename, "Best overall: số lần chính nghiệm có J thấp nhất đủ điều kiện. Có hợp lệ: đã từng có ít nhất một nghiệm hợp lệ."))

    # Mở rộng phần benchmark bằng ảnh có thể chụp lên slide.
    import csv
    with open(output / "benchmark_summary.csv", encoding="utf-8-sig") as file:
        benchmark = list(csv.DictReader(file))
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    names = []
    rates = []
    rows = []
    for row in benchmark:
        names.append(row["function"])
        rates.append(int(row["success_n"]))
        rows.append([row["function"], row["success_n"] + "/" + row["n"], row["score_mean"]])
    axes[0].bar(names, rates, color=["#6b9dbf", "#78b195", "#dcac65"])
    axes[0].set_ylim(0, 35)
    axes[0].set_ylabel("Seed đạt ngưỡng sai số")
    axes[0].set_title("N=30 · T=500 · 30 seed · miền tọa độ gốc")
    from src.n9_trang_nguyen_ve_hinh import table_on_axis
    table_on_axis(axes[1], "Đáp án biết trước: f*=0", ["Bài", "Đạt đích", "f trung bình"], rows)
    fig.tight_layout()
    save_figure(fig, figures / "benchmark.png")

    css = "body{margin:0;background:#f5f4ef;color:#20394b;font:16px/1.6 system-ui}main{max-width:1300px;margin:auto;padding:28px}h1{font-size:38px}section{background:white;padding:24px;margin:24px 0;border-radius:14px}img{width:100%;height:auto}a{color:#246a4e}.lead{font-size:20px}"
    body = "<h1>Đom Đóm · bản nhóm đã thu gọn</h1><p class='lead'>Ca gốc trước, bốn ngách sau. Toàn bộ hình có nguồn từ Python.</p>"
    body += "<p>Mở <b>demo_colab.ipynb</b> hoặc chạy <b>python -m streamlit run app.py</b> để điều khiển cả đàn. Trang này là kết quả đã lưu.</p>"
    body += "<p><b>Chốt:</b> 30 biến, pin 220, q=0.5, b=1, phạt bão/pin/map cố định, utility bão hòa, bỏ phạt gấp khúc.</p>"
    body += "<section><h2>Tổng quan các ca gốc · 30 seed/ca</h2><img src='results/figures/00_case_goc_tong_hop.png'></section>"
    for title, filename, note in sections:
        body += "<section><h2>" + html.escape(title) + "</h2><p>" + html.escape(note) + "</p><img loading='lazy' src='results/figures/" + filename + "'></section>"
    body += "<section><h2>Kiểm chứng benchmark</h2><p>Quadratic 1 chiều; Sphere và Rastrigin 30 chiều. Ngưỡng: 1e-8, 1e-8, 1e-6. Không gọi f máy tính bằng 0 là chứng minh tối ưu tuyệt đối.</p><img src='results/figures/benchmark.png'></section>"
    body += "<h1>Bốn ngách đã chốt</h1>"
    for title, filename, note in niche_sections:
        body += "<section><h2>" + html.escape(title) + "</h2><p>" + html.escape(note) + "</p><img loading='lazy' src='results/figures/" + filename + "'></section>"
    body += "<p><a href='docs/01_de_bai.md'>Đề bài</a> · <a href='docs/02_loi_va_tac_gia.md'>Lõi và mã tác giả</a> · <a href='docs/03_bon_ngach.md'>Bốn ngách</a></p>"
    import os
    prefix = Path(os.path.relpath(output, ROOT)).as_posix() + "/figures/"
    body = body.replace("results/figures/", prefix)
    (ROOT / "MO_KET_QUA.html").write_text("<!doctype html><html lang='vi'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Đom Đóm</title><style>" + css + "</style><main>" + body + "</main></html>", encoding="utf-8")
    print("Đã tạo ảnh 16:9, ba ca gốc, sáu ảnh đối chứng cho bốn ngách và ba bản replay.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "results"))
    args = parser.parse_args()
    build(args.output)
