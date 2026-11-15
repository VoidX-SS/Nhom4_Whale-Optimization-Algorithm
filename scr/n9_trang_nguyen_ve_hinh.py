

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).resolve().parent


def chosen_report(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("best_valid") is not None:
        return result["best_valid"]["evaluation"]
    return result["best_overall"]["evaluation"]


def draw_light_bulb(ax: plt.Axes, x: float, y: float, energy: float) -> None:
    scale = 0.7 + 0.03 * energy
    bulb = Circle(
        (x, y),
        1.8 * scale,
        facecolor="#f7c75e",
        edgecolor="#916b18",
        linewidth=1.2,
        zorder=10,
        clip_on=False,
    )
    base = Rectangle(
        (x - 0.7 * scale, y - 2.5 * scale),
        1.4 * scale,
        1.0 * scale,
        facecolor="#b0b0b0",
        edgecolor="#606060",
        zorder=9,
        clip_on=False,
    )
    ax.add_patch(bulb)
    ax.add_patch(base)


def draw_map(
    ax: plt.Axes,
    problem: dict[str, Any],
    report: dict[str, Any] | None = None,
    population: list[list[float]] | None = None,
    title: str = "",
    alpha: float = 0.10,
) -> None:
    for storm in problem.get("storms", []):
        center = (storm["x"], storm["y"])
        ax.add_patch(Circle(center, storm["r"], facecolor="#f0a6ca", alpha=0.55, zorder=1))
        ax.add_patch(
            Circle(
                center,
                storm["r"] + problem["safety"],
                fill=False,
                edgecolor="#d87a99",
                linestyle="--",
                linewidth=1.2,
                zorder=2,
            )
        )
        if "name" in storm:
            ax.text(
                storm["x"],
                storm["y"],
                storm["name"],
                ha="center",
                va="center",
                fontsize=9,
                weight="bold",
                color="#8b0000",
                zorder=6,
            )

    if "gate" in problem:
        gate = problem["gate"]
        ax.plot(
            [gate["x"], gate["x"]],
            [gate["y_min"], gate["y_max"]],
            color="#7a3eb1",
            linewidth=4,
            zorder=7,
        )

    if population is not None:
        for whale in population:
            xs = [problem["start"][0]] + [whale[3 * k] for k in range(10)] + [problem["target"][0]]
            ys = [problem["start"][1]] + [whale[3 * k + 1] for k in range(10)] + [problem["target"][1]]
            ax.plot(xs, ys, color="#646e77", alpha=alpha, linewidth=0.8, zorder=3)

    for camp in problem.get("camps", []):
        ax.scatter(camp["x"], camp["y"], marker="D", s=28, color="#233848", zorder=8)
        if "name" in camp:
            ax.text(
                camp["x"] + 1.5,
                camp["y"] + 1.5,
                camp["name"],
                fontsize=8,
                weight="bold",
                color="#233848",
                zorder=8,
            )

    if report is not None:
        points = report["points"]
        bad_segments = set(report.get("bad_segments", []))
        for i in range(len(points) - 1):
            a, b = points[i], points[i + 1]
            color = "#cb3945" if i in bad_segments else "#126aaf"
            ax.plot([a[0], b[0]], [a[1], b[1]], color=color, linewidth=2.3, zorder=9)

        for beacon in report.get("beacons", []):
            if beacon["energy"] > 0.001:
                draw_light_bulb(ax, beacon["x"], beacon["y"], beacon["energy"])
            else:
                ax.scatter(
                    beacon["x"],
                    beacon["y"],
                    s=25,
                    facecolor="white",
                    edgecolor="#126aaf",
                    zorder=10,
                    clip_on=False,
                )

        status = "HỢP LỆ" if report.get("valid") else "CHƯA HỢP LỆ"
        budget = float(problem.get("budget", 220.0))
        total_pin = float(report.get("total", 0.0))
        u_val = report.get("utility_sat")
        u_text = "—" if u_val is None else f"{u_val:.3f}"
        title = f"{title}\n{status} · U={u_text} · pin={total_pin:.1f}/{budget:.0f}"

    for label, pt in [("S", problem["start"]), ("T", problem["target"])]:
        ax.scatter(pt[0], pt[1], s=50, color="black", zorder=11, clip_on=False)
        offset = 2 if label != "T" else -4
        ax.text(pt[0] + offset, pt[1] + 3, label, weight="bold", fontsize=10, zorder=11)

    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.set_aspect("equal")
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.13)
    ax.set_title(title, fontsize=10, pad=7)


