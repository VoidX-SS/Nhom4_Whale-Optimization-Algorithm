
import math
import random
import copy
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
import numpy as np

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['axes.unicode_minus'] = False


def get_base_problem(map_type="co_ban"):
    prob = {
        "start": [0, 50],
        "target": [100, 50],
        "safety": 2,
        "budget": 220,
        "flight_cost": 0.45,
        "signal_range": 18,
        "alpha": 0.1,
        "beacon_max": 25,
        "active_lights": 10,
        "length_weight": 0.12,
        "collision_weight": 100.0,
        "battery_weight": 30.0,
        "map_weight": 100.0,
        "camps": [
            {"name": "C1", "x": 12, "y": 70, "w": 12},
            {"name": "C2", "x": 20, "y": 25, "w": 18},
            {"name": "C3", "x": 38, "y": 31, "w": 15},
            {"name": "C4", "x": 43, "y": 85, "w": 20},
            {"name": "C5", "x": 61, "y": 43, "w": 16},
            {"name": "C6", "x": 65, "y": 83, "w": 12},
            {"name": "C7", "x": 84, "y": 63, "w": 18},
            {"name": "C8", "x": 90, "y": 22, "w": 14},
        ],
    }
    
    if map_type == "co_ban":  # Ca A
        prob["storms"] = [
            {"name": "V1", "x": 28, "y": 50, "r": 14},
            {"name": "V2", "x": 50, "y": 50, "r": 14},
            {"name": "V3", "x": 72, "y": 50, "r": 14},
        ]
    elif map_type == "khe_hep":  # Ca B
        prob["storms"] = [
            {"name": "V1", "x": 40, "y": 25, "r": 18},
            {"name": "V2", "x": 40, "y": 75, "r": 18},
            {"name": "V3", "x": 70, "y": 50, "r": 12},
        ]
        prob["gate"] = {"x": 40, "y_min": 43, "y_max": 57}
    elif map_type == "chan_duong":  # Ca C
        prob["storms"] = [
            {"name": "V1", "x": 25, "y": 50, "r": 15},
            {"name": "V2", "x": 50, "y": 50, "r": 15},
            {"name": "V3", "x": 75, "y": 50, "r": 15},
        ]
    return prob


def distance(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])

def distance_to_segment(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    square_length = dx * dx + dy * dy
    if square_length == 0:
        return distance(point, a)
    t = max(0, min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / square_length))
    nearest = [a[0] + t * dx, a[1] + t * dy]
    return distance(point, nearest)

def decode(whale, problem):
    beacons = [{"x": whale[3*k], "y": whale[3*k+1], "energy": whale[3*k+2], "active": False} for k in range(10)]
    for _ in range(problem["active_lights"]):
        chosen = -1
        for k in range(10):
            if not beacons[k]["active"]:
                if chosen == -1 or beacons[k]["energy"] > beacons[chosen]["energy"]:
                    chosen = k
        if chosen != -1:
            beacons[chosen]["active"] = True
    for b in beacons:
        if not b["active"]:
            b["energy"] = 0
    return beacons

def crosses_gate(points, problem):
    if "gate" not in problem:
        return False
    gate = problem["gate"]
    for i in range(len(points) - 1):
        a, b = points[i], points[i+1]
        if (a[0] < gate["x"] <= b[0]) or (b[0] <= gate["x"] < a[0]):
            if b[0] != a[0]:
                fraction = (gate["x"] - a[0]) / (b[0] - a[0])
                y = a[1] + fraction * (b[1] - a[1])
                if gate["y_min"] <= y <= gate["y_max"]:
                    return True
    return False

