# Thực nghiệm ca gốc và cách đọc ảnh

## Trước các ngách, hỏi bản cơ sở làm được gì

Bản cơ sở là a linear, shared_l, clip; ba ca A/B/C đều có 30 biến, pin 220, N=30,T=800. A có 29/30 lần tìm được nghiệm hợp lệ, B có 30/30, C có 29/30. Utility trung bình của các lượt hợp lệ lần lượt khoảng 0.659,0.558,0.647; SD khoảng 0.141,0.183,0.123.

Chính nghiệm có J thấp nhất chỉ hợp lệ 0/30,5/30,6/30 ở ba ca. Đây là lý do không đồng nhất “điểm tốt nhất” với “đường đủ luật”. Các nghiệm được công nhận lấy từ best_valid. Bộ kết quả giữ cả lượt thất bại để số liệu không chỉ gồm những bài đẹp.

Ảnh `00_case_goc_tong_hop.png` đặt ba ca cạnh nhau, gồm map, cột/râu, bảng utility, bảng hợp lệ. Mỗi ca còn có ba loại ảnh: cả đàn qua sáu thời điểm; các seed tốt/điển hình/kém trong những lượt hợp lệ; pin và hữu dụng từng trại. Báo cáo HTML xếp chúng trước các ngách.

## Seed điển hình lấy bằng quy tắc nào?

Tìm phần mục tiêu `-U+0.12*L/100` gần trung vị nhất trong các lượt hợp lệ. Quy tắc này chọn A seed16, B seed11, C seed27. Seed có mục tiêu thấp nhất và cao nhất cũng được hiện cạnh nhau, ghi tên rõ ràng. Không gọi seed tốt nhất là “đại diện”. `results/representatives.json` lưu lựa chọn và các replay được chạy lại, đối chiếu khớp nghiệm trong lượt đo gốc.

## Đường xám nghĩa là gì?

Mỗi đường xám là cả chuyến bay được mã hóa bởi một cá voi ở thời điểm đang xem. Có đường xuyên bão hoặc quá pin; mình vẫn vẽ để thấy quá trình tìm. Đường nổi bật là nghiệm đang được lưu trong sổ, có thể được bắt gặp ở một lượt trước. Ở cuối, đàn có thể tụm sát nhau khiến nhiều nét xám chồng lên nét xanh. Đây không có nghĩa chỉ vẽ một cá voi; kéo replay về đầu sẽ thấy chúng tách ra.

Vàng là đèn có pin đáng kể; điểm rỗng có pin gần 0 hoặc đang tắt. Việc đèn trùng hoặc nằm sát mép không tự bị cấm bởi đề hiện tại. Tô đỏ chỉ những đoạn vi phạm vùng bão. Phần vượt pin được báo bằng số và nhãn hợp lệ, vì không có một đoạn riêng nào để tô cho việc ấy.

## Cột và râu

Cột là U trung bình trong các lượt hợp lệ. Râu là **độ lệch chuẩn mẫu**, giúp nhìn độ phân tán, không tự quyết định cột nào tốt nhất. Râu dài nghĩa kết quả dao động nhiều hơn, không phải bản thân nó luôn xấu; còn cần đọc độ cao, số lần thành công và mục tiêu muốn đạt.

“Có hợp lệ 26/30” nghĩa từng bắt gặp ít nhất một đường hợp lệ trong 26 lượt chạy. “Best overall 2/30” nghĩa chính phương án có J nhỏ nhất của hai lượt đủ điều kiện. “Từng qua khe 5/30” nghĩa đã từng có đường hợp lệ cắt qua cổng; nó chưa chắc là đường được chọn cuối. Ba cột trả lời ba câu hỏi khác nhau.

Các ảnh ngách dùng bản đồ seed7 cố định, nhưng cột và bảng dùng cả 30 seed. Do các biến thể có tập thành công khác nhau, nên còn có `paired.csv` để xem delta U ở những cặp cùng seed đều hợp lệ. Khác trung bình chưa tự là khác biệt có ý nghĩa thống kê; bộ này báo cáo mô tả, không gắn nhãn kiểm định chưa thực hiện.
