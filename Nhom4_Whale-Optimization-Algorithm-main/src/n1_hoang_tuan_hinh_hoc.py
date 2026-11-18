"""Hoàng Tuấn: đo đường, soi từng đoạn xem có chạm bão không.

Đừng chỉ nhìn các chấm thả đèn. Hai chấm đều ở ngoài bão nhưng sợi dây
nối chúng vẫn có thể xuyên giữa bão. Vì vậy mình phải kiểm tra cả dây.
"""

import math


def distance(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return math.sqrt(dx * dx + dy * dy)


def distance_to_segment(point, a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    square_length = dx * dx + dy * dy
    if square_length == 0:
        # Hai chấm trùng nhau: sợi dây co thành một chấm, vẫn đo được.
        return distance(point, a)
    t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / square_length
    t = max(0, min(1, t))
    nearest = [a[0] + t * dx, a[1] + t * dy]
    return distance(point, nearest)


def path_metrics(points, storms, safety):
    length = 0
    collision = 0
    clearance = None
    bad_segments = []
    backtrack = 0

    for i in range(len(points) - 1):
        a = points[i]
        b = points[i + 1]
        length += distance(a, b)
        backtrack += max(0, a[0] - b[0])
        bad = False
        for storm in storms:
            center = [storm["x"], storm["y"]]
            safe_radius = storm["r"] + safety
            gap = distance_to_segment(center, a, b) - safe_radius
            if clearance is None or gap < clearance:
                clearance = gap
            if gap < -0.000000001:
                bad = True
            # Đi sâu vào vùng cấm thì phạt nhiều; ra ngoài thì bằng 0.
            depth = max(0, -gap) / safe_radius
            collision += depth * depth
        if bad:
            bad_segments.append(i)

    return {
        "length": length,
        "collision": collision,
        "clearance": clearance,
        "bad_segments": bad_segments,
        "backtrack": backtrack,
    }