def evaluate(whale, problem):
    beacons = decode(whale, problem)
    points = [problem["start"]] + [[b["x"], b["y"]] for b in beacons] + [problem["target"]]
    
    length, collision, clearance = 0, 0, None
    bad_segments = []
    for i in range(len(points) - 1):
        a, b = points[i], points[i+1]
        length += distance(a, b)
        bad = False
        for storm in problem["storms"]:
            safe_radius = storm["r"] + problem["safety"]
            gap = distance_to_segment([storm["x"], storm["y"]], a, b) - safe_radius
            if clearance is None or gap < clearance:
                clearance = gap
            if gap < -1e-9:
                bad = True
            depth = max(0, -gap) / safe_radius
            collision += depth * depth
        if bad:
            bad_segments.append(i)
            
    flight = problem["flight_cost"] * length
    lamps = sum(b["energy"] for b in beacons)
    total_energy = flight + lamps
    over_energy = max(0, total_energy - problem["budget"]) / problem["budget"]
    
    levels, satisfaction = [], []
    weighted_sat, weight_sum = 0, 0
    range_sq = problem["signal_range"] ** 2
    for camp in problem["camps"]:
        level = sum(b["energy"] / (1 + ((b["x"] - camp["x"])**2 + (b["y"] - camp["y"])**2) / range_sq) for b in beacons)
        sat = 1 - math.exp(-problem["alpha"] * level)
        levels.append(level)
        satisfaction.append(sat)
        weighted_sat += camp["w"] * sat
        weight_sum += camp["w"]
    utility_sat = weighted_sat / weight_sum
    
    box_ok = all(0 <= whale[3*k] <= 100 and 0 <= whale[3*k+1] <= 100 and 0 <= whale[3*k+2] <= problem["beacon_max"] for k in range(10))
    map_violation = sum((max(0, -v, v - 100) / 100) ** 2 for k in range(10) for v in [whale[3*k], whale[3*k+1]])
    
    base_score = -utility_sat + problem["length_weight"] * length / 100
    penalty = problem["collision_weight"] * collision + problem["battery_weight"] * (over_energy ** 2) + problem["map_weight"] * map_violation
    
    valid = box_ok and (clearance is None or clearance >= -1e-9) and (total_energy <= problem["budget"] + 1e-7)
    through_gate = valid and crosses_gate(points, problem)
    
    return {
        "score": base_score + penalty, "base_score": base_score, "valid": valid,
        "through_gate": through_gate, "beacons": beacons, "points": points,
        "utility_sat": utility_sat, "minimum_service": min(satisfaction),
        "total": total_energy, "flight": flight, "lamps": lamps, "length": length,
        "satisfaction": satisfaction, "bad_segments": bad_segments, "collision": collision
    }


def run_woa(problem, settings):
    rng = random.Random(settings["seed"])
    lower = [0, 0, 0] * 10
    upper = [100, 100, problem["beacon_max"]] * 10
    
    population = [[lower[j] + rng.random() * (upper[j] - lower[j]) for j in range(30)] for _ in range(settings["population"])]
    best_overall, best_valid, best_gate = None, None, None
    snapshots = []
    total_iter = settings["iterations"]
    
    for t in range(total_iter):
        for i in range(settings["population"]):
            for j in range(30):
                population[i][j] = max(lower[j], min(upper[j], population[i][j]))
                    
            rep = evaluate(population[i], problem)
            if best_overall is None or rep["score"] < best_overall["evaluation"]["score"]:
                best_overall = {"position": population[i].copy(), "evaluation": rep}
            if rep["valid"]:
                if best_valid is None or rep["base_score"] < best_valid["evaluation"]["base_score"]:
                    best_valid = {"position": population[i].copy(), "evaluation": rep}
                if rep["through_gate"]:
                    if best_gate is None or rep["base_score"] < best_gate["evaluation"]["base_score"]:
                        best_gate = {"position": population[i].copy(), "evaluation": rep}
                        
        if t % settings["snapshot_every"] == 0 or t == total_iter - 1:
            chosen = best_valid if best_valid else best_overall
            snapshots.append({"iteration": t, "population": copy.deepcopy(population), "position": chosen["position"].copy()})
            
        progress = t / total_iter
        a = 2 - 2 * progress
        a2 = -1 - progress
        
        leader = best_overall["position"]
        for i in range(settings["population"]):
            r1, r2, p = rng.random(), rng.random(), rng.random()
            A, C = 2 * a * r1 - a, 2 * r2
            l = (a2 - 1) * rng.random() + 1
            for j in range(30):
                if p < 0.5:
                    ref = population[int(len(population) * rng.random())][j] if abs(A) >= 1 else leader[j]
                    population[i][j] = ref - A * abs(C * ref - population[i][j])
                else:
                    D = abs(leader[j] - population[i][j])
                    population[i][j] = leader[j] + D * math.exp(1.0 * l) * math.cos(2 * math.pi * l)
                    
    return {
        "problem": problem, "settings": settings, "best_overall": best_overall,
        "best_valid": best_valid, "best_gate": best_gate, "snapshots": snapshots,
        "final_population": population
    }


def chosen_report(result):
    if result["best_valid"] is not None:
        return result["best_valid"]["evaluation"]
    return result["best_overall"]["evaluation"]

def draw_light_bulb(ax, x, y, energy):
    scale = 0.7 + 0.03 * energy
    bulb = Circle((x, y), 1.8 * scale, facecolor='#f7c75e', edgecolor='#916b18', linewidth=1.2, zorder=10, clip_on=False)
    base = plt.Rectangle((x - 0.7 * scale, y - 2.5 * scale), 1.4 * scale, 1.0 * scale, facecolor='#b0b0b0', edgecolor='#606060', zorder=9, clip_on=False)
    ax.add_patch(bulb)
    ax.add_patch(base)

