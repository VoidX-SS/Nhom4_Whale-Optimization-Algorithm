# Đom Đóm — Cài Đặt Và Đối Chứng Thuật Toán Tối Ưu Hóa Bầy Cá Voi (WOA)

> **Nhóm 4** · Nghiên cứu cơ chế tìm kiếm, cài đặt bám sát mã tác giả (Mirjalili & Lewis, 2016) và kiểm chứng thực nghiệm trên bài toán định tuyến UAV kết hợp phân bổ pin phát tín hiệu.

---

## 1. Mở nhanh kết quả và giao diện

* **Xem ngay kết quả đã chạy:** Mở file `MO_KET_QUA.html` bằng trình duyệt web. Toàn bộ bảng số liệu và 17 ảnh phân tích độ phân giải `1920 × 1080` nằm sẵn trong `results/figures/` (trong đó 6 ảnh `*_ONE_SHOT.png` tóm tắt 6 đối chứng của 4 ngách).
* **Chạy giao diện điều khiển trên máy cá nhân (Streamlit):**

      python -m pip install -r requirements.txt
      python -m streamlit run app.py

  Giao diện cho phép đổi số cá voi $N$, số lượt $T$, `seed`, chỉnh tọa độ/bán kính 3 vùng bão, chọn 4 ngách thuật toán, bật xem cả đàn cá voi trong lúc tính và kéo thanh trượt `Replay` để phát lại quá trình hội tụ.
* **Chạy trên Google Colab:** Tải `demo_colab.ipynb` lên Google Colab, chạy ô chuẩn bị và tải gói `.zip` của repository lên để mở bảng điều khiển `ipywidgets` (đầy đủ nút chạy, chỉnh 3 bão, phát lại quỹ đạo và xuất file `PNG`, `JSON`, `HTML`).
* **Chạy thử một lượt từ dòng lệnh:**

      python run_demo.py --map khe_hep --l independent_l --iterations 800

---

## 2. Phát biểu bài toán Đom Đóm

### Không gian tìm kiếm (30 biến)
Trên bản đồ 2D kích thước $100 \times 100$, UAV xuất phát từ $S(0, 50)$, bay qua 10 điểm trung gian $(x_k, y_k)$ và kết thúc tại $T(100, 50)$ để vận hành các thiết bị phát tín hiệu (**đèn đom đóm**) hỗ trợ 8 trại có trọng số nhu cầu $w_m$ khác nhau, đồng thời tránh 3 vùng bão hình tròn với biên an toàn 2 đơn vị.

Mỗi cá voi trong quần thể là một vector gồm **30 biến số thực**:

$$\mathbf{X} = [x_1, y_1, e_1, x_2, y_2, e_2, \dots, x_{10}, y_{10}, e_{10}]$$

* Tọa độ $(x_k, y_k) \in [0, 100]^2$: thứ tự đi theo đúng chỉ số $1 \to 10$, không ép sắp xếp theo trục $x$ để đường bay có thể linh hoạt quay đầu khi cần.
* Mức pin đề xuất $e_k \in [0, 25]$: trong bản cơ sở, tối đa 10 đèn cùng phát; ở ngách giới hạn $K \in \{6, 8, 10\}$, chỉ giữ lại $K$ đèn có mức pin đề xuất cao nhất, các đèn còn lại tắt ($\tilde{e}_k = 0$) nhưng vị trí đó vẫn là điểm trung gian trên đường bay.

### Năng lượng, tín hiệu và hàm mục tiêu
* **Túi pin chung $220$:** Tổng chiều dài $L$ qua 11 đoạn thẳng tiêu tốn $E_{\text{bay}} = 0.45 \times L$; các đèn bật tiêu tốn $E_{\text{đèn}} = \sum_{k=1}^{10} \tilde{e}_k$. Phương án hợp lệ phải thỏa $E_{\text{tổng}} = E_{\text{bay}} + E_{\text{đèn}} \le 220$.
* **Tín hiệu và độ hữu dụng bão hòa:** Trại $m$ nhận tín hiệu cộng dồn từ mọi đèn đang bật theo thang khoảng cách đặc trưng $18$:

  $$I_m = \sum_{k=1}^{10} \frac{\tilde{e}_k}{1 + \frac{d_{km}^2}{18^2}}, \qquad u_m = 1 - e^{-0.1 \times I_m}$$

  Chỉ số toàn hệ thống là trung bình có trọng số $U = \frac{\sum_{m=1}^{8} w_m u_m}{\sum_{m=1}^{8} w_m} \in [0, 1)$, đi kèm $u_{\min} = \min_{m=1..8} u_m$ để theo dõi mức phục vụ của trại thiệt thòi nhất.
