"""Trang Nguyễn: mỗi ảnh đủ để chụp lên slide, không phải đi tìm bảng.

Đường xám là các phương án trong đàn, có thể còn sai luật.
Đường nổi bật lấy từ sổ hợp lệ; nếu chưa có, mình ghi rõ chưa hợp lệ.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


def chosen_report(result):
    if result["best_valid"] is not None:
        return result["best_valid"]["evaluation"]
    return result["best_overall"]["evaluation"]


def draw_map(ax, problem, report=None, population=None, title="", alpha=0.10):
    for storm in problem["storms"]:
        center = (storm["x"], storm["y"])
        ax.add_patch(Circle(center, storm["r"], facecolor="#f0a6ca", alpha=0.55, zorder=1))
        ax.add_patch(Circle(center, storm["r"] + problem["safety"], fill=False,
                            edgecolor="#d87a99", linestyle="--", linewidth=1.2, zorder=2))
        ax.text(storm["x"], storm["y"], storm["name"], ha="center", va="center",
                fontsize=9, weight="bold", color="#8b0000", zorder=6)
    if population is not None:
        for whale in population:
            xs = [problem["start"][0]]
            ys = [problem["start"][1]]
            for k in range(10):
                xs.append(whale[3 * k])
                ys.append(whale[3 * k + 1])
            xs.append(problem["target"][0])
            ys.append(problem["target"][1])
            ax.plot(xs, ys, color="#646e77", alpha=alpha, linewidth=0.8, zorder=3)
    if "gate" in problem:
        gate = problem["gate"]
        ax.plot([gate["x"], gate["x"]], [gate["y_min"], gate["y_max"]],
                color="#7a3eb1", linewidth=4, zorder=7)
    for camp in problem["camps"]:
        w = camp.get("weight", camp.get("w", None))
        label = f"{camp['name']} (w={w})" if w is not None else camp["name"]
        ax.scatter(camp["x"], camp["y"], marker="D", s=28, color="#233848", zorder=8)
        ax.text(camp["x"] + 1.5, camp["y"] + 1.5, label, fontsize=7.5,
                weight="bold", color="#233848", zorder=8)
    if report is not None:
        points = report["points"]
        for i in range(len(points) - 1):
            a = points[i]
            b = points[i + 1]
            color = "#126aaf"
            if i in report["bad_segments"]:
                color = "#cb3945"
            ax.plot([a[0], b[0]], [a[1], b[1]], color=color, linewidth=2.3, zorder=9)
        for beacon in report["beacons"]:
            if beacon["energy"] > 0.001:
                ax.scatter(beacon["x"], beacon["y"], s=20 + 7 * beacon["energy"],
                           color="#f7c75e", edgecolor="#916b18", alpha=0.8, zorder=10)
            else:
                ax.scatter(beacon["x"], beacon["y"], s=22, facecolor="white", edgecolor="#126aaf", zorder=10)
        status = "HỢP LỆ"
        if not report["valid"]:
            status = "CHƯA HỢP LỆ"
        title += "\n" + status + " · U=" + str(round(report["utility_sat"], 3))
        title += " · pin=" + str(round(report["total"], 1)) + "/220"
    for label, point in [["S", problem["start"]], ["T", problem["target"]]]:
        ax.scatter(point[0], point[1], s=45, color="black", zorder=11)
        offset = 2
        if label == "T":
            offset = -4
        ax.text(point[0] + offset, point[1] + 3, label, weight="bold", fontsize=10, zorder=11)
    ax.set_xlim(-2, 102)
    ax.set_ylim(-2, 102)
    ax.set_aspect("equal")
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.13)
    ax.set_title(title, fontsize=10, pad=7)


def plot_population(problem, report, population, title="", alpha=0.1):
    fig, ax = plt.subplots(figsize=(7, 7))
    draw_map(ax, problem, report, population, title, alpha)
    fig.text(0.5, 0.02, "Xám: cả đàn (có thể sai luật) · Vàng: đèn có pin · Rỗng: điểm không phát", ha="center", fontsize=9)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    return fig


def text_number(value):
    if value is None:
        return "—"
    return str(round(float(value), 3))


def table_on_axis(ax, title, headers, rows):
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=12, weight="bold", pad=6)
    table = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.65)


def one_shot(results, summaries, labels, title, subtitle=""):
    # Chọn các khung bằng tọa độ của tờ hình: x, y, rộng, cao, đều 0..1.
    fig = plt.figure(figsize=(16, 9), facecolor="#faf9f5")
    fig.text(0.035, 0.965, title, fontsize=21, weight="bold", color="#20394b")
    fig.text(0.035, 0.93, subtitle, fontsize=11, color="#455967")
    width = 0.94 / len(results)
    for i in range(len(results)):
        result = results[i]
        ax = fig.add_axes([0.03 + width * i, 0.35, width - 0.018, 0.51])
        draw_map(ax, result["problem"], chosen_report(result), result["final_population"],
                 labels[i] + " · seed " + str(result["settings"]["seed"]))

    ax = fig.add_axes([0.055, 0.075, 0.25, 0.205])
    means = []
    errors = []
    utility_rows = []
    valid_rows = []
    for i in range(len(summaries)):
        row = summaries[i]
        mean = row["utility_sat_mean"]
        if mean is None:
            mean = float("nan")
        means.append(mean)
        errors.append(row["utility_sat_std"] or 0)
        utility_rows.append([labels[i], text_number(row["utility_sat_mean"]),
                             text_number(row["utility_sat_std"]), text_number(row["minimum_service_mean"])])
        gate = "—"
        if "gate" in results[i]["problem"]:
            gate = str(row["gate_found_n"]) + "/" + str(row["n"])
        valid_rows.append([labels[i], str(row["valid_n"]) + "/" + str(row["n"]),
                           str(row["overall_valid_n"]) + "/" + str(row["n"]), gate])
    ax.bar(range(len(means)), means, yerr=errors, capsize=5, color=["#6b9dbf", "#78b195", "#dcac65"][:len(means)])
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Utility bão hòa", fontsize=10)
    ax.set_ylim(0, 1.08)
    ax.grid(axis="y", alpha=0.15)
    ax.set_title("Trung bình ± SD mẫu", loc="left", fontsize=12, weight="bold")
    table_on_axis(fig.add_axes([0.35, 0.075, 0.285, 0.205]), "Utility · chỉ lượt hợp lệ",
                  ["Cấu hình", "TB", "SD", "Trại yếu"], utility_rows)
    table_on_axis(fig.add_axes([0.675, 0.075, 0.29, 0.205]), "Độ tin cậy · mọi seed",
                  ["Cấu hình", "Có hợp lệ", "Best overall", "Từng qua khe"], valid_rows)
    fig.text(0.035, 0.025, "Bản đồ: ví dụ ghi rõ seed · Bảng/cột: toàn bộ seed · Xám: đàn cuối đã chấm · Đỏ: vi phạm bão", fontsize=9)
    return fig


def population_story(result):
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    from src.n3_phuc_khang_danh_gia import evaluate
    snapshots = result["snapshots"]
    fractions = [0, 0.05, 0.2, 0.5, 0.8, 1]
    for i in range(6):
        index = int(fractions[i] * (len(snapshots) - 1))
        snap = snapshots[index]
        report = evaluate(snap["position"], result["problem"])
        draw_map(axes[i // 3][i % 3], result["problem"], report, snap["population"],
                 "Lượt " + str(snap["iteration"]) + " · cả " + str(len(snap["population"])) + " cá voi", 0.13)
    fig.suptitle("Ca gốc · đàn thay đổi theo thời gian · seed " + str(result["settings"]["seed"]), fontsize=17)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    return fig


def utility_and_energy(result):
    report = chosen_report(result)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    names = []
    for camp in result["problem"]["camps"]:
        names.append(camp["name"])
    axes[0].bar(names, report["satisfaction"], color="#78b195")
    axes[0].set_ylim(0, 1)
    axes[0].set_title("Hữu dụng tại từng trại")
    axes[1].bar(["Bay", "Đèn", "Tổng"], [report["flight"], report["lamps"], report["total"]], color=["#6b9dbf", "#dcac65", "#78b195"])
    axes[1].axhline(220, color="#cb3945", linestyle="--", label="Ngân sách 220")
    axes[1].set_title("Một túi pin, hai việc")
    axes[1].legend()
    fig.tight_layout()
    return fig
