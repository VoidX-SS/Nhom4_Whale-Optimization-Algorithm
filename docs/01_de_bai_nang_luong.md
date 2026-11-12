# Phần Năng Lượng và Hữu Dụng Bão Hòa — Đề Bài Đom Đóm


## 1. Túi pin chung 220: Bay vs. Thắp đèn

UAV được cấp một túi năng lượng cố định là **220 đơn vị**. Túi pin này dùng chung cho hai việc: bay trên đường và phát tín hiệu cho các trại cứu trợ.

### Tiêu hao pin bay
- Cứ bay được 1 đơn vị chiều dài $L$ thì tốn $0.45$ đơn vị pin:
  $$E_{\text{bay}} = 0.45 \times L$$
- Đường bay càng dài, ngoằn ngoèo thì pin bay càng tốn. $L$ là tổng chiều dài 11 đoạn thẳng nối từ điểm xuất phát $S(0, 50)$, qua 10 điểm trung gian, đến đích $T(100, 50)$.

### Tiêu hao pin đèn
- Tại 10 điểm trung gian, UAV mang theo các thiết bị phát tín hiệu (gọi là đèn hoặc đom đóm).
- Mỗi đèn có mức pin đề xuất $e_k \in [0, 25]$.
- Ở bản cơ sở, tối đa 10 đèn đều có thể bật. Ở các ngách giới hạn $K = 6$ hoặc $8$, chỉ có $K$ đèn có mức pin đề xuất cao nhất được kích hoạt; các đèn còn lại bị tắt ($\tilde{e}_k = 0$).
- Tổng pin đèn thực tế tiêu thụ chỉ tính các đèn thực sự được bật:
  $$E_{\text{đèn}} = \sum_{k=1}^{10} \tilde{e}_k$$
- **Lưu ý:** Đèn tắt không tiêu pin và không phát tín hiệu, nhưng UAV vẫn phải bay qua điểm đó (vẫn tính vào độ dài $L$ và tốn pin bay).

### Tổng pin và phần phạt vượt pin
- Tổng pin dùng hết:
  $$E_{\text{tổng}} = E_{\text{bay}} + E_{\text{đèn}}$$
- Nếu $E_{\text{tổng}} \le 220$: Phương án đạt yêu cầu về pin.
- Nếu $E_{\text{tổng}} > 220$: Bị tính phần vượt chuẩn hóa:
  $$V = \frac{E_{\text{tổng}} - 220}{220}$$
- **Quy tắc quan trọng:** Thuật toán tuyệt đối **không tự ý gọt bớt pin** của đèn hay co ngắn đường bay lại cho vừa 220. Vi phạm pin sẽ bị phạt vào hàm mục tiêu với mức phạt $30 \times V^2$. Hàm phạt này giúp cá voi tự học cách giảm pin ở các vòng sau.

---

## 2. Tín hiệu từ đèn truyền đến 8 trại

Bản đồ có 8 trại cứu trợ cố định, mỗi trại có vị trí $(x_m, y_m)$ và trọng số nhu cầu $w_m$ khác nhau.

### Quy luật suy giảm tín hiệu
Tín hiệu truyền trong không gian bị yếu dần khi khoảng cách xa ra:
- Đèn thứ $k$ đặt tại $(x_k, y_k)$ có pin phát $\tilde{e}_k$.
- Khoảng cách hình học từ đèn $k$ tới trại $m$ là $d_{km}$.
- Mức tín hiệu trại $m$ nhận được từ riêng đèn $k$ là:
  $$I_{km} = \frac{\tilde{e}_k}{1 + \frac{d_{km}^2}{18^2}}$$

Con số $18$ ở mẫu số là **thang khoảng cách đặc trưng** của mô hình:
- Nếu đặt đèn ngay sát trại ($d = 0$): Trại nhận trọn vẹn $I = \tilde{e}_k$.
- Nếu cách trại $18$ đơn vị: Tín hiệu giảm còn một nửa ($50\%$).
- Nếu cách trại $36$ đơn vị: Mẫu số là $1 + 4 = 5$, tín hiệu chỉ còn $20\%$.
- Số $18$ không phải là bán kính cắt cụt. Kể cả ở xa hơn 18, đèn vẫn góp một chút tín hiệu nhỏ, không bị gán về 0.