def draw_map(ax, prob, report=None, population=None, title="", alpha=0.10):
    for storm in prob["storms"]:
        center = (storm["x"], storm["y"])
        ax.add_patch(Circle(center, storm["r"], facecolor="#f0a6ca", alpha=0.55, zorder=1))
        ax.add_patch(Circle(center, storm["r"] + prob["safety"], fill=False, edgecolor="#d87a99", linestyle="--", linewidth=1.2, zorder=2))
        ax.text(storm["x"], storm["y"], storm["name"], ha="center", va="center", fontsize=9, weight="bold", color="#8b0000", zorder=6)

    if "gate" in prob:
        gate = prob["gate"]
        ax.plot([gate["x"], gate["x"]], [gate["y_min"], gate["y_max"]], color="#7a3eb1", linewidth=4, zorder=7)

    if population is not None:
        for whale in population:
            xs = [prob["start"][0]] + [whale[3*k] for k in range(10)] + [prob["target"][0]]
            ys = [prob["start"][1]] + [whale[3*k+1] for k in range(10)] + [prob["target"][1]]
            ax.plot(xs, ys, color="#646e77", alpha=alpha, linewidth=0.8, zorder=3)

    for camp in prob["camps"]:
        ax.scatter(camp["x"], camp["y"], marker="D", s=28, color="#233848", zorder=8)
        ax.text(camp["x"] + 1.5, camp["y"] + 1.5, camp["name"], fontsize=8, weight="bold", color="#233848", zorder=8)

    if report is not None:
        points = report["points"]
        for i in range(len(points) - 1):
            a, b = points[i], points[i+1]
            color = "#cb3945" if i in report["bad_segments"] else "#126aaf"
            ax.plot([a[0], b[0]], [a[1], b[1]], color=color, linewidth=2.3, zorder=9)
            
        for beacon in report["beacons"]:
            if beacon["energy"] > 0.001:
                draw_light_bulb(ax, beacon["x"], beacon["y"], beacon["energy"])
            else:
                ax.scatter(beacon["x"], beacon["y"], s=25, facecolor="white", edgecolor="#126aaf", zorder=10, clip_on=False)

        status = "HỢP LỆ" if report["valid"] else "CHƯA HỢP LỆ"
        title += f"\n{status} · U={round(report['utility_sat'], 3)} · pin={round(report['total'], 1)}/220"

    for label, pt in [["S", prob["start"]], ["T", prob["target"]]]:
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

def table_on_axis(ax, title, headers, rows):
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=11, weight="bold", pad=6)
    t = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
    t.auto_set_font_size(False)
    t.set_fontsize(9)
    t.scale(1, 1.6)

def one_shot_comparison(results, summaries, labels, title, subtitle, filename):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor="#faf9f5")
    
    fig.text(0.035, 0.95, title, fontsize=20, weight="bold", color="#20394b")
    fig.text(0.035, 0.92, subtitle, fontsize=11, color="#455967")
    
    n_cases = len(results)
    width = 0.92 / n_cases
    
    for i in range(n_cases):
        res = results[i]
        ax = fig.add_axes([0.03 + width * i, 0.36, width - 0.02, 0.52])
        draw_map(ax, res["problem"], chosen_report(res), res["final_population"], 
                 f"{labels[i]} · seed {res['settings']['seed']}")
        
    ax_bar = fig.add_axes([0.04, 0.08, 0.26, 0.21])
    means = [s["u_mean"] for s in summaries]
    stds = [s["u_std"] for s in summaries]
    colors = ["#6b9dbf", "#78b195", "#dcac65"][:n_cases]
    
    ax_bar.bar(range(n_cases), means, yerr=stds, capsize=5, color=colors)
    ax_bar.set_xticks(range(n_cases))
    ax_bar.set_xticklabels(labels, fontsize=9)
    ax_bar.set_ylabel("Utility bão hòa", fontsize=10)
    ax_bar.set_ylim(0, 1.08)
    ax_bar.grid(axis="y", alpha=0.15)
    ax_bar.set_title("Trung bình ± SD mẫu (30 seed)", loc="left", fontsize=11, weight="bold")
    
    u_rows = [[labels[i], f"{s['u_mean']:.3f}", f"{s['u_std']:.3f}", f"{s['min_serv']:.3f}"] for i, s in enumerate(summaries)]
    table_on_axis(fig.add_axes([0.33, 0.08, 0.30, 0.21]), "Utility · chỉ lượt hợp lệ", ["Cấu hình", "TB", "SD", "Trại yếu"], u_rows)
    
    v_rows = []
    for i, s in enumerate(summaries):
        gate_str = f"{s['gate_n']}/30" if "gate" in results[i]["problem"] else "—"
        v_rows.append([labels[i], f"{s['valid_n']}/30", f"{s['overall_valid_n']}/30", gate_str])
        
    table_on_axis(fig.add_axes([0.66, 0.08, 0.30, 0.21]), "Độ tin cậy · mọi seed", ["Cấu hình", "Có hợp lệ", "Best overall", "Từng qua khe"], v_rows)
    
    fig.text(0.035, 0.02, "Bản đồ: ví dụ seed 7 · Bảng/Cột: tổng hợp đủ 30 seed · Xám: cả đàn · Xanh: hợp lệ · Đỏ: vi phạm bão", fontsize=9)
    
    os.makedirs("results/figures", exist_ok=True)
    fig.savefig(f"results/figures/{filename}", dpi=100)
    plt.close(fig)
    print(f"->results/figures/{filename}")

