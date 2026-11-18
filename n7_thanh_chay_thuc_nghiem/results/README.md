# Results directory

- `trials.csv` là CSV 330 dòng do nhóm cung cấp trước khi tích hợp lại N4/N6/N7. File được giữ nguyên như dữ liệu lịch sử tham chiếu; trong ZIP đầu vào không có 330 JSON lần chạy tương ứng để kiểm toán lại từng dòng.
- Khi chạy lại đầy đủ, các JSON mới sẽ được ghi vào `runs/`, benchmark vào `benchmarks/`, và `trials.csv` sẽ được xuất lại từ các JSON trong `runs/`.
- Replay A/B/C theo seed nhóm chọn được ghi vào `demos/`.
- Pilot được tách riêng trong `pilot/` và không được tính vào kết quả chính thức.
