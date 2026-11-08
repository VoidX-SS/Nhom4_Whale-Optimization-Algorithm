# Báo cáo Phân công & Hướng dẫn Kỹ thuật — Quốc Phong (N2)

> **Phụ trách:** Pin, Túi năng lượng dùng chung, Tín hiệu & Độ hữu dụng bão hòa tại 8 trại cứu trợ, Phân tích mức từng trại ca gốc, Hỗ trợ ngách $K=6/8/10$, Ý nghĩa & Giới hạn mô hình WOA.  
> **Nhánh Git:** `Quoc_Phong`  
> **Các file phụ trách & bàn giao:**  
> - `src/n2_quoc_phong_nang_luong.py` (Mã nguồn cốt lõi)  
> - `tests/test_quoc_phong.py` (Kiểm thử tự động toàn diện)  
> - `docs/01_de_bai.md` (Đối chiếu ràng buộc đề bài)  
> - `README_quoc_phong.md` (Tài liệu báo cáo, giải trình & nội dung slide thuyết trình)

---

## 1. Bảng đối chiếu 6 bước hoàn thành theo phân công

| Bước | Nội dung làm | Đầu vào | Đầu ra của Quốc Phong |
|---|---|---|---|
| **1** | Tính pin bay và pin đèn từ các thiết bị thật sự được bật | Chiều dài bay $L$ từ N1; mảng trạm đèn `beacons` sau giải mã top-K của N4 | $E_{\text{bay}} = 0.45 \times L$, $E_{\text{đèn}} = \sum \tilde{e}_k$, $E_{\text{tổng}} = E_{\text{bay}} + E_{\text{đèn}}$ |
| **2** | Tính phần vượt pin chuẩn hóa với ngân sách 220 | Tổng năng lượng $E_{\text{tổng}}$ | $\text{over} = \frac{\max(0, E_{\text{tổng}} - 220)}{220}$, `energy_ok`; tuyệt đối **không tự cắt gọt pin** về 220 |
| **3** | Tính tín hiệu từ mọi đèn tới từng trại theo khoảng cách | Tọa độ đèn $(x_k, y_k)$, pin thực dùng $\tilde{e}_k$ và tọa độ 8 trại | $I_{km} = \frac{\tilde{e}_k}{1 + d_{km}^2 / 18^2}$, $I_m = \sum_{k=1}^{10} I_{km}$; đèn tắt ($\tilde{e}_k=0$) cho $I_{km}=0$ |
| **4** | Đổi $I_m$ sang $u_m = 1 - e^{-0.1 I_m}$, tính $U$ có trọng số và $u_{\min}$ | Tín hiệu $I_m$ và trọng số $w_m$ của 8 trại | `utility_sat` ($U$), `minimum_service` ($u_{\min}$), bảng kiểm tính tay đối chiếu tài liệu |
| **5** | Đọc hình pin/từng trại của A/B/C, hỗ trợ Lâm (N6) đọc $K=6/8/10$ | Các nghiệm hợp lệ ca gốc, ảnh N9 (`ca_A_phan_tich_pin.png`) và số liệu N8 | Phân tích cán cân pin bay vs. pin đèn; chỉ ra các trại yếu ($u_{\min}$); giải thích ngách $K$ |
| **6** | Viết ghi chú dễ hiểu, đưa nội dung slide và thuyết trình demo | Module, test case, số liệu đối chiếu đã kiểm | Báo cáo chi tiết, công thức, nội dung nói seminar (phút 8–12 & 22–23) |

---

## 2. Giao diện bàn giao cho các thành viên trong nhóm

> *"Mình nhận gì từ phần trước, tính gì, trả gì cho phần sau?"*

### 2.1. Nhận từ phần trước:
- **Từ Hoàng Tuấn (N1):** Chiều dài đường bay gấp khúc $L$ (`length`).
- **Từ Hoàng Yến (N4):** Danh sách 10 trạm đèn `beacons` đã qua hàm `decode` chọn top-$K$ đèn phát lớn nhất ($\tilde{e}_k$).
- **Từ Dữ liệu đề bài:** Ngân sách pin $220.0$, thang suy giảm khoảng cách $R = 18.0$, hệ số bão hòa $\alpha = 0.1$, tọa độ và trọng số 8 trại $w_m$.

