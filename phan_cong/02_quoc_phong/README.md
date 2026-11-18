# Quốc Phong

Mở [src/n2_quoc_phong_nang_luong.py](../../src/n2_quoc_phong_nang_luong.py) và dùng bảng dưới để đối chiếu.

| Bước | Nội dung làm | Đầu vào | Đầu ra |
|---|---|---|---|
| 1 | Tính pin | L và pin các đèn được bật | 0.45*L, pin đèn, tổng và phần vượt 220 |
| 2 | Tính tín hiệu | Vị trí đèn, khoảng cách và trại | I từng trại rồi u=1-exp(-0.1*I) |
| 3 | Ghép utility | u và trọng số 8 trại | U trung bình có trọng số, trại yếu nhất |
| 4 | Đọc ca gốc | Các ảnh A/B/C_pin_va_trai | Lời giải thích túi pin chung và giới hạn ý nghĩa U |

Bạn chọn một hàm nhỏ trong phần mình, lần từ đầu vào đến return, rồi chỉ một kết quả thật. Không cần thuộc mười module một lượt. Tên trên file là trách nhiệm theo phân công; nhóm thực hiện PR và review thật để ghi nhận đóng góp.
