"""N8 - Thống kê từng lượt.
Giả định: U = cột utility_sat; điểm càng thấp càng tốt;
nhóm = cột id (đã cố định N/T/dimensions/active_lights); cơ sở của A_* là A_goc, của B_* là B_goc."""
import csv, json, re, statistics as st, sys, os

U_COL, SCORE_COL = "utility_sat", "base_score"
GROUP_KEYS = ("population", "iterations", "evaluations", "dimensions", "active_lights", "budget")
EXPECTED_N = 30

def num(s):
    if s is None: return None
    s = s.strip()
    if s == "" or s.lower() in ("na", "nan", "none"): return None
    return float(s)

def read(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            o = {"id": r["id"], "seed": int(r["seed"])}
            for k, v in r.items():
                if k not in ("id", "seed"): o[k] = num(v)
            for k in ("valid", "overall_valid", "gate_found"):
                o[k] = int(o[k]) if o[k] is not None else 0
            rows.append(o)
    return rows

def group(rows):
    g = {}
    for r in rows: g.setdefault(r["id"], []).append(r)
    for cid, rs in g.items():
        if len(rs) != EXPECTED_N or len({r["seed"] for r in rs}) != len(rs):
            print(f"CẢNH BÁO: {cid} có {len(rs)} dòng / {len({r['seed'] for r in rs})} seed")
        if len({tuple(r[k] for k in GROUP_KEYS) for r in rs}) > 1:
            raise SystemExit(f"{cid} trộn N/T/cấu hình khác nhau")
    return g

def vals(rs, col):
    return [r[col] for r in rs if r["valid"] == 1 and r.get(col) is not None]

def mean_sd(x):
    return (st.mean(x) if x else None, st.stdev(x) if len(x) >= 2 else None)

def fmt(v, d=4): return "" if v is None else f"{v:.{d}f}"

def summary(g, out):
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "valid", "overall_valid", "gate_found", "U_n", "U_mean", "U_sd_sample", "U_min", "U_max"])
        for cid in sorted(g):
            rs = g[cid]; n = len(rs); u = vals(rs, U_COL); m, sd = mean_sd(u)
            w.writerow([cid, f"{sum(r['valid'] for r in rs)}/{n}", f"{sum(r['overall_valid'] for r in rs)}/{n}",
                        f"{sum(r['gate_found'] for r in rs)}/{n}", len(u), fmt(m), fmt(sd),
                        fmt(min(u) if u else None), fmt(max(u) if u else None)])

def paired(g, out):
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant", "base", "pairs", "both_valid", "only_variant_valid", "only_base_valid",
                    "neither_valid", "dU_n", "dU_mean(variant-base)", "dU_sd_sample"])
        for cid in sorted(g):
            m = re.match(r"^([A-Z])_", cid)
            base = f"{m.group(1)}_goc" if m else None
            if not base or cid == base or base not in g: continue
            b = {r["seed"]: r for r in g[base]}; v = {r["seed"]: r for r in g[cid]}
            seeds = sorted(set(b) & set(v))
            both = [s for s in seeds if b[s]["valid"] and v[s]["valid"] and b[s][U_COL] is not None and v[s][U_COL] is not None]
            ov = sum(1 for s in seeds if v[s]["valid"] and not b[s]["valid"])
            ob = sum(1 for s in seeds if b[s]["valid"] and not v[s]["valid"])
            ne = sum(1 for s in seeds if not b[s]["valid"] and not v[s]["valid"])
            d = [v[s][U_COL] - b[s][U_COL] for s in both]; mm, sd = mean_sd(d)
            w.writerow([cid, base, len(seeds), len(both), ov, ob, ne, len(d), fmt(mm), fmt(sd)])

def representatives(g, out):
    res = {"rule": f"Trong lượt valid=1, chọn seed có {SCORE_COL} gần trung vị nhất (hòa: seed nhỏ hơn); "
                   f"ghi thêm seed tốt nhất (thấp nhất) và kém nhất (cao nhất). Không chọn theo kết quả đẹp.",
           "groups": {}}
    for cid in sorted(g):
        ok = [r for r in g[cid] if r["valid"] == 1 and r.get(SCORE_COL) is not None]
        if not ok:
            res["groups"][cid] = {"note": "chưa có ví dụ hợp lệ"}; continue
        med = st.median(r[SCORE_COL] for r in ok)
        pick = lambda r: {"seed": r["seed"], SCORE_COL: r[SCORE_COL], "U": r[U_COL]}
        res["groups"][cid] = {"n_valid": len(ok), "median_" + SCORE_COL: med,
            "typical": pick(min(ok, key=lambda r: (abs(r[SCORE_COL] - med), r["seed"]))),
            "best": pick(min(ok, key=lambda r: r[SCORE_COL])), "worst": pick(max(ok, key=lambda r: r[SCORE_COL]))}
    with open(out, "w", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "trials.csv"
    d = sys.argv[2] if len(sys.argv) > 2 else "results"
    os.makedirs(d, exist_ok=True)
    g = group(read(src))
    summary(g, f"{d}/summary.csv"); paired(g, f"{d}/paired.csv"); representatives(g, f"{d}/representatives.json")
    print("Xong:", sorted(g))
