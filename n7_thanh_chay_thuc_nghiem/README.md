# Nhóm 4 – Whale Optimization Algorithm

## Cấu trúc thực nghiệm N7

- `data/`: ba JSON A/B/C do nhóm cung cấp (giữ nguyên).
- `src/n4_hoang_yen_du_lieu.py`: tải, xác thực và chuẩn hóa alias dữ liệu cho các module cũ.
- `src/n3_phuc_khang_danh_gia.py`: hàm đánh giá bài toán bay và benchmark.
- `src/n5_quynh_ngan_buoc_woa.py`: hook cập nhật, l độc lập và sửa biên.
- `src/n6_van_lam_woa.py`: lõi WOA, lưu history và snapshot toàn đàn.
- `src/n7_ngoc_thanh_thuc_nghiem.py`: 11 cấu hình, 330 lượt đường bay, 90 benchmark, CSV và replay.
- `results/`: CSV được nhóm cung cấp và nơi lưu kết quả chạy mới.

## Chạy

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python run_experiments.py --suite pilot
python run_experiments.py --suite all
```

Xem hướng dẫn chi tiết tại `docs/07_huong_dan_thuc_nghiem_ngoc_thanh.md`.
