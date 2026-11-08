# Chốt bốn ngách hữu ích

Mỗi đối chứng dùng seed 1..30, N=30,T=800, 30 biến, pin 220 và cùng đề của ca. Không ghép thành một tổ hợp mọi nút; mình muốn biết đúng thay đổi đang hỏi tạo ra chuyện gì. Tỷ lệ tìm thấy nghiệm và utility đều phải được đọc, vì chỉ nhìn trung bình trên một tập nhỏ thành công có thể gây hiểu lầm.

## 1. l dùng chung hay độc lập theo chiều

Bản cơ sở lấy một l cho cả tờ phương án. Đối chứng để mỗi chiều có l riêng. Câu hỏi là: các tọa độ cùng co/giãn một nhịp hay tự đổi nhịp có ảnh hưởng chất lượng và sự ổn định không? So trên cả A và B. Không gọi đây là phép quay 2D thật hay “từ 1D sang 2D”; đó là thay các hệ số theo chiều.

Trong bộ mới, A có 29/30 lần hợp lệ ở cơ sở và 30/30 khi l riêng; U có điều kiện khoảng 0.659 và 0.790. B đều có 30/30, U khoảng 0.558 và 0.692. Nhưng số seed từng qua khe ở B đều là 2/30. Nâng utility chưa đồng nghĩa tăng xác suất qua khe.

## 2. Clip hay re-init tọa độ vượt biên

Clip đưa tọa độ về tường gần nhất. Re-init bốc lại riêng ô vượt ra ngoài. Hai cách không sửa đường khỏi bão và không bớt pin về 220. Câu hỏi là cách xử lý biên tác động đến tìm kiếm như thế nào.

A: clip 29/30, re-init 30/30, U khoảng 0.659 và 0.823. B: clip 30/30, re-init 26/30; U trong các lượt hợp lệ khoảng 0.558 và 0.708. Re-init ở B có 5/30 seed từng qua khe so với 2/30, nhưng lại thất bại tìm đường hợp lệ nhiều hơn. Đây là một đánh đổi để kể, không phải “re-init luôn tốt”.

## 3. a linear, cosine, quadratic

Đặt u=t/T. Linear `a=2-2*u`; cosine `a=1+cos(pi*u)`; quadratic `a=2*(1-u)*(1-u)`. Chỉ thay lịch a; giữ a2 của cách bốc l theo mã tác giả. Chạy trên B để xem nhịp bước tìm và kết quả thay đổi thế nào.

Cả ba có 30/30 lượt hợp lệ. U khoảng 0.558,0.555,0.546. Không có một lợi thế utility lớn trong bộ này. Số seed từng qua khe lần lượt 2,1,4. Các chênh lệch ấy nhỏ, nên báo như thống kê mô tả chứ không gọi là thắng chắc. Ngách này giúp nhóm trình bày được một kết quả gần đối chứng, không ép đồ thị kể câu chuyện đẹp.

## 4. Giới hạn số đèn phát — giữ nguyên 30 biến

Vì yêu cầu giữ 30 chiều, bản mới không còn đổi 6/10/14 điểm trung gian. Mình giữ 10 điểm đường và 10 biến pin, rồi chỉ cho tối đa K=6/8/10 đèn được nhận pin. Lấy K đề xuất pin lớn nhất; phần còn lại tắt. Do đèn có thể nhận pin 0, hiểu đây là số đèn **tối đa**, không buộc tất cả phải phát.

Câu hỏi dễ nói: “Nếu được mang nhiều thiết bị hơn, WOA có tận dụng được quyền ấy trong cùng lượt thử không?” Trong bộ này cả ba có 29/30 lần hợp lệ, nhưng U của K=6/8/10 khoảng 0.722/0.636/0.659. Không được từ đó kết luận ít đèn luôn có tiềm năng tốt hơn.

Về mặt mô hình, mọi phương án có 6 đèn phát đều có thể viết thành phương án 10 đèn bằng cách đặt pin bốn đèn còn lại bằng 0. Do đó bộ nghiệm cho phép tối đa 10 chứa bộ nghiệm tối đa 6. Điểm tối ưu toàn cục của K=10 không thể kém chỉ vì nó được phép nhiều hơn. WOA chạy hữu hạn lại có thể chưa tìm được cách tắt và phân bổ phù hợp. Phép chọn top-K còn thay hình dạng bề mặt tìm kiếm; đây là ngách về mô hình và biểu diễn, không phải thuần “số chiều”.

`results/K_embedding_check.csv` kiểm điều đó trên cả 29 nghiệm K=6 hợp lệ: đưa về K=10 bằng cách tắt các đèn không chọn, mọi đường vẫn hợp lệ và phần mục tiêu không đổi. Những nghiệm ấy **không được đưa vào đàn ban đầu**. Đây chỉ là một phép kiểm chứng để tránh diễn giải ngược số liệu.

## Ảnh để dùng

`1_l_A/B`, `2_bien_A/B`, `3_a`, `4_so_den` là sáu ảnh ONE_SHOT cho bốn ngách. Trên mỗi ảnh, bản đồ dùng seed 7 cố định, còn cột/râu và hai bảng dùng đủ 30 seed. Râu là độ lệch chuẩn mẫu, không tự là kiểm định ý nghĩa thống kê. File `paired.csv` so U trên những cặp cùng seed đều hợp lệ và đếm các cặp chỉ một bên thành công.