### 2.2. Bàn giao cho phần sau:
- **Cho Phúc Khang (N3):**
  - Từ điển `energy`: `total`, `flight`, `lamps`, `over`, `energy_ok`. Khang dùng `over` để phạt $30 \times \text{over}^2$ và kiểm tra `energy_ok`.
  - Từ điển `signal`: `utility_sat` ($U$), `minimum_service` ($u_{\min}$), `levels` ($I_m$), `satisfaction` ($u_m$). Khang dùng $U$ để tính $f_0 = -U + 0.12 \times L/100$.
- **Cho Vân Lâm (N6):** Hỗ trợ giải thích bản chất không gian nghiệm khi giới hạn $K = 6, 8, 10$ đèn phát.
- **Cho Trang Nguyễn (N9) & Bảo Ngọc (N10):**
  - Cung cấp tỷ lệ phân bổ pin bay vs. pin đèn (`flight_ratio_percent`, `lamp_ratio_percent`).
  - Danh sách chi tiết 8 trại để vẽ biểu đồ thanh (bar chart) mức phục vụ từng trại trên ảnh `ca_A_phan_tich_pin.png`.
  - Chỉ số tập trung năng lượng Herfindahl $H_E = \sum (\tilde{e}_k / E_{\text{đèn}})^2$ (Trang 15 tài liệu).

---

## 3. Cách chạy và Đầu ra thật (Actual Output)

### 3.1. Chạy tự kiểm chứng độc lập (Self-Verification):
```bash
python src/n2_quoc_phong_nang_luong.py
```

**Đầu ra thật:**
```text
============================================================================
 BỘ KIỂM CHỨNG TOÁN HỌC & ĐỐI CHIẾU SỐ LIỆU TÀI LIỆU (N2 - QUỐC PHONG)
============================================================================

[1] Kiểm tra Pin (Tài liệu Trang 9): L = 150, Pin đèn = 130
    - Pin bay tính toán:  67.5 (Kỳ vọng: 67.5)
    - Pin đèn tính toán:  130.0 (Kỳ vọng: 130.0)
    - Tổng pin tính toán: 197.5 (Kỳ vọng: 197.5 <= 220)
    - Đạt chuẩn ngân sách: True
    -> [KHỚP CHÍNH XÁC]

[2] Kiểm tra Suy giảm tín hiệu theo khoảng cách (Tài liệu Trang 10: Đèn pin 20)
    - Tại d = 0  (ngay trại): I = 20.0000 (Kỳ vọng: 20.0)
    - Tại d = 18 (cách 18dv): I = 10.0000 (Kỳ vọng: 10.0)
    - Tại d = 36 (cách 36dv): I = 4.0000 (Kỳ vọng: 4.0)
    -> [KHỚP CHÍNH XÁC]

[3] Kiểm tra Bảng Hữu dụng Bão hòa u = 1 - exp(-0.1 * I) (Tài liệu Trang 10)
    - I = 0.0  -> u = 0.0000 (Kỳ vọng: 0.0000)
    - I = 5.0  -> u = 0.3935 (Kỳ vọng: 0.3935)
    - I = 10.0 -> u = 0.6321 (Kỳ vọng: 0.6321)
    - I = 20.0 -> u = 0.8647 (Kỳ vọng: 0.8647)
    - I = 40.0 -> u = 0.9817 (Kỳ vọng: 0.9817)
    -> [KHỚP CHÍNH XÁC]

[4] Kiểm tra Gộp hữu dụng có trọng số (Tài liệu Trang 10: w=[3, 1], u=[0.8, 0.4])
    - U tính toán:    0.7000 (Kỳ vọng: 0.7000)
    - u_min tính toán: 0.4000 (Kỳ vọng: 0.4000)
    -> [KHỚP CHÍNH XÁC]

[5] Kiểm tra Vượt pin chuẩn hóa (Tài liệu Trang 12: E_tong = 230, Budget = 220)
    - Tổng pin: 230.0 | Vượt: 10.0
    - over tính toán: 0.045455 (Kỳ vọng: 0.045455)
    - Phạt pin N3 (30 * over^2): 0.061983
    -> [KHỚP CHÍNH XÁC - KHÔNG TỰ Ý CẮT BỚT PIN]

[6] Kiểm tra Đèn tắt (active = False hoặc energy = 0)
    - Tổng pin đèn: 15.0 (Chỉ tính đèn active: 15.0, bỏ qua đèn tắt: 25.0)
    -> [KHỚP CHÍNH XÁC]

============================================================================
 TẤT CẢ 6 ĐIỀU KIỆN KIỂM CHỨNG CỦA QUỐC PHONG ĐỀU THÀNH CÔNG RỰC RỠ!
============================================================================
```

