# Chạy, kiểm tra và các giới hạn kỹ thuật

## Lệnh ngắn

```bash
python -m pip install -r requirements.txt
python kiem_tra.py
python kiem_tra_ket_qua.py
python -m streamlit run app.py
```

Trong Colab, chạy ô chuẩn bị rồi ô mở bảng điều khiển. Chỉnh tọa độ/bán kính của cả ba bão, chọn T và nhấn Chạy. Bật xem trực tiếp sẽ tốn thêm thời gian vẽ; tắt nó thì vẫn có dữ liệu để replay sau đó. Lưu mỗi 1 lượt cho nhiều khung; lưu mỗi 10 nhẹ hơn. T là số lượt chấm, đánh số từ 0 nên cuối T=800 hiện t=799.

Khi mở bản lưu, các số in ở phần kết quả là cấu hình của lần chạy thật ấy. Các nút mới chỉnh chưa làm thay đổi bản lưu. Replay luôn dùng bản đồ đi kèm lần chạy, không ghép với tọa độ bão vừa sửa bên trái.

## Đã kiểm những gì?

Đã kiểm ví dụ có đường qua khe, đoạn vi phạm bão, pin, K tối đa với 30 biến, lịch a theo t/T, clip, tái lập seed và benchmark. Bộ đầy đủ gồm 330 lượt ứng dụng và 90 benchmark, đã được chấm lại từ các mảng nghiệm. Toàn bộ final_population là đàn đã sửa biên và chấm, không phải bước mới chưa chấm cuối vòng.

Giao diện Streamlit được kiểm bằng AppTest chính thức: đổi N/T/l, chạy form, kéo replay, đổi bản đồ, sửa bão và bật vẽ cả đàn trực tiếp. Các handler ipywidgets được gọi thử với N/T và bão mới, kiểm kết quả và replay. Đây là kiểm thử logic giao diện; việc hiển thị widget đặc thù vẫn nên mở thử trong một phiên Google Colab trên máy trình bày. Thư viện vẽ đã xuất và kiểm tra các ảnh 16:9.

Mã tác giả được giữ cùng license ở `tham_khao_tac_gia`; bản dịch Python không hứa tái lập cùng dãy ngẫu nhiên của MATLAB. Đối chiếu chính là các công thức và thứ tự cập nhật. Snapshot và giao diện không tự sửa nghiệm cho đẹp.

Thời gian trong CSV đo ở phiên chạy có nhiều tiến trình cùng hoạt động, nên không dùng để xếp hạng tốc độ các ngách. Khi xem trực tiếp, thời gian còn gồm việc dựng ảnh. Giá trị mục tiêu và số lần chấm dùng cùng ngân sách đã nêu.

## Dùng code mà chưa quen tên tiếng Anh

Whale là một phương án; population là danh sách các phương án; problem là đề; settings là cách chạy; report là phiếu chấm; valid là đủ điều kiện; history là dấu mốc; snapshots là ảnh số của cả đàn; boundary là miền biến. `None` là chưa có kết quả, không phải 0. `append` bỏ thêm vào danh sách, `copy` cất một bản để sổ không bị đổi theo đàn đang sửa.

Lõi ở n5/n6, pin ở n2, phiếu chấm n3. Các file vẽ và UI có nhiều tên hàm của thư viện; bạn có thể để chúng sang bên khi đang học WOA. Đầu tiên theo một tọa độ ở một nhánh, sau đó cả mảng chỉ lặp lại việc ấy. Bình phương trong code dùng `x*x` hoặc `x**2`; `^` không phải phép bình phương của Python.