### Tổng tín hiệu tại một trại
Mỗi trại nhận tín hiệu cộng dồn từ **toàn bộ 10 đèn**:
$$I_m = \sum_{k=1}^{10} I_{km}$$
Không có luật chia một đèn chỉ phục vụ riêng một trại nào. Các đèn cùng phủ sóng lên mọi trại.

---

## 3. Vì sao phải dùng hàm hữu dụng bão hòa?

Nhóm không dùng trực tiếp $I_m$ để tính điểm, mà đổi sang độ hữu dụng $u_m$:
$$u_m = 1 - e^{-0.1 \times I_m}$$

### Ý nghĩa thực tế: Lợi ích cận biên giảm dần
- Hãy hình dung một trại đang bị cô lập hoàn toàn ($I_m = 0$). Khi nhận được một chút tín hiệu đầu tiên ($I_m$ từ 0 lên 5), họ đã có thể gửi tin nhắn khẩn cấp, mức hữu dụng tăng vọt từ $0$ lên $0.39$.
- Tăng tiếp từ 5 lên 10: $u_m$ tăng từ $0.39$ lên $0.63$.
- Nhưng khi trại đã có tín hiệu rất mạnh ($I_m = 20 \to u_m = 0.86$), nếu cố dồn thêm pin để $I_m$ lên 40 thì $u_m$ cũng chỉ nhích nhẹ lên $0.98$.
- **Tác dụng với thuật toán:** Hàm bão hòa ép cá voi không được "tham lam" dồn hết pin vào các trại ở gần để cày điểm, mà buộc phải chia sẻ năng lượng bay sang các trại xa hơn đang thiếu tín hiệu.

### Độ hữu dụng trung bình toàn hệ thống ($U$)
Gộp 8 trại theo trọng số nhu cầu $w_m$:
$$U = \frac{\sum_{m=1}^8 w_m u_m}{\sum_{m=1}^8 w_m}$$
$U$ luôn nằm trong khoảng $[0, 1)$. Giá trị $U$ càng gần 1 nghĩa là việc phủ sóng càng tốt.

### Mức phục vụ tối thiểu ($u_{\min}$)
Bên cạnh $U$, code luôn đọc thêm:
$$u_{\min} = \min_{m=1..8} u_m$$
Một phương án có thể có $U$ rất cao (ví dụ $0.78$) nhưng lại có một trại ở góc xa chỉ nhận được $u = 0.05$ (bị bỏ rơi). $u_{\min}$ giúp người quan sát biết được trại thiệt thòi nhất đang được phục vụ ở mức nào.

---

## 4. Những điều không được hiểu nhầm

1. **Về ý nghĩa của $U$:**
   $U$ là một chỉ số mô phỏng toán học trừu tượng. **Tuyệt đối không diễn giải $U = 0.8$ là "80% số người dân được cứu sống"**. Mô hình chưa có dữ liệu dân số thật và chưa mô phỏng diễn biến cứu trợ theo thời gian.
2. **Về tính hợp lệ:**
   Điểm số mục tiêu $J$ thấp không đồng nghĩa với hợp lệ. Vì hàm phạt pin $30 \times V^2$ là phạt hữu hạn, một cá voi vượt pin nhẹ vẫn có thể có điểm $J$ tốt. Kết quả báo cáo chất lượng luôn phải lấy từ sổ `best_valid`, không lấy từ cá voi vi phạm pin.
3. **Về mô hình vật lý:**
   Đây là mô hình 2D tĩnh đơn giản hóa:
   - Chưa tính đến gió, độ cao bay, gia tốc hay góc cua vật lý của UAV.
   - Vùng bão chỉ cản đường bay của UAV, không cản sóng tín hiệu.
   - Các đèn phát được đặt trùng với điểm đường bay là quy ước của bài toán mô phỏng, không xem đây là thiết kế UAV thực tế ngoài đời.
