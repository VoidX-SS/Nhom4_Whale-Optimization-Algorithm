# Ngọc Thanh

Mở [src/n7_ngoc_thanh_thuc_nghiem.py](../../src/n7_ngoc_thanh_thuc_nghiem.py) và dùng bảng dưới để đối chiếu.

| Bước | Nội dung làm | Đầu vào | Đầu ra |
|---|---|---|---|
| 1 | Chốt thiết kế đo | Ba ca gốc và 4 câu hỏi | 11 cấu hình không trộn Cartesian mọi nút |
| 2 | Chạy ứng dụng | N=30,T=800,seed1..30 | 330 JSON, bao gồm 8 lượt chưa tìm thấy hợp lệ |
| 3 | Chạy kiểm chứng | N=30,T=500, 3 hàm | 90 JSON benchmark riêng với ngưỡng rõ |
| 4 | Xuất CSV | Kết quả từng seed | Trials.csv một hàng/lượt gửi cho Trang Bùi |

Bạn chọn một hàm nhỏ trong phần mình, lần từ đầu vào đến return, rồi chỉ một kết quả thật. Không cần thuộc mười module một lượt. Tên trên file là trách nhiệm theo phân công; nhóm thực hiện PR và review thật để ghi nhận đóng góp.