def plot_population(
    problem: dict[str, Any],
    report: dict[str, Any] | None,
    population: list[list[float]] | None,
    title: str = "",
    alpha: float = 0.10,
) -> plt.Figure:
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor="#faf9f5")
    ax = fig.add_axes([0.08, 0.12, 0.56, 0.76])
    draw_map(ax, problem, report, population, title, alpha)

    fig.text(0.70, 0.85, "CHÚ THÍCH", fontsize=14, weight="bold")
    legend = [
        ("Các phương án trong đàn", "#646e77", "-"),
        ("Đường bay hợp lệ", "#126aaf", "-"),
        ("Đường bay vi phạm bão", "#cb3945", "-"),
        ("Biên an toàn bão", "#d87a99", "--"),
    ]
    y_pos = 0.79
    for text, color, style in legend:
        fig.add_artist(
            Line2D(
                [0.70, 0.75],
                [y_pos, y_pos],
                transform=fig.transFigure,
                color=color,
                linestyle=style,
                linewidth=2.2,
            )
        )
        fig.text(0.77, y_pos - 0.008, text, fontsize=11)
        y_pos -= 0.055

    fig.text(0.70, 0.55, "◆  Trại cứu hộ", fontsize=11)
    fig.text(0.70, 0.50, "●  Đèn đang phát (kích thước theo pin)", fontsize=11)
    fig.text(0.70, 0.45, "○  Đèn không phát", fontsize=11)

    if report is not None:
        status = "HỢP LỆ" if report.get("valid") else "CHƯA HỢP LỆ"
        u_val = report.get("utility_sat")
        fig.text(0.70, 0.35, "KẾT QUẢ", fontsize=14, weight="bold")
        fig.text(0.70, 0.30, f"Trạng thái: {status}", fontsize=11)
        fig.text(0.70, 0.26, f"U = {'—' if u_val is None else round(u_val, 3)}", fontsize=11)
        fig.text(
            0.70,
            0.22,
            f"Pin = {report.get('total', 0.0):.1f}/{problem.get('budget', 220):.0f}",
            fontsize=11,
        )

    fig.text(
        0.5,
        0.025,
        "Đường xám là cả đàn (có thể chưa hợp lệ) · Đường nổi bật lấy từ sổ hợp lệ (hoặc ghi rõ CHƯA HỢP LỆ)",
        ha="center",
        fontsize=10,
    )
    return fig


def table_on_axis(ax: plt.Axes, title: str, headers: list[str], rows: list[list[str]]) -> None:
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=11, weight="bold", pad=6)
    table = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.55)


def _fmt_num(val: float | None) -> str:
    return "—" if val is None else f"{float(val):.3f}"


def one_shot(
    results: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    labels: list[str],
    title: str,
    subtitle: str = "",
) -> plt.Figure:
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor="#faf9f5")
    fig.text(0.035, 0.95, title, fontsize=20, weight="bold", color="#20394b")
    fig.text(0.035, 0.92, subtitle, fontsize=11, color="#455967")

    n_cases = len(results)
    width = 0.92 / max(1, n_cases)

    for i, res in enumerate(results):
        ax = fig.add_axes([0.03 + width * i, 0.37, width - 0.02, 0.51])
        seed = res.get("settings", {}).get("seed", "?")
        draw_map(
            ax,
            res["problem"],
            chosen_report(res),
            res.get("final_population"),
            f"{labels[i]} · seed {seed}",
        )

    ax_bar = fig.add_axes([0.04, 0.08, 0.25, 0.21])
    means = [float("nan") if s.get("utility_sat_mean") is None else s["utility_sat_mean"] for s in summaries]
    errs = [s.get("utility_sat_std") or 0.0 for s in summaries]
    colors = ["#6b9dbf", "#78b195", "#dcac65"][:n_cases]

    ax_bar.bar(range(n_cases), means, yerr=errs, capsize=5, color=colors)
    ax_bar.set_xticks(range(n_cases))
    ax_bar.set_xticklabels(labels, fontsize=9)
    ax_bar.set_ylabel("Utility bão hòa (U)", fontsize=10)
    ax_bar.set_ylim(0, 1.08)
    ax_bar.grid(axis="y", alpha=0.15)
    ax_bar.set_title("Trung bình ± SD mẫu (30 seed)", loc="left", fontsize=11, weight="bold")

    u_rows = [
        [
            labels[i],
            _fmt_num(s.get("utility_sat_mean")),
            _fmt_num(s.get("utility_sat_std")),
            _fmt_num(s.get("minimum_service_mean")),
        ]
        for i, s in enumerate(summaries)
    ]
    table_on_axis(
        fig.add_axes([0.32, 0.08, 0.28, 0.21]),
        "Utility · chỉ lượt hợp lệ (30 seed)",
        ["Cấu hình", "TB", "SD mẫu", "Trại yếu"],
        u_rows,
    )

    v_rows: list[list[str]] = []
    for i, s in enumerate(summaries):
        n_total = s.get("n", 30)
        gate_str = f"{s.get('gate_found_n', 0)}/{n_total}" if "gate" in results[i]["problem"] else "—"
        v_rows.append(
            [
                labels[i],
                f"{s.get('valid_n', 0)}/{n_total}",
                f"{s.get('overall_valid_n', 0)}/{n_total}",
                gate_str,
            ]
        )
    table_on_axis(
        fig.add_axes([0.63, 0.08, 0.33, 0.21]),
        "Độ tin cậy · mọi seed (30 seed)",
        ["Cấu hình", "Có hợp lệ", "Best overall hợp lệ", "Qua khe"],
        v_rows,
    )

    fig.text(
        0.035,
        0.02,
        "Bản đồ: seed minh họa ghi trên tiêu đề · Cột/Bảng: 30 seed · Râu: SD mẫu · Xám: đàn · Xanh: hợp lệ · Đỏ: vi phạm bão",
        fontsize=9,
    )
    return fig


