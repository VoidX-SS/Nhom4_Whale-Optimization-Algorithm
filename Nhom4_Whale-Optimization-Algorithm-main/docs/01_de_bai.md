# Đề bài Đom Đóm — bản chốt thu gọn

Một UAV đi từ S=(0,50) đến T=(100,50) trong bản đồ giả định 100×100. UAV mang các thiết bị phát tín hiệu, gọi gần gũi là đom đóm, để hỗ trợ 8 trại có trọng số nhu cầu khác nhau. Trên đường có ba vùng cấm hình tròn và biên an toàn 2 đơn vị. Một túi năng lượng 220 được dùng chung cho bay và vận hành thiết bị trong một khoảng thời gian đã quy ước.

Tìm một đường gấp khúc qua 10 điểm trung gian và cách chia pin cho các đèn, sao cho mức hữu dụng cao và chi phí đường đi nhỏ, đồng thời tránh mọi vùng cấm và không vượt pin. Dùng WOA để tìm; dùng nhiều seed để đo độ ổn định. Mục đích seminar là hiểu cơ chế, cài đặt và các lựa chọn tìm kiếm của WOA qua bài toán này.

## Một cá voi mang gì?

Một cá voi là cả mảng `[x1,y1,E1,...,x10,y10,E10]`, có 30 biến. Tọa độ nằm trong 0..100; pin mỗi đèn trong 0..25. UAV đi theo thứ tự S, điểm 1, ..., điểm 10, T. Không sắp xếp theo x, vì đường có thể quay lại. Tọa độ và pin là đơn vị mô phỏng.

Bản cơ sở cho phép tối đa 10 đèn phát. Ngách số đèn chọn tối đa 6/8/10 đèn: giữ các đèn có pin đề xuất cao nhất, các đèn còn lại tắt và không tiêu pin. Những vị trí tắt vẫn là điểm đường bay. Vì vậy số điểm đường và số biến giữ nguyên. Đèn có pin gần 0 được vẽ rỗng, không đánh lừa mắt rằng chỗ ấy đang phát mạnh.

## Các phép đo

Độ dài L là tổng độ dài đoạn thẳng. Pin bay bằng 0.45*L. Pin đèn là tổng các E thực sự được bật. Tổng pin phải không vượt 220. Một đoạn chỉ được chấp nhận nếu khoảng cách ngắn nhất từ tâm mỗi bão đến đoạn ít nhất bằng bán kính cộng 2; kiểm toàn đoạn, không chỉ điểm đầu/cuối.

Tại trại m, tín hiệu là tổng `E / (1 + d*d/(18*18))` từ mọi đèn. Mức hữu dụng `u=1-exp(-0.1*I)`: khi còn thiếu tín hiệu, thêm một chút có ích nhiều; khi đã đủ, lợi ích tăng thêm chậm lại. U là trung bình các u có trọng số trại. Chỉ số này không phải phần trăm người được cứu, và không tự bảo đảm mọi trại đều được phục vụ đủ.

Phần mục tiêu cần nhỏ:

```text
base = -U + 0.12*L/100
```

Phần phạt giữ cố định:

```text
J = base + 100*collision + 30*over_pin*over_pin + 100*outside_map
```

Collision cộng bình phương độ lấn chuẩn hóa của từng cặp đoạn–bão. Over_pin bằng phần vượt pin chia 220, bằng 0 khi không vượt. Outside_map cộng bình phương mức vượt các cạnh chia 100. Lõi đã sửa biến về biên trước khi chấm nên thành phần ra map thường bằng 0; nó là kiểm tra bổ sung. Không còn thành phần phạt gấp khúc.

## Ba sổ ghi, chỉ một sổ dẫn đàn

Best_overall giữ J thấp nhất, theo đúng cơ chế leader của lõi. Best_valid giữ phần mục tiêu thấp nhất trong các nghiệm đã đủ luật. Best_gate giữ nghiệm hợp lệ từng đi qua cổng khe, phục vụ kiểm tra ca B. Hai sổ sau chỉ lưu bằng chứng, không thay leader.

Hàm phạt hữu hạn không tạo bức tường tuyệt đối. Một đường lấn bão rất nhẹ có thể có J thấp, vì vậy bảng luôn báo cả “đã tìm thấy hợp lệ ?/30” và “chính best_overall hợp lệ ?/30”. Khi chưa có best_valid, giao diện ghi chưa hợp lệ. Không sửa đường hoặc bớt pin sau tối ưu để đổi nhãn.

## Phạm vi

Đây là mô hình 2D tĩnh; chưa có gia tốc, góc quay vật lý, gió, độ cao, mất tín hiệu theo thời gian hoặc mô hình truyền sóng đã hiệu chuẩn. Vùng bão ràng buộc đường, không chặn tín hiệu. Đặt trùng đèn và điểm đường là điều đề hiện tại cho phép; không diễn giải chúng như bằng chứng UAV thật vận hành tốt.

Ca A là bản đồ cơ bản. B là khe giữa hai bão có cổng x=40, y từ 47 đến 53, đồng thời vẫn cho phép đi vòng ngoài. C là các bão chắn giữa đường. Cả ba dùng pin 220. Vì đề chưa bắt buộc qua khe, một nghiệm đi vòng vẫn hợp lệ.