# --- 4.2 HÀM XUẤT HÌNH DIỄN BIẾN TIẾN HÓA ĐÀN (6 MỐC THỜI ĐIỂM) ---
def population_story(result, case_label, filename):
    fig, axes = plt.subplots(2, 3, figsize=(19.2, 10.8), dpi=100, facecolor="#faf9f5")
    snapshots = result["snapshots"]
    fractions = [0, 0.05, 0.2, 0.5, 0.8, 1.0]
    
    for i in range(6):
        idx = int(fractions[i] * (len(snapshots) - 1))
        snap = snapshots[idx]
        rep = evaluate(snap["position"], result["problem"])
        ax = axes[i // 3][i % 3]
        draw_map(ax, result["problem"], rep, snap["population"], 
                 f"Lượt {snap['iteration']} · Cả {len(snap['population'])} cá voi", alpha=0.13)
        
    fig.suptitle(f"{case_label} · Tiến hóa của đàn cá voi theo thời gian · seed {result['settings']['seed']}", fontsize=18, weight="bold", color="#20394b")
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    os.makedirs("results/figures", exist_ok=True)
    fig.savefig(f"results/figures/{filename}", dpi=100)
    plt.close(fig)
    print(f"->results/figures/{filename}")

# --- 4.3 HÀM XUẤT HÌNH PHÂN TÍCH PIN & HỮU DỤNG TRẠI ---
def utility_and_energy(result, case_label, filename):
    report = chosen_report(result)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), dpi=100, facecolor="#faf9f5")
    
    names = [c["name"] for c in result["problem"]["camps"]]
    axes[0].bar(names, report["satisfaction"], color="#78b195", edgecolor="#3f6d57")
    axes[0].set_ylim(0, 1.05)
    axes[0].set_ylabel("Mức bão hòa u_m", fontsize=11)
    axes[0].set_title(f"Hữu dụng thu nhận tại từng trại cứu hộ ({case_label})", fontsize=12, weight="bold")
    axes[0].grid(axis="y", alpha=0.2)
    
    for i, val in enumerate(report["satisfaction"]):
        axes[0].text(i, val + 0.02, f"{val:.2f}", ha="center", fontsize=9)
        
    axes[1].bar(["Bay", "Đèn", "Tổng cộng"], [report["flight"], report["lamps"], report["total"]], 
               color=["#6b9dbf", "#dcac65", "#78b195"], edgecolor="#2f4858")
    axes[1].axhline(220, color="#cb3945", linestyle="--", linewidth=1.5, label="Pin tối đa 220")
    axes[1].set_ylabel("Mức tiêu thụ pin (đơn vị)", fontsize=11)
    axes[1].set_title(f"Phân bổ pin ('Pin tiêu tốn cho cả việc bay và thắp sáng')", fontsize=12, weight="bold")
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].legend(loc="upper left")
    
    for i, val in enumerate([report["flight"], report["lamps"], report["total"]]):
        axes[1].text(i, val + 3, f"{val:.1f}", ha="center", fontsize=9, weight="bold")
        
    fig.suptitle(f"Phân tích năng lượng & độ hữu dụng - {case_label} · seed {result['settings']['seed']}", fontsize=16, weight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    
    os.makedirs("results/figures", exist_ok=True)
    fig.savefig(f"results/figures/{filename}", dpi=100)
    plt.close(fig)
    print(f"->results/figures/{filename}")

# --- 4.4 HÀM XUẤT HÌNH 3 VÍ DỤ SEED (TỐT / TIÊU BIỂU / KÉM) ---
def plot_three_seeds(res_best, res_typical, res_worst, case_label, filename):
    fig, axes = plt.subplots(1, 3, figsize=(19.2, 6.5), dpi=100, facecolor="#faf9f5")
    
    draw_map(axes[0], res_best["problem"], chosen_report(res_best), res_best["final_population"], 
             f"Nghiệm tốt nhất · seed {res_best['settings']['seed']}")
    draw_map(axes[1], res_typical["problem"], chosen_report(res_typical), res_typical["final_population"], 
             f"Gần trung vị (tiêu biểu) · seed {res_typical['settings']['seed']}")
    draw_map(axes[2], res_worst["problem"], chosen_report(res_worst), res_worst["final_population"], 
             f"Nghiệm thấp nhất · seed {res_worst['settings']['seed']}")
    
    fig.suptitle(f"Khảo sát tính ổn định qua 3 ví dụ - {case_label}", fontsize=17, weight="bold", color="#20394b")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    
    os.makedirs("results/figures", exist_ok=True)
    fig.savefig(f"results/figures/{filename}", dpi=100)
    plt.close(fig)
    print(f"->results/figures/{filename}")


def run_multi_seeds(problem_builder, settings_builder, n_seeds=30):
    results = []
    for s in range(1, n_seeds + 1):
        p = problem_builder()
        st = settings_builder(s)
        results.append(run_woa(p, st))
        
    valid_results = [r for r in results if r["best_valid"] is not None]
    u_vals = [r["best_valid"]["evaluation"]["utility_sat"] for r in valid_results]
    min_serv = [r["best_valid"]["evaluation"]["minimum_service"] for r in valid_results]
    
    summary = {
        "valid_n": len(valid_results),
        "overall_valid_n": sum(1 for r in results if r["best_overall"]["evaluation"]["valid"]),
        "gate_n": sum(1 for r in results if r["best_gate"] is not None),
        "u_mean": np.mean(u_vals) if u_vals else 0,
        "u_std": np.std(u_vals, ddof=1) if len(u_vals) > 1 else 0,
        "min_serv": np.mean(min_serv) if min_serv else 0
    }
    return results, summary

if __name__ == "__main__":

    
    print("\nCa A (cơ bản), Ca B (khe hẹp), Ca C (chắn đường)...")
    res_A, sum_A = run_multi_seeds(lambda: get_base_problem("co_ban"), lambda s: {"population": 30, "iterations": 100, "seed": s, "snapshot_every": 20})
    res_B, sum_B = run_multi_seeds(lambda: get_base_problem("khe_hep"), lambda s: {"population": 30, "iterations": 100, "seed": s, "snapshot_every": 20})
    res_C, sum_C = run_multi_seeds(lambda: get_base_problem("chan_duong"), lambda s: {"population": 30, "iterations": 100, "seed": s, "snapshot_every": 20})
    

    one_shot_comparison([res_A[6], res_B[6], res_C[6]], [sum_A, sum_B, sum_C], 
                         ["A · cơ bản", "B · khe hẹp", "C · chắn đường"], 
                         "Ca gốc · ba bài toán kiểm tra năng lực tìm đường", 
                         "Ba ca gốc đại diện cho ba mức độ khó địa hình khác nhau", 
                         "00_ca_goc_tong_hop.png")


    population_story(res_A[6], "Ca A · cơ bản", "ca_A_tien_hoa_dan.png")
    utility_and_energy(res_A[6], "Ca A · cơ bản", "ca_A_phan_tich_pin.png")
    
    population_story(res_B[6], "Ca B · khe hẹp", "ca_B_tien_hoa_dan.png")
    utility_and_energy(res_B[6], "Ca B · khe hẹp", "ca_B_phan_tich_pin.png")
    
    population_story(res_C[6], "Ca C · chắn đường", "ca_C_tien_hoa_dan.png")
    utility_and_energy(res_C[6], "Ca C · chắn đường", "ca_C_phan_tich_pin.png")

    valid_A = [r for r in res_A if r["best_valid"] is not None]
    valid_A_sorted = sorted(valid_A, key=lambda r: r["best_valid"]["evaluation"]["base_score"])
    
    res_best = valid_A_sorted[0]
    res_typical = valid_A_sorted[len(valid_A_sorted) // 2]
    res_worst = valid_A_sorted[-1]
    plot_three_seeds(res_best, res_typical, res_worst, "Ca A cơ bản", "ca_A_ba_seed_dai_dien.png")