def population_story(result: dict[str, Any], evaluate_fn: Any, case_label: str = "") -> plt.Figure:
    fig, axes = plt.subplots(2, 3, figsize=(19.2, 10.8), dpi=100, facecolor="#faf9f5")
    snapshots = result["snapshots"]
    fractions = [0.0, 0.05, 0.2, 0.5, 0.8, 1.0]

    for i in range(6):
        idx = int(fractions[i] * (len(snapshots) - 1))
        snap = snapshots[idx]
        rep = evaluate_fn(snap["position"], result["problem"])
        ax = axes[i // 3][i % 3]
        draw_map(
            ax,
            result["problem"],
            rep,
            snap.get("population"),
            f"Lượt {snap['iteration']} · đàn {len(snap.get('population', []))} cá voi",
            alpha=0.13,
        )

    seed = result.get("settings", {}).get("seed", "?")
    prefix = f"{case_label} · " if case_label else ""
    fig.suptitle(f"{prefix}Diễn biến quần thể theo thời gian · seed {seed}", fontsize=18, weight="bold", color="#20394b")
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig


def utility_and_energy(result: dict[str, Any], case_label: str = "") -> plt.Figure:
    report = chosen_report(result)
    fig, axes = plt.subplots(1, 2, figsize=(19.2, 10.8), dpi=100, facecolor="#faf9f5")

    camps = result["problem"].get("camps", [])
    names = [c.get("name", f"C{idx + 1}") for idx, c in enumerate(camps)]
    sat = report.get("satisfaction", [])
    axes[0].bar(names, sat, color="#78b195", edgecolor="#3f6d57")
    axes[0].set_ylim(0, 1.05)
    axes[0].set_ylabel("Mức bão hòa (u_m)", fontsize=12)
    axes[0].set_title("Hữu dụng tại từng trại", fontsize=14, weight="bold")
    axes[0].grid(axis="y", alpha=0.2)

    budget = float(result["problem"].get("budget", 220.0))
    vals = [float(report.get("flight", 0.0)), float(report.get("lamps", 0.0)), float(report.get("total", 0.0))]
    axes[1].bar(["Bay", "Đèn", "Tổng"], vals, color=["#6b9dbf", "#dcac65", "#78b195"], edgecolor="#2f4858")
    axes[1].axhline(budget, color="#cb3945", linestyle="--", linewidth=1.8, label=f"Ngân sách {budget:.0f}")
    axes[1].set_ylabel("Năng lượng (pin)", fontsize=12)
    axes[1].set_title("Một túi pin, hai việc", fontsize=14, weight="bold")
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].legend(loc="upper left")

    seed = result.get("settings", {}).get("seed", "?")
    prefix = f"{case_label} · " if case_label else ""
    fig.suptitle(f"{prefix}Phân tích hữu dụng & năng lượng · seed {seed}", fontsize=18, weight="bold", color="#20394b")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    return fig


def plot_seed_triplets(
    res_best: dict[str, Any],
    res_typical: dict[str, Any],
    res_worst: dict[str, Any],
    title: str,
) -> plt.Figure:
    fig, axes = plt.subplots(1, 3, figsize=(19.2, 10.8), dpi=100, facecolor="#faf9f5")
    items = [
        ("Tốt nhất", res_best),
        ("Tiêu biểu (gần trung vị)", res_typical),
        ("Kém nhất", res_worst),
    ]
    for ax, (tag, res) in zip(axes, items):
        seed = res.get("settings", {}).get("seed", "?")
        draw_map(ax, res["problem"], chosen_report(res), res.get("final_population"), f"{tag} · seed {seed}")

    fig.suptitle(title, fontsize=18, weight="bold", color="#20394b")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    return fig


def save_figure(fig: plt.Figure, path: str | Path) -> Path:
    target = Path(path)
    if not target.is_absolute():
        target = BASE_DIR / target
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=100)
    plt.close(fig)
    return target
