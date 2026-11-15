"""
app.py - Giao diện Streamlit cho bài demo Đom Đóm (UAV + WOA) - Bảo Ngọc (N10).
Chạy bằng lệnh: streamlit run app.py
"""
import time
import matplotlib.pyplot as plt
import streamlit as st

from src.n10_bao_ngoc_demo import (
    CASE_LABELS,
    export_backup_html,
    export_figure_png_bytes,
    get_problem_case,
    load_result_json,
    render_demo_figure,
    run_demo_experiment,
    serialize_result_json,
)

st.set_page_config(page_title="Demo WOA · Đom Đóm", layout="wide")
st.title("Demo Thuật toán Tối ưu Cá voi (WOA) · Bài toán Đom Đóm")
st.caption("Kết nối trực tiếp lõi WOA (N6), mô hình hình học & năng lượng (N1–N4), biến thể ngách (N5) và trực quan hóa đàn (N9–N10).")

# --- THANH ĐIỀU KHIỂN BÊN TRÁI ---
with st.sidebar:
    st.header("1. Chọn đề & Tham số WOA")
    case_id = st.selectbox("Ca bài toán", options=["A", "B", "C"], format_func=lambda c: CASE_LABELS[c])
    n_whales = st.number_input("Số cá voi (N)", min_value=5, max_value=100, value=30, step=5)
    n_iter = st.number_input("Số lượt (T)", min_value=10, max_value=2000, value=300, step=50)
    seed = st.number_input("Hạt giống ngẫu nhiên (Seed)", min_value=0, max_value=99999, value=7, step=1)
    snapshot_every = st.selectbox("Lưu snapshot mỗi (lượt)", options=[1, 2, 5, 10, 20], index=2)

    st.header("2. Bốn nhóm lựa chọn (4 Ngách)")
    a_mode = st.selectbox("Ngách 3 · Lịch giảm a", options=["linear", "cosine", "quadratic"], index=0)
    l_mode = st.selectbox("Ngách 1 · Kiểu l nhánh xoắn", options=["shared_l", "independent_l"], index=0)
    boundary_mode = st.selectbox("Ngách 2 · Sửa biên", options=["clip", "reinit"], index=0)
    active_lights = st.selectbox("Ngách 4 · Số đèn tối đa (K)", options=[10, 8, 6], index=0)

    st.header("3. Chỉnh đích T & Ba vùng bão")
    base_prob = get_problem_case(case_id)
    col_tx, col_ty = st.columns(2)
    target_x = col_tx.number_input("Đích T · x", min_value=0.0, max_value=100.0, value=float(base_prob["target"][0]), step=1.0)
    target_y = col_ty.number_input("Đích T · y", min_value=0.0, max_value=100.0, value=float(base_prob["target"][1]), step=1.0)

    storms_xyr = []
    for idx, st_obj in enumerate(base_prob["storms"]):
        st.markdown(f"**Bão {st_obj['name']}**")
        c1, c2, c3 = st.columns(3)
        sx = c1.number_input(f"x_{idx+1}", 0.0, 100.0, float(st_obj["x"]), 1.0, key=f"sx_{case_id}_{idx}")
        sy = c2.number_input(f"y_{idx+1}", 0.0, 100.0, float(st_obj["y"]), 1.0, key=f"sy_{case_id}_{idx}")
        sr = c3.number_input(f"r_{idx+1}", 1.0, 40.0, float(st_obj["r"]), 0.5, key=f"sr_{case_id}_{idx}")
        storms_xyr.append((sx, sy, sr))

    run_btn = st.button("Chạy WOA", type="primary", use_container_width=True)

    st.divider()
    st.header("4. Mở lại kết quả đã lưu")
    uploaded_json = st.file_uploader("Tải lên file .json đã xuất trước đó", type=["json"])

# --- XỬ LÝ CHẠY HOẶC NẠP FILE LƯU ---
if "demo_result" not in st.session_state:
    st.session_state["demo_result"] = run_demo_experiment(
        case_id="A", n_whales=30, n_iter=200, seed=7, snapshot_every=5
    )
    st.session_state["source_label"] = "Kết quả chạy mặc định ban đầu"

