# Đối chiếu phân công sau khi thu gọn

Nhóm vẫn 11 người; Minh Nhân giữ vai trò S0. Mười module theo tên như trước, nhưng công việc được điều chỉnh cho bốn ngách thay vì duy trì các nút đã bỏ. Mỗi bạn có README riêng trong `phan_cong`, với bước làm, đầu vào, đầu ra và chỗ cần mở.

| Người | Phần hoàn thiện và trách nhiệm đối chiếu |
|---|---|
| Minh Nhân | Chốt đề, đối chiếu tác giả, kiểm định, ghép và duyệt phạm vi kết luận |
| Hoàng Tuấn | Hình học đoạn–bão, độ dài; cùng đọc ảnh clip/re-init và các đường ca gốc |
| Quốc Phong | Pin và utility bão hòa; đọc mức từng trại, ý nghĩa và giới hạn mô hình |
| Phúc Khang | Phiếu evaluate, valid, kiểm benchmark miền gốc, độc lập kiểm đường hợp lệ |
| Hoàng Yến | Ba bản đồ, 30 biến, giải mã đèn, ba lịch a; sơ đồ khối |
| Quỳnh Ngân | Dịch ba nhánh theo WOA.m, đối chiếu cập nhật tại chỗ; ngách l |
| Vân Lâm | Vòng lặp, các sổ, snapshot cả đàn; ngách giới hạn đèn và phép nhúng K6→K10 |
| Ngọc Thanh | Kế hoạch 11 cấu hình, 30 seed, CSV từng lượt; thực nghiệm bản cơ sở |
| Trang Bùi | Đọc CSV, mean/SD, cặp seed, quy tắc seed gần trung vị; giải thích bảng |
| Trang Nguyễn | Ảnh 16:9 đủ thông tin, đàn xám, ca gốc theo thời gian và benchmark |
| Bảo Ngọc | Colab/Streamlit, N/T và ba bão, chạy/phát lại, tải hình/dữ liệu và kiểm giao diện |

Gắn tên file là đối chiếu phần việc được giao. Lịch sử đóng góp, PR, review và mức hiểu bài cần được nhóm thực hiện thật. Mỗi bạn nên giải thích được: “Mình nhận gì từ phần trước, tính gì, trả gì cho phần sau?” rồi mở một đầu ra cụ thể.

## Mạch 23 phút

| Phút | Nội dung |
|---|---|
| 0–2 | Vì sao cần tìm kiếm nhiều biến; WOA, tác giả, năm 2016 và nguồn |
| 2–8 | Nghiệm/cá voi, leader, ba nhánh, vòng lặp; chỉ một ví dụ thay số |
| 8–12 | Đom Đóm: túi pin chung, đoạn tránh bão, 30 biến, hợp lệ và hai sổ chính |
| 12–15 | Ca gốc: ảnh tổng hợp, cả đàn lúc đầu/cuối, số seed thành công |
| 15–18 | Ngách l và biên; a và số đèn dùng ảnh/slide tổng hợp ngắn |
| 18–22 | Demo: chỉnh một bão hoặc T, xem đàn, kéo replay và chỉ vào bảng |
| 22–23 | Giới hạn, kết luận đúng phạm vi |

Các thử riêng của Nhân không đưa vào phần trình bày chính. Nếu có câu hỏi sâu, dùng tài liệu nghiên cứu riêng để giải thích, không biến seminar thành một loạt prototype chưa chốt.

## Năm tiêu chí

C-Modulization: tách dữ liệu, lõi, đo, chấm và vẽ. C-Algo setup: đối chiếu mã tác giả, ghi rõ biến/ngẫu nhiên/lượt chấm và nguồn. C-Experiments: ca gốc đứng trước, đủ seed, không bỏ thất bại, đối chứng đúng yếu tố. C-GUI: sửa được T và ba bão, xem toàn đàn/phát lại, cùng một lõi Python. C-Task distribution: bảng theo người và các sản phẩm cụ thể. Chưa có rubric trọng số chi tiết của thầy, nên bộ này là bằng chứng đáp ứng, không phải lời bảo đảm điểm.
