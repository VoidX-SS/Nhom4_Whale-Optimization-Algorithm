# Hướng dẫn chạy thí nghiệm N7 – Ngọc Thanh

## 1. Chuẩn bị

Mở terminal tại thư mục gốc repository, cài các thư viện cần thiết:

```bash
python -m pip install numpy pytest
```

Ba bản đồ đầu vào nằm trong `data/`: `co_ban.json`, `khe_hep.json`, `chan_duong.json`. Không sửa cấu trúc hoặc thông số của các JSON này nếu chưa được nhóm thống nhất.

## 2. Chạy kiểm thử trước

```bash
python -m pytest -q
```

Kiểm thử hiện có bao gồm kiểm tra dữ liệu N4, giải mã Top-K và 11 điều kiện của lõi WOA N6.

## 3. Chạy pilot (thí điểm)

Pilot được lưu riêng trong `results/pilot/`, không ghi đè kết quả chính:

```bash
python run_experiments.py --suite pilot
```

Mặc định pilot giới hạn tối đa 2 seed, 8 cá voi và 20 lượt. Đây chỉ là kiểm tra tích hợp, không được gộp vào số liệu 330 lượt chính thức.

## 4. Chạy 330 lượt đường bay

```bash
python run_experiments.py --suite path
```

Mặc định: 11 cấu hình × 30 seed, mỗi lượt N=30, T=800, tương ứng 24.000 lần đánh giá cho mỗi lần chạy. Kết quả JSON lưu tại `results/runs/`, CSV tổng hợp tại `results/trials.csv`.

Có thể chạy riêng một cấu hình khi cần kiểm tra:

```bash
python run_experiments.py --suite path --only A_goc --seeds 1 --population 30 --iterations 800
```

## 5. Chạy 90 benchmark

```bash
python run_experiments.py --suite benchmark
```

Gồm 3 hàm (quadratic, sphere, rastrigin) × 30 seed, N=30, T=500. Kết quả lưu trong `results/benchmarks/`.

## 6. Chạy toàn bộ

```bash
python run_experiments.py --suite all
```

Lệnh này chạy 330 lượt đường bay và 90 benchmark. Nên chạy pilot và kiểm thử trước; không chạy đồng thời nhiều tiến trình ghi vào cùng thư mục `results/`.

## 7. Replay A/B/C (phát lại thí nghiệm)

Chỉ chạy sau khi có dữ liệu gốc trong `results/runs/`. Nhập đúng danh sách seed đại diện do Trang Bùi/nhóm chọn; ví dụ dưới đây chỉ minh họa cú pháp, không phải seed được nhóm chỉ định:

```bash
python run_experiments.py --suite replay --replay-seeds 1,7,12
```

Chương trình chạy lại ba cấu hình gốc A/B/C, lưu JSON trong `results/demos/` và so sánh điểm tốt nhất cùng toàn bộ đàn cuối với lần chạy gốc. Kết quả đối chiếu nằm ở khóa `replay_check`.

## 8. Lưu ý về CSV

Mỗi lần chạy có một dòng. Nếu không tìm được nghiệm hợp lệ, các chỉ số chỉ có nghĩa khi tồn tại nghiệm hợp lệ sẽ để trống (`None` trong JSON, ô trống trong CSV), không thay bằng 0. Không xóa các lần chạy thất bại.

## 9. Đo thời gian

Trường `seconds` là thời gian chạy phần tối ưu hóa của một lần chạy, không bao gồm việc ghi JSON/CSV. Khi so sánh cấu hình, cần chạy trên cùng máy, cùng điều kiện tải máy và không bật trực quan hóa thời gian thực.