### 3.2. Chạy toàn bộ bộ kiểm thử tự động (Unit Tests):
```bash
python -m unittest tests/test_quoc_phong.py
```
**Đầu ra:**
```text
.......
----------------------------------------------------------------------
Ran 7 tests in 0.006s

OK
```

---

## 4. Phân tích chi tiết: Ca gốc & Hỗ trợ ngách $K=6/8/10$

### 4.1. Cán cân phân bổ năng lượng (Đánh đổi Đường bay vs. Chiếu sáng)
- Trong ngân sách cố định 220:
  - Nếu UAV chọn đường bay dài (ví dụ $L = 200 \implies E_{\text{bay}} = 90$), năng lượng còn lại cho đèn phát chỉ là $220 - 90 = 130$.
  - Nếu UAV chọn đường bay ngắn ($L \approx 120 \implies E_{\text{bay}} = 54$), túi pin dôi dư tới $166$ cho đèn phát, giúp chiếu sáng các trại mạnh hơn.
  - Tuy nhiên, đường bay quá ngắn lại không thể uốn lượn tiếp cận gần các trại ở xa (như C1, C4, C6 ở biên trên hay C8 ở góc đông nam), dẫn đến tín hiệu bị suy giảm mạnh theo mẫu số $1 + d^2 / 18^2$.
  - Thuật toán WOA phải liên tục giải bài toán đánh đổi Pareto đa mục tiêu giữa **độ dài đường bay** và **cường độ phủ sóng**.

### 4.2. Đọc mức phục vụ từng trại & Phát hiện "Trại đói tín hiệu"
- Hàm bão hòa $u_m = 1 - e^{-0.1 I_m}$ có độ dốc giảm dần:
  - Tăng $I$ từ 0 lên 10: $u$ tăng từ $0 \to 0.6321$ ($\Delta u = +0.6321$).
  - Tăng $I$ từ 10 lên 20: $u$ tăng từ $0.6321 \to 0.8647$ ($\Delta u = +0.2326$).
  - Tăng $I$ từ 20 lên 40: $u$ chỉ tăng thêm $+0.1170$.
- **Ý nghĩa cảnh báo:** Điểm tổng hợp $U$ trung bình có thể đạt mức cao ($0.75 - 0.80$), nhưng có thể có 1-2 trại hẻo lánh bị "bỏ rơi" (ví dụ C8 chỉ đạt $u_8 = 0.15$). Do đó, việc báo cáo $u_{\min}$ là thước đo đạo đức và công bằng bắt buộc trong bài toán cứu trợ nhân đạo.

