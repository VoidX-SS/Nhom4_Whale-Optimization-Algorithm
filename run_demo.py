"""Chạy nhanh một lần; muốn điều khiển cả đàn, mở app.py hoặc Colab."""
import argparse
from src.n4_hoang_yen_du_lieu import ROOT, default_settings, load_problem
from src.n3_phuc_khang_danh_gia import evaluate
from src.n6_van_lam_woa import woa
from src.n7_ngoc_thanh_thuc_nghiem import save_json
from src.n10_bao_ngoc_demo import tell_result
from src.n9_trang_nguyen_ve_hinh import plot_population, chosen_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", choices=["co_ban", "khe_hep", "chan_duong"], default="co_ban")
    parser.add_argument("--iterations", type=int, default=800)
    parser.add_argument("--population", type=int, default=30)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--l", choices=["shared_l", "independent_l"], default="shared_l")
    parser.add_argument("--boundary", choices=["clip", "reinit"], default="clip")
    parser.add_argument("--a", choices=["linear", "cosine", "quadratic"], default="linear")
    parser.add_argument("--lights", type=int, default=10)
    args = parser.parse_args()
    p = load_problem(args.map)
    p["active_lights"] = args.lights
    s = default_settings()
    s.update({"iterations": args.iterations, "population": args.population, "seed": args.seed,
              "l_mode": args.l, "boundary": args.boundary, "a_mode": args.a})
    r = woa(evaluate, p, s, True)
    output = ROOT / "results" / "user_demo"
    save_json(output / "result.json", r)
    fig = plot_population(p, chosen_report(r), r["final_population"], "Kết quả và cả đàn cuối")
    fig.savefig(output / "map.png", dpi=150)
    tell_result(r)
