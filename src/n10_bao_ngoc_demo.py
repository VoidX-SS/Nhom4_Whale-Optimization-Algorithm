"""Bảo Ngọc: giao diện chỉ gọi cùng hàm woa, không có một lõi khác.

Có bản Streamlit trên máy và bảng điều khiển ipywidgets trong Colab.
Mình giữ phần nối nút ở đây, để các bạn học công thức không phải đọc UI.
"""
import json
import matplotlib.pyplot as plt
from src.n4_hoang_yen_du_lieu import ROOT, load_problem, default_settings
from src.n3_phuc_khang_danh_gia import evaluate
from src.n6_van_lam_woa import woa
from src.n9_trang_nguyen_ve_hinh import chosen_report, plot_population
from src.n7_ngoc_thanh_thuc_nghiem import save_json


def load_demo(case="A_goc"):
    path = ROOT / "results" / "demos" / (case + "_typical.json")
    if not path.exists():
        path = ROOT / "results" / "runs" / case / "seed_07.json"
    with open(path, encoding="utf-8") as file:
        result = json.load(file)
    if not result["snapshots"]:
        archive = result["best_valid"]
        if archive is None:
            archive = result["best_overall"]
        result["snapshots"] = [{"iteration": result["settings"]["iterations"] - 1,
                                "population": result["final_population"], "position": archive["position"],
                                "overall_position": result["best_overall"]["position"]}]
    return result


def tell_result(result):
    report = chosen_report(result)
    if result["best_valid"] is None:
        print("Lần này chưa có đường đủ điều kiện; hình không được coi là nghiệm hợp lệ.")
    else:
        print("Đã có đường hợp lệ. Utility:", round(report["utility_sat"], 4))
    print("Pin:", round(report["total"], 2), "/220 · Đường dài:", round(report["length"], 2))
    print("Best overall hợp lệ:", result["best_overall"]["evaluation"]["valid"])
    print("Từng tìm được đường hợp lệ qua khe:", result["best_gate"] is not None)


def replay_figure(result, index, show_all=True, alpha=0.1, show_overall=False):
    snapshots = result["snapshots"]
    index = max(0, min(index, len(snapshots) - 1))
    snapshot = snapshots[index]
    position = snapshot["position"]
    if show_overall:
        position = snapshot["overall_position"]
    report = evaluate(position, result["problem"])
    population = None
    if show_all:
        population = snapshot["population"]
    return plot_population(result["problem"], report, population,
                           "Lượt " + str(snapshot["iteration"]) + " · seed " + str(result["settings"]["seed"]), alpha)


# PANEL như một bàn điều khiển chung: mỗi ngăn giữ một ô chọn hay nút.
PANEL = {}


def notebook_live(snapshot, overall, valid):
    from IPython.display import clear_output, display
    if not PANEL["live"].value:
        return
    archive = valid
    if archive is None:
        archive = overall
    clear_output(wait=True)
    print("Đang chạy lượt", snapshot["iteration"], "— xám là toàn bộ đàn.")
    fig = plot_population(PANEL["running_problem"], archive["evaluation"], snapshot["population"],
                          "Đàn đang tìm", 0.12)
    display(fig)
    plt.close(fig)


def notebook_run(button):
    from IPython.display import clear_output, display
    problem = load_problem(PANEL["map"].value)
    problem["active_lights"] = PANEL["lights"].value
    for i in range(3):
        for key in ["x", "y", "r"]:
            problem["storms"][i][key] = PANEL["storms"][i][key].value
    settings = default_settings()
    for key in ["population", "iterations", "seed", "a_mode", "l_mode", "boundary"]:
        settings[key] = PANEL[key].value
    settings["snapshot_every"] = PANEL["every"].value
    PANEL["running_problem"] = problem
    PANEL["busy"] = True
    with PANEL["output"]:
        clear_output(wait=True)
        result = woa(evaluate, problem, settings, True, notebook_live)
        PANEL["result"] = result
        PANEL["replay"].max = len(result["snapshots"]) - 1
        PANEL["play"].max = len(result["snapshots"]) - 1
        PANEL["replay"].value = len(result["snapshots"]) - 1
        clear_output(wait=True)
        tell_result(result)
        fig = replay_figure(result, len(result["snapshots"]) - 1)
        display(fig)
        plt.close(fig)
        save_json(ROOT / "results" / "user_demo" / "result.json", result)
    PANEL["busy"] = False


def notebook_replay(change):
    from IPython.display import clear_output, display
    if PANEL.get("busy", False) or "result" not in PANEL:
        return
    with PANEL["output"]:
        clear_output(wait=True)
        fig = replay_figure(PANEL["result"], PANEL["replay"].value)
        display(fig)
        plt.close(fig)


def notebook_map(change):
    problem = load_problem(PANEL["map"].value)
    for i in range(3):
        for key in ["x", "y", "r"]:
            PANEL["storms"][i][key].value = problem["storms"][i][key]


def show_notebook_controls():
    import ipywidgets as widgets
    from IPython.display import display
    PANEL["map"] = widgets.Dropdown(options=["co_ban", "khe_hep", "chan_duong"], description="Bản đồ")
    PANEL["population"] = widgets.IntSlider(value=30, min=10, max=100, description="Cá voi N")
    PANEL["iterations"] = widgets.IntSlider(value=800, min=50, max=3000, step=50, description="Lượt T")
    PANEL["seed"] = widgets.IntText(value=7, description="Seed")
    PANEL["a_mode"] = widgets.Dropdown(options=["linear", "cosine", "quadratic"], description="Lịch a")
    PANEL["l_mode"] = widgets.Dropdown(options=["shared_l", "independent_l"], description="Kiểu l")
    PANEL["boundary"] = widgets.Dropdown(options=["clip", "reinit"], description="Biên")
    PANEL["lights"] = widgets.IntSlider(value=10, min=1, max=10, description="Tối đa đèn")
    PANEL["every"] = widgets.IntSlider(value=10, min=1, max=50, description="Lưu mỗi")
    PANEL["live"] = widgets.Checkbox(value=False, description="Xem cả đàn khi đang chạy (sẽ chậm hơn)")
    PANEL["storms"] = []
    problem = load_problem()
    for storm in problem["storms"]:
        fields = {}
        for key in ["x", "y", "r"]:
            fields[key] = widgets.FloatText(value=storm[key], description=storm["name"] + " " + key)
        PANEL["storms"].append(fields)
    run = widgets.Button(description="Chạy WOA", button_style="success")
    run.on_click(notebook_run)
    PANEL["output"] = widgets.Output()
    PANEL["replay"] = widgets.IntSlider(value=0, min=0, max=1, description="Khung xem")
    PANEL["play"] = widgets.Play(value=0, min=0, max=1, interval=350)
    PANEL["link"] = widgets.link((PANEL["play"], "value"), (PANEL["replay"], "value"))
    PANEL["replay"].observe(notebook_replay, names="value")
    PANEL["map"].observe(notebook_map, names="value")
    display(widgets.VBox([PANEL["map"], PANEL["population"], PANEL["iterations"], PANEL["seed"],
                          PANEL["a_mode"], PANEL["l_mode"], PANEL["boundary"], PANEL["lights"], PANEL["every"], PANEL["live"]]))
    for fields in PANEL["storms"]:
        display(widgets.HBox([fields["x"], fields["y"], fields["r"]]))
    display(run, widgets.HBox([PANEL["play"], PANEL["replay"]]), PANEL["output"])