### 4.3. Hỗ trợ giải thích ngách $K=6, 8, 10$ cho Vân Lâm (N6)
- **Thực nghiệm nhóm ghi nhận:** $U$ trung bình của $K=6$ đạt khoảng $0.722$, cao hơn $K=8$ ($0.636$) và $K=10$ ($0.659$).
- **Giải thích đúng bản chất mô hình:**
  1. *Về mặt toán học (Không gian nghiệm lồng nhau):* Mọi phương án 6 đèn phát đều có thể viết thành phương án 10 đèn bằng cách gán pin của 4 đèn còn lại bằng 0. Do đó, không gian nghiệm $K=10$ bao chứa toàn bộ không gian nghiệm $K=6$. Điểm tối ưu toàn cục của $K=10$ về mặt lý thuyết **không bao giờ kém hơn** $K=6$.
  2. *Về mặt tìm kiếm hữu hạn của WOA:* Thuật toán chạy 800 lượt bị phân tán tài nguyên tìm kiếm khi phải tối ưu đồng thời cả 10 đèn. Cơ chế giải mã top-$K$ của Yến (N4) với $K=6$ đóng vai trò như một bộ lọc làm thưa (sparsity regularizer), giúp thuật toán dồn pin tập trung vào các điểm trọng yếu thay vì rải mỏng pin ra 10 vị trí.

---

## 5. Nội dung thuyết trình Seminar (Phút 8–12 & 22–23)

### 🎯 Phút 8–12: Trình bày Mô hình Năng lượng & Utility bão hòa
1. **Bài toán túi pin chung 220:**  
   "Thưa thầy và các bạn, UAV trong mô phỏng mang một túi năng lượng cố định là 220 đơn vị. Năng lượng này phục vụ đồng thời hai nhiệm vụ: di chuyển ($E_{\text{bay}} = 0.45 \times L$) và thắp sáng các trạm đèn đom đóm ($E_{\text{đèn}} = \sum \tilde{e}_k$). Bất kỳ phương án nào có $E_{\text{tổng}} > 220$ đều bị tính vi phạm $\text{over} = (E_{\text{tổng}} - 220)/220$ và chịu mức phạt bình phương nặng $30 \times \text{over}^2$."
2. **Quy luật suy giảm tín hiệu vật lý:**  
   "Mỗi trạm đèn truyền tín hiệu tới trại cứu trợ theo định luật suy giảm phi tuyến $I = \frac{\tilde{e}}{1 + d^2/18^2}$. Khoảng cách $R=18$ là thang đo đặc trưng của mô hình: ở cự ly 18 đơn vị, tín hiệu giảm 50%; ở cự ly 36 đơn vị, tín hiệu giảm tới 80%."
3. **Ý nghĩa hàm bão hòa $u = 1 - e^{-0.1 I}$:**  
   "Nhóm không dùng hàm tuyến tính vì trong thực tế cứu hộ, khi một trại đang mất liên lạc hoàn toàn, nhận được một chút tín hiệu ban đầu có ý nghĩa sống còn. Nhưng khi tín hiệu đã đủ mạnh để đàm thoại và gửi tọa độ, việc dồn thêm sóng hầu như không tăng thêm giá trị. Hàm bão hòa ép thuật toán WOA không được 'lãng phí' pin vào những trại đã no sóng mà phải tìm cách vươn tới các trại khác."

### ⚠️ Phút 22–23: Ý nghĩa và Giới hạn mô hình (Đánh giá phản biện trung thực)
1. **Lưu ý định danh chỉ số $U$:**  
   "Chỉ số $U$ là thước đo hữu dụng toán học mô phỏng trong thang điểm $[0, 1)$, **tuyệt đối không được gọi là tỷ lệ người được cứu sống** hay bảo đảm 100% mọi trại đều an toàn."
2. **Giới hạn của hàm phạt mềm:**  
   "Phạt pin $30 \cdot V^2$ và phạt bão $100 \cdot P_c$ là các hàm phạt hữu hạn. Do đó, cá voi đầu đàn (`best_overall`) có thể đạt điểm $J$ rất nhỏ nhưng vẫn vi phạm nhẹ một luật nào đó. Đây là lý do nhóm bắt buộc phải duy trì sổ `best_valid` độc lập để báo cáo kết quả thật."
3. **Giới hạn không gian 2D tĩnh:**  
   "Mô hình chưa xét đến động lực học bay (gia tốc, góc lượn, sức cản của gió), độ cao 3D hay hiện tượng nhiễu sóng đa đường. Các kết luận rút ra phản ánh đặc tính hội tụ của thuật toán WOA trên mô hình toán trừu tượng, không tuyên bố áp dụng nguyên bản cho UAV thật ngoài đời."
