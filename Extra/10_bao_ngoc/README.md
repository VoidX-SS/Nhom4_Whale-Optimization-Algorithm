# Phần Công Việc Tiên Phong - Nguyễn Thị Bảo Ngọc (N10)

Thư mục này lưu trữ riêng các kết quả và sản phẩm tiên phong do bạn **Nguyễn Thị Bảo Ngọc** hoàn thành:
1. **Bộ Snapshot ngoại tuyến (Offline Demo Backup)**:
   - `demo_ca_A_seed7.html`: Trang hiển thị phát lại toàn bộ quá trình hội tụ của đàn cá voi qua từng thế hệ dưới dạng HTML độc lập.
   - `demo_ca_A_seed7.json`: Bản ghi chi tiết 15.441 dòng ghi nhận toàn bộ tọa độ, điểm số, mức tiêu thụ pin và trạng thái hợp lệ của đàn qua 150 vòng lặp.
   - `demo_ca_A_seed7.png`: Biểu đồ tổng quan đường bay và các trại cứu trợ.
2. **Cơ chế phòng thủ (Fallback Mechanism)**:
   - Trong quá trình phát triển, khi các module N7, N8 chưa hoàn thiện kịp, Bảo Ngọc đã chủ động thiết kế cơ chế nạp dữ liệu dự phòng để đảm bảo giao diện Colab (`demo_colab.ipynb`) và Streamlit (`app.py`) có thể chạy độc lập, trơn tru mà không bị phụ thuộc hay gây gián đoạn cho nhóm.
