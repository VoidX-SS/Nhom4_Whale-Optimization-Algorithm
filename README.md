# Đom Đóm — bản nhóm thu gọn, ngày 01/11/2026

Mình đã thu gọn về đúng bốn câu hỏi nghiên cứu. Phần đầu của báo cáo bây giờ dành cho **bài toán gốc và cách đàn tìm kiếm**, rồi mới đến các ngách. Các thí nghiệm đổi b, utility tuyến tính, random mới và điều tra K=14 cũ được chuyển sang một gói cá nhân riêng.

## Mở cái gì trước?

**Xem ngay:** mở `MO_KET_QUA.html`. Các ảnh trong `results/figures` có đủ bản đồ, cột và râu, bảng utility, số seed tìm thấy nghiệm hợp lệ và số best_overall hợp lệ. Sáu ảnh `*_ONE_SHOT.png` là sáu đối chứng cho bốn ngách, xuất đúng **1920 × 1080** để đưa lên slide.

**Muốn điều khiển cả đàn trên máy:** mở terminal trong thư mục này:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Trang mở trên máy mình. Chỉnh N, T, seed, cả ba bão, lịch a, kiểu l, sửa biên và số đèn tối đa. Bật “Xem cả đàn khi đang tính” để thấy các đường xám trong quá trình chạy. Sau đó kéo khung xem để phát lại. Đường xám có thể chưa đủ điều kiện; chúng là các bài làm của đàn, không phải đều là nghiệm được công nhận.

**Muốn dùng Colab:** tải `demo_colab.ipynb` lên Google Colab, chạy ô chuẩn bị và tải ZIP này lên khi được hỏi. Notebook có bảng điều khiển ipywidgets: nút chạy, chỉnh cả ba bão, Play và thanh trượt để phát lại cả đàn. Chọn lưu mỗi 1 lượt nếu muốn lưu thật dày; mặc định mỗi 10 lượt cho nhẹ. Giao diện và thí nghiệm cùng gọi **một hàm `woa` Python**.

**Chạy một lần bằng terminal:**

```bash
python run_demo.py --map khe_hep --l independent_l --iterations 800
```

## Các thông số đã chốt

| Giữ cố định trong bài nhóm | Giá trị |
|---|---|
| Điểm trung gian / số biến | 10 điểm × (x,y,pin) = 30 biến |
| Túi pin chung | 220 |
| Ngưỡng chọn nhánh / b | 0.5 / 1 |
| Utility | Bão hòa |
| Phạt bão / vượt pin / ra map | 100 / 30 / 100 |
| Phạt gấp khúc | Đã bỏ |
| Bản cơ sở | a linear, shared_l, clip |

Bốn ngách: **l dùng chung/độc lập; clip/re-init; a linear/cosine/quadratic; số đèn phát tối đa trên 10 điểm đường bay**. Ngách cuối giữ 30 biến và khảo sát tối đa 6/8/10 đèn được phân pin. Nó là một câu hỏi về giới hạn số thiết bị, không còn là thí nghiệm đổi số chiều 18/30/42 như bản cũ. Đọc `docs/03_bon_ngach.md` để hiểu việc này và kiểm chứng bao hàm nghiệm K=6 vào K=10.

## Đổi gì ở lõi?

Bản trước chưa đủ sát mã MATLAB công bố của tác giả. Bản này giữ **A/C vô hướng, chọn cá voi tham khảo bên trong vòng từng chiều, cập nhật tại chỗ, lịch a và a2/l, thứ tự sửa biên–chấm–cập nhật**, và tổng lượt chấm N*T theo `WOA.m`. Mã MATLAB cùng license được giữ nguyên trong `tham_khao_tac_gia`. Phần thêm của nhóm là đề bài, hàm phạt, sổ nghiệm hợp lệ/qua khe và việc vẽ/lưu.

Benchmark được chạy trên miền gốc thay vì dời đáy về 0.5 trong hộp 0..1. Bộ mới: **Sphere 30 chiều và Rastrigin 30 chiều đều đạt ngưỡng ở 30/30 seed**, N=30, T=500. Không sử dụng lại bảng benchmark cũ. Điều tra riêng giữ cùng toán tử mới nhưng đổi miền biểu diễn cho thấy việc dời gốc có ảnh hưởng mạnh; chi tiết có trong gói cá nhân.

## Bản đồ và dữ liệu

Trong bản mới: **A=cơ bản, B=khe hẹp, C=chắn đường**. Bản cũ gọi B=chắn đường và C=khe hẹp; mình ghi rõ thay đổi nhãn này để không trộn hai bảng. Khe B có cổng kiểm tra x=40, y trong [47,53]. “Đã qua khe” chỉ được đếm khi có một đường tránh bão và đủ pin thực sự cắt qua cổng đó.

Đã chạy **330 lượt ứng dụng**: 11 cấu hình ×30 seed, N=30, T=800, 24.000 lần chấm/lượt. Cộng **90 benchmark**, tổng 420 lượt cho bản nhóm. `trials.csv` do Ngọc Thanh xuất; Trang Bùi đọc nó để tạo `summary.csv`, `paired.csv`. JSON giữ từng phương án và toàn bộ đàn cuối đã được chấm. Ba replay ca gốc ở `results/demos` dùng seed gần trung vị phần mục tiêu, có kiểm tra tái lập khớp lượt gốc.

```bash
python kiem_tra.py
python kiem_tra_ket_qua.py
python run_experiments.py --output results/chay_lai
```

Lệnh cuối chạy lại toàn bộ vào thư mục mới. `tao_bao_cao.py` dựng bộ ảnh kèm theo từ `results`. Dữ liệu gốc đã được kiểm lại; không cần chạy hàng trăm lượt chỉ để mở báo cáo.

## Tìm phần của từng người

Mười module trong `src` giữ tên mười bạn như trước. `phan_cong` có thư mục riêng cho cả 11 người và bảng **Bước / Nội dung làm / Đầu vào / Đầu ra**. Đọc đề ở `docs/01_de_bai.md`, đọc chuyện lõi ở `docs/02_loi_va_tac_gia.md`, rồi mở phần của mình. Vòng lặp vẫn viết bằng `def`, `for`, `if`, danh sách và từ điển; thư viện ngoài chủ yếu lo giao diện và vẽ hình.