if run_btn:
    with st.spinner("Đang chạy thuật toán WOA qua lõi N6..."):
        st.session_state["demo_result"] = run_demo_experiment(
            case_id=case_id,
            n_whales=int(n_whales),
            n_iter=int(n_iter),
            seed=int(seed),
            a_mode=a_mode,
            l_mode=l_mode,
            boundary_mode=boundary_mode,
            active_lights=int(active_lights),
            target_xy=(target_x, target_y),
            storms_xyr=storms_xyr,
            snapshot_every=int(snapshot_every),
        )
        st.session_state["source_label"] = "Kết quả vừa chạy trực tiếp"

if uploaded_json is not None:
    try:
        loaded = load_result_json(uploaded_json.getvalue().decode("utf-8"))
        st.session_state["demo_result"] = loaded
        st.session_state["source_label"] = f"Đang phát lại từ file lưu: {uploaded_json.name} (giữ nguyên map gốc trong file)"
    except Exception as err:
        st.error(f"Không đọc được file JSON: {err}")

result = st.session_state["demo_result"]
st.info(st.session_state["source_label"])

# --- THANH ĐIỀU KHIỂN PHÁT LẠI TOÀN ĐÀN (REPLAY) ---
snapshots = result["snapshots"]
col_v, col_s, col_chk, col_play = st.columns([2, 4, 1.5, 1.5])
view_mode = col_v.radio(
    "Chế độ xem nghiệm",
    options=["best_valid", "best_overall"],
    format_func=lambda m: "best_valid (Hợp lệ)" if m == "best_valid" else "best_overall (J thấp nhất)",
    horizontal=True,
)
snap_idx = col_s.slider(
    "Mốc phát lại (Snapshot)",
    min_value=0,
    max_value=len(snapshots) - 1,
    value=len(snapshots) - 1,
    format="Mốc %d",
)
show_swarm = col_chk.checkbox("Hiện cả đàn", value=True)
play_btn = col_play.button("Play / Replay", use_container_width=True)

plot_placeholder = st.empty()

if play_btn:
    for idx in range(len(snapshots)):
        fig = render_demo_figure(result, snapshot_idx=idx, view_mode=view_mode, show_swarm=show_swarm)
        plot_placeholder.pyplot(fig)
        plt.close(fig)
        time.sleep(0.12)
else:
    fig = render_demo_figure(result, snapshot_idx=snap_idx, view_mode=view_mode, show_swarm=show_swarm)
    plot_placeholder.pyplot(fig)
    png_bytes = export_figure_png_bytes(fig)
    plt.close(fig)

    # Bảng chỉ số tổng hợp & tải file
    rep_valid = result["reports"]["best_valid"]
    rep_overall = result["reports"]["best_overall"]
    if rep_valid is None:
        st.warning("Cảnh báo: Chưa tìm được nghiệm hợp lệ nào trong lượt chạy này!")

    rep_show = rep_valid if (view_mode == "best_valid" and rep_valid is not None) else rep_overall
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Trạng thái", "HỢP LỆ" if rep_show["valid"] else "VI PHẠM")
    m2.metric("Hữu dụng U", f"{rep_show['utility_sat']:.4f}")
    m3.metric("Trại yếu u_min", f"{rep_show['minimum_service']:.4f}")
    m4.metric("Pin tổng", f"{rep_show['total']:.1f} / 220")
    m5.metric("Điểm mục tiêu f0", f"{rep_show.get('f0', rep_show['base_score']):.4f}")
    d1, d2, d3 = st.columns(3)
    cfg = result["config"]
    prefix = f"woa_{cfg['case_id']}_seed{cfg['seed']}_{cfg['a_mode']}"
    d1.download_button("Tải ảnh PNG", data=png_bytes, file_name=f"{prefix}.png", mime="image/png", use_container_width=True)
    d2.download_button("Tải kết quả JSON", data=serialize_result_json(result), file_name=f"{prefix}.json", mime="application/json", use_container_width=True)
    d3.download_button("Tải bản HTML dự phòng", data=export_backup_html(result), file_name=f"{prefix}.html", mime="text/html", use_container_width=True)