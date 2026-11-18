"""Giao diện trên máy: python -m streamlit run app.py

Phần trang dùng thư viện Streamlit. Công thức vẫn ở n5/n6 như Colab.
"""
import io
import json
import matplotlib.pyplot as plt
import streamlit as st
from src.n4_hoang_yen_du_lieu import load_problem, default_settings
from src.n3_phuc_khang_danh_gia import evaluate
from src.n6_van_lam_woa import woa
from src.n9_trang_nguyen_ve_hinh import plot_population, chosen_report, utility_and_energy
from src.n10_bao_ngoc_demo import load_demo, replay_figure

st.set_page_config(page_title="Đom Đóm · WOA", layout="wide")
st.title("Đom Đóm · nhìn cả đàn WOA tìm đường")
st.caption("30 biến · pin 220 · q=0.5 · b=1 · utility bão hòa · không phạt gấp khúc")
map_name = st.sidebar.selectbox("Bản đồ", ["co_ban", "khe_hep", "chan_duong"], key="map")
problem = load_problem(map_name)
with st.sidebar.form("controls"):
    N = st.slider("Số cá voi N", 10, 100, 30, key="N")
    T = st.slider("Số lượt chấm đàn T", 50, 3000, 800, 50, key="T")
    seed = st.number_input("Seed", min_value=1, max_value=9999, value=7, key="seed")
    a_mode = st.selectbox("Lịch giảm a", ["linear", "cosine", "quadratic"], key="a")
    l_mode = st.selectbox("Cách dùng l", ["shared_l", "independent_l"], key="l")
    boundary = st.selectbox("Khi vượt biên", ["clip", "reinit"], key="boundary")
    lights = st.slider("Số đèn phát tối đa (10 điểm đường bay)", 1, 10, 10, key="lights")
    every = st.slider("Lưu một khung mỗi bao nhiêu lượt?", 1, 50, 10, key="every")
    live = st.checkbox("Xem cả đàn khi đang tính", value=False, key="live")
    st.caption("Sửa được cả ba vùng bão. Đổi bản đồ sẽ nạp lại tọa độ mặc định.")
    for i in range(3):
        storm = problem["storms"][i]
        st.markdown("**" + storm["name"] + "**")
        for key in ["x", "y", "r"]:
            field_key = map_name + "_" + str(i) + "_" + key
            minimum = 0.1 if key == "r" else 0.0
            storm[key] = st.number_input(storm["name"] + " " + key, min_value=minimum,
                                         max_value=100.0, value=float(storm[key]), step=1.0, key=field_key)
    run = st.form_submit_button("Chạy WOA", type="primary")

problem["active_lights"] = lights
progress = st.empty()
live_area = st.empty()


def show_live(snapshot, overall, valid):
    progress.progress((snapshot["iteration"] + 1) / T, text="Đang chấm lượt " + str(snapshot["iteration"]))
    if live:
        archive = valid
        if archive is None:
            archive = overall
        fig = plot_population(problem, archive["evaluation"], snapshot["population"], "Đàn đang tìm", 0.1)
        live_area.pyplot(fig)
        plt.close(fig)


if run:
    settings = default_settings()
    settings.update({"population": N, "iterations": T, "seed": int(seed),
                     "a_mode": a_mode, "l_mode": l_mode, "boundary": boundary, "snapshot_every": every})
    st.session_state["result"] = woa(evaluate, problem, settings, True, show_live)
    progress.empty()
    live_area.empty()
    st.session_state["replay"] = len(st.session_state["result"]["snapshots"]) - 1

case = st.selectbox("Hoặc mở một ca gốc đã lưu", ["A_goc", "B_goc", "C_goc"], key="saved_case")
if st.button("Mở bản lưu", key="open_saved"):
    st.session_state["result"] = load_demo(case)
    st.session_state["replay"] = len(st.session_state["result"]["snapshots"]) - 1
    st.info("Đang mở kết quả đã tính; các nút bên trái chưa chạy lại đề này.")

if "result" in st.session_state:
    result = st.session_state["result"]
    report = chosen_report(result)
    original = result["settings"]
    st.subheader("Kết quả của lần chạy đã ghi")
    st.write(result["problem"]["name"], "· seed", original["seed"], "· N", original["population"],
             "· T", original["iterations"], "·", original["l_mode"], original["boundary"], original["a_mode"])
    if result["best_valid"] is None:
        st.warning("Chưa tìm thấy nghiệm hợp lệ. Hình vẫn hiện phương án chưa đủ điều kiện.")
    columns = st.columns(4)
    columns[0].metric("Utility bão hòa", round(report["utility_sat"], 4))
    columns[1].metric("Tổng pin / 220", round(report["total"], 2))
    columns[2].metric("Best overall hợp lệ", str(result["best_overall"]["evaluation"]["valid"]))
    columns[3].metric("Từng qua khe hợp lệ", str(result["best_gate"] is not None))
    show_all = st.checkbox("Hiện toàn bộ đàn bằng các đường xám", value=True, key="all")
    show_overall = st.checkbox("Xem best_overall thay sổ hợp lệ", value=False, key="overall")
    alpha = st.slider("Độ đậm của đàn xám", 0.02, 0.3, 0.1, 0.02, key="alpha")
    index = 0
    if len(result["snapshots"]) > 1:
        index = st.slider("Xem lại khung", 0, len(result["snapshots"]) - 1, key="replay")
    fig = replay_figure(result, index, show_all, alpha, show_overall)
    st.pyplot(fig)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    st.download_button("Tải hình khung này", buffer.getvalue(), "woa_khung.png", "image/png")
    plt.close(fig)
    fig = utility_and_energy(result)
    st.pyplot(fig)
    plt.close(fig)
    st.download_button("Tải dữ liệu lần chạy", json.dumps(result, ensure_ascii=False), "woa_result.json", "application/json")
else:
    st.info("Chọn đề và nhấn Chạy WOA, hoặc mở một bản lưu. Cả hai đều dùng chung lõi Python.")
    fig = plot_population(problem, None, None, "Đề đang chọn")
    st.pyplot(fig)
    plt.close(fig)