* **Hàm mục tiêu cần cực tiểu hóa:**

  $$\text{base} = -U + 0.12 \times \frac{L}{100}$$

  $$J = \text{base} + 100 \cdot \text{collision} + 30 \cdot \text{over\_pin}^2 + 100 \cdot \text{outside\_map}$$

* **Ba sổ ghi (không sửa nghiệm hậu kiểm):**
  * `best_overall`: lưu cá voi có $J$ thấp nhất để dẫn dắt cả đàn.
  * `best_valid`: lưu nghiệm hợp lệ (không lấn bão, không vượt pin, nằm trong bản đồ) có $\text{base}$ thấp nhất.
  * `best_gate`: lưu nghiệm hợp lệ từng đi qua cổng khe $x = 40, y \in [47, 53]$ để kiểm tra riêng trên Ca B.

### Ba kịch bản bản đồ (`data/`)
| Ký hiệu | File dữ liệu | Đặc điểm địa hình |
| :--- | :--- | :--- |
| **Ca A** | `data/co_ban.json` | Bản đồ cơ bản với 3 vùng bão bố trí mở |
| **Ca B** | `data/khe_hep.json` | Hai vùng bão tạo khe hẹp tại cổng $x = 40, y \in [47, 53]$ (vẫn cho phép đi vòng ngoài) |
| **Ca C** | `data/chan_duong.json` | Ba vùng bão chắn ngang trục đường chính từ $S$ đến $T$ |

---

## 3. Lõi WOA và Bốn ngách đối chứng

### Đối chiếu mã tác giả (`tham_khao_tac_gia`)
Lõi thuật toán trong `src/n5_quynh_ngan_buoc_woa.py` và `src/n6_van_lam_woa.py` bám sát cấu trúc mã MATLAB công bố của Mirjalili & Lewis (2016):
* Dùng hệ số vô hướng $A, C$; khi $|A| \ge 1$ và $p < 0.5$, cá voi tham khảo ngẫu nhiên được chọn lại bên trong vòng lặp từng chiều.
* Cập nhật vị trí tại chỗ theo 3 nhánh (bao vây con mồi, tìm kiếm ngẫu nhiên và đường xoắn ốc với $b = 1$), giữ đúng thứ tự **sửa biên $\to$ chấm điểm $\to$ cập nhật sổ** với đúng $N \times T$ lượt chấm.

### Cấu hình cơ sở và Bốn ngách nghiên cứu (`docs/03_bon_ngach.md`)
Cấu hình cơ sở đặt $N = 30$, $T = 800$ ($24.000$ lượt chấm/seed), lịch giảm $a$ tuyến tính (`linear`), hệ số $l$ dùng chung (`shared_l`), xử lý biên bằng cắt tường (`clip`) và tối đa $K = 10$ đèn. Bốn đối chứng đơn yếu tố gồm:

1. **Hệ số xoắn ốc $l$ (`shared_l` vs. `independent_l`):** So sánh dùng một giá trị $l \in [-1, 1]$ chung cho cả vector nghiệm với bốc độc lập $l_j$ cho từng biến $j = 1 \dots 30$ trên Ca A và Ca B.
2. **Xử lý vượt biên (`clip` vs. `reinit`):** So sánh đưa tọa độ vượt biên về sát cạnh bản đồ với khởi tạo lại ngẫu nhiên riêng thành phần vượt biên trên Ca A và Ca B.
3. **Lịch giảm tham số $a$ (`linear` vs. `cosine` vs. `quadratic`):** Với $u = t / T$, đối chứng $a = 2 - 2u$, $a = 1 + \cos(\pi u)$ và $a = 2(1 - u)^2$ trên Ca B.
4. **Giới hạn số đèn phát tối đa ($K \in \{6, 8, 10\}$ trên 30 biến):** Giữ nguyên 10 điểm đường bay (30 biến), chỉ kích hoạt tối đa $K$ đèn có pin đề xuất lớn nhất; kèm phép kiểm chứng bao hàm mọi nghiệm $K = 6$ hợp lệ vào không gian $K = 10$ (`results/K_embedding_check.csv`).

---

## 4. Tổng hợp kết quả thực nghiệm (420 lượt chạy)

### A. Kiểm chuẩn hàm chuẩn 30 chiều (`results/benchmark_summary.csv`, $N = 30, T = 500$)
| Hàm kiểm chuẩn | Số seed | Số lượt đạt ngưỡng | Giá trị tốt nhất (`mean ± std`) |
| :--- | :---: | :---: | :---: |
| **Sphere (30D)** | 30 | **30 / 30** | $3.18 \times 10^{-74} \pm 9.14 \times 10^{-74}$ |
| **Quadratic (30D)** | 30 | **30 / 30** | $1.21 \times 10^{-14} \pm 3.36 \times 10^{-14}$ |
| **Rastrigin (30D)** | 30 | **30 / 30** | $5.92 \times 10^{-17} \pm 3.24 \times 10^{-16}$ |

### B. Kết quả trên bài toán Đom Đóm (`results/summary.csv`, $N = 30, T = 800$, 30 seed/cấu hình)
| Cấu hình | Hợp lệ (`valid_n`) | `best_overall` hợp lệ | Qua khe B (`gate_found`) | Utility $U$ (`mean ± std`) | Phục vụ tối thiểu $u_{\min}$ | Điểm gốc `base` (`mean ± std`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ca A — Cơ sở (`A_goc`)** | 29/30 | 0/30 | — | $0.659 \pm 0.141$ | $0.409 \pm 0.125$ | $-0.364 \pm 0.157$ |
| **Ca A — $l$ độc lập (`A_l_independent`)** | **30/30** | **8/30** | — | $0.790 \pm 0.108$ | $0.582 \pm 0.142$ | **$-0.583 \pm 0.141$** |
| **Ca A — Sửa biên `re-init` (`A_reinit`)** | **30/30** | 0/30 | — | **$0.823 \pm 0.046$** | **$0.612 \pm 0.075$** | $-0.553 \pm 0.074$ |
| **Ca A — Tối đa 6 đèn (`A_den_6`)** | 29/30 | 2/30 | — | $0.722 \pm 0.109$ | $0.456 \pm 0.118$ | $-0.461 \pm 0.167$ |
| **Ca A — Tối đa 8 đèn (`A_den_8`)** | 29/30 | 0/30 | — | $0.636 \pm 0.171$ | $0.390 \pm 0.148$ | $-0.342 \pm 0.205$ |
| **Ca B — Cơ sở (`B_goc`)** | 30/30 | 5/30 | 2/30 | $0.558 \pm 0.183$ | $0.336 \pm 0.166$ | $-0.305 \pm 0.176$ |
| **Ca B — $l$ độc lập (`B_l_independent`)** | 30/30 | 1/30 | 2/30 | $0.693 \pm 0.108$ | $0.450 \pm 0.111$ | **$-0.466 \pm 0.114$** |
| **Ca B — Sửa biên `re-init` (`B_reinit`)** | 26/30 | 2/30 | **5/30** | **$0.708 \pm 0.115$** | **$0.463 \pm 0.124$** | $-0.414 \pm 0.159$ |
| **Ca B — Lịch $a$ `cosine` (`B_a_cosine`)** | 30/30 | 4/30 | 1/30 | $0.555 \pm 0.135$ | $0.318 \pm 0.111$ | $-0.304 \pm 0.130$ |
| **Ca B — Lịch $a$ `quadratic` (`B_a_quadratic`)** | 30/30 | 8/30 | 4/30 | $0.546 \pm 0.140$ | $0.313 \pm 0.111$ | $-0.282 \pm 0.120$ |
| **Ca C — Cơ sở (`C_goc`)** | 29/30 | 6/30 | — | $0.647 \pm 0.123$ | $0.401 \pm 0.118$ | $-0.377 \pm 0.130$ |

**Ghi nhận chính từ bảng số liệu:**
* Tách riêng hệ số $l$ theo từng chiều nâng mức hữu dụng trung bình từ $0.659$ lên $0.790$ ở Ca A và từ $0.558$ lên $0.693$ ở Ca B, nhưng trên Ca B số seed đi qua khe vẫn giữ ở mức $2/30$.
* Xử lý biên `re-init` tăng số seed đi qua khe trên Ca B lên $5/30$ và đạt $U = 0.708$ trong nhóm hợp lệ, nhưng tỷ lệ tìm được nghiệm hợp lệ giảm từ $30/30$ xuống $26/30$.
* Ba lịch giảm $a$ (`linear`, `cosine`, `quadratic`) trên Ca B đều đạt $30/30$ lượt hợp lệ với mức hữu dụng tương đương ($0.558$, $0.555$, $0.546$).
* Ở ngách giới hạn số đèn, cả $29/29$ nghiệm hợp lệ của $K = 6$ đều giữ nguyên tính hợp lệ và điểm mục tiêu khi ánh xạ sang $K = 10$ (`results/K_embedding_check.csv`), cho thấy kết quả $U = 0.722$ của $K = 6$ phản ánh độ dễ tìm của bề mặt tìm kiếm trong ngân sách 800 lượt chứ không chứng minh ít đèn có tiềm năng tốt hơn.

---

## 5. Cấu trúc thư mục & Kiểm định

    Nhom4_Whale-Optimization-Algorithm/
    ├── app.py                          # Giao diện web Streamlit chạy trên máy cá nhân
    ├── demo_colab.ipynb                # Notebook tương tác ipywidgets chạy trên Google Colab
    ├── run_demo.py                     # Chạy nhanh một kịch bản từ dòng lệnh
    ├── run_experiments.py              # Chạy lại toàn bộ 330 lượt ứng dụng + 90 lượt benchmark
    ├── tao_bao_cao.py                  # Dựng bộ ảnh 1920×1080 và báo cáo từ results/
    ├── kiem_tra.py                     # Bộ kiểm thử đơn vị cho hình học, năng lượng, lõi WOA và UI
    ├── kiem_tra_ket_qua.py             # Chấm lại và đối chiếu độc lập toàn bộ dữ liệu trong results/
    ├── MO_KET_QUA.html                 # Trang tổng hợp kết quả mở bằng trình duyệt
    ├── data/                           # 3 bản đồ: co_ban.json, khe_hep.json, chan_duong.json
    ├── docs/                           # Tài liệu đề bài, bốn ngách, phân công và kiểm định
    ├── phan_cong/                      # Thư mục nhiệm vụ chi tiết của 11 thành viên (00..10)
    ├── src/                            # 10 module mã nguồn (n1_... đến n10_...)
    ├── results/                        # Kết quả CSV, JSON từng seed, replay ca gốc và 17 ảnh figures/
    └── tests/                          # Bộ kiểm thử dữ liệu và cấu hình

Lệnh kiểm tra toàn bộ logic và tái lập dữ liệu thực nghiệm:

    python kiem_tra.py
    python kiem_tra_ket_qua.py
    python run_experiments.py --output results/chay_lai
    python tao_bao_cao.py

---

## 6. Phân công thành viên (`phan_cong/`)

| Mã | Thành viên | Phần phụ trách và sản phẩm đối chiếu |
| :---: | :--- | :--- |
| **S0** | **Minh Nhân** | Chốt đề bài, đối chiếu mã tác giả, kiểm định độc lập, ghép nhánh và chốt phạm vi kết luận |
| **N1** | **Hoàng Tuấn** | Hình học đoạn thẳng–vùng bão, độ dài đường bay (`src/n1_hoang_tuan_hinh_hoc.py`) |
| **N2** | **Quốc Phong** | Tiêu hao pin bay/đèn, tín hiệu và utility bão hòa (`src/n2_quoc_phong_nang_luong.py`) |
| **N3** | **Phúc Khang** | Hàm đánh giá `evaluate()`, kiểm tra hợp lệ và benchmark (`src/n3_phuc_khang_danh_gia.py`) |
| **N4** | **Hoàng Yến** | Dữ liệu 3 bản đồ, giải mã 30 biến, lịch tham số $a$ (`src/n4_hoang_yen_du_lieu.py`) |
| **N5** | **Quỳnh Ngân** | Cập nhật vị trí 3 nhánh WOA, ngách $l$ và xử lý biên (`src/n5_quynh_ngan_buoc_woa.py`) |
| **N6** | **Vân Lâm** | Vòng lặp chính, quản lý 3 sổ ghi, snapshot đàn và kiểm chứng $K=6 \to K=10$ (`src/n6_van_lam_woa.py`) |
| **N7** | **Ngọc Thanh** | Kế hoạch 11 cấu hình × 30 seed, chạy thực nghiệm và xuất CSV/JSON (`src/n7_ngoc_thanh_thuc_nghiem.py`) |
| **N8** | **Trang Bùi** | Thống kê `mean`/`SD`, phân tích cặp seed (`paired.csv`), chọn seed gần trung vị (`src/n8_trang_bui_thong_ke.py`) |
| **N9** | **Trang Nguyễn** | Biểu đồ 1920×1080, vẽ đàn xám, ca gốc theo thời gian và benchmark (`src/n9_trang_nguyen_ve_hinh.py`) |
| **N10** | **Bảo Ngọc** | Giao diện Colab/Streamlit, phát lại quỹ đạo, tải hình/dữ liệu và tài liệu dự án (`src/n10_bao_ngoc_demo.py`, `app.py`, `demo_colab.ipynb`, `README.md`) |

---

## 7. Giới hạn mô hình và Tài liệu tham khảo

* **Phạm vi mô hình:** Bài toán xét trên mặt phẳng 2D tĩnh, chưa tính đến gia tốc, bán kính cua vật lý, gió, độ cao bay hoặc suy hao tín hiệu theo thời gian. Vùng bão chỉ ràng buộc đường bay, không chặn sóng tín hiệu; đèn phát được đặt trùng với các điểm trung gian của đường bay.
* **Diễn giải số liệu:** $U$ là chỉ số hữu dụng toán học phục vụ so sánh phương án, không diễn giải thành tỷ lệ phần trăm người dân được cứu trợ thực tế.
* **Nguồn thuật toán gốc:** Mirjalili, S., & Lewis, A. (2016). *The Whale Optimization Algorithm*. Advances in Engineering Software, 95, 51–67.
