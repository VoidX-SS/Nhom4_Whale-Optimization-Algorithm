"""Quỳnh Ngân: dịch ba nhánh của WOA.m sang Python dễ đọc.

Đối chiếu bản MATLAB đặt ở tham_khao_tac_gia/WOA.m nhé.
A, C và l dùng chung cho một cá voi ở bản cơ sở, đúng mã ấy.
"""
import math


def initialize_population(size, lower, upper, rng):
    population = []
    for i in range(size):
        whale = []
        for j in range(len(lower)):
            whale.append(lower[j] + rng.random() * (upper[j] - lower[j]))
        population.append(whale)
    return population


def repair_population(population, lower, upper, mode, boundary_rng):
    changed = 0
    for whale in population:
        for j in range(len(whale)):
            if whale[j] < lower[j] or whale[j] > upper[j]:
                changed += 1
                if mode == "clip":
                    whale[j] = max(lower[j], min(upper[j], whale[j]))
                else:
                    whale[j] = lower[j] + boundary_rng.random() * (upper[j] - lower[j])
    return changed


def update_population(population, leader, a, a2, settings, rng, l_rng):
    counts = {"search": 0, "encircle": 0, "spiral": 0}
    for i in range(len(population)):
        r1 = rng.random()
        r2 = rng.random()
        A = 2 * a * r1 - a
        C = 2 * r2
        b = settings["b"]
        l = (a2 - 1) * rng.random() + 1
        p = rng.random()
        if p >= 0.5:
            counts["spiral"] += 1
        elif abs(A) >= 1:
            counts["search"] += 1
        else:
            counts["encircle"] += 1

        for j in range(len(leader)):
            if p < 0.5:
                if abs(A) >= 1:
                    # Trong MATLAB, chọn lại chỉ số nằm BÊN TRONG vòng j.
                    # Và đàn được sửa tại chỗ, không chụp cả đàn cũ.
                    index = int(len(population) * rng.random())
                    reference = population[index][j]
                else:
                    reference = leader[j]
                D = abs(C * reference - population[i][j])
                population[i][j] = reference - A * D
            else:
                this_l = l
                if settings["l_mode"] == "independent_l" and j > 0:
                    # Hộp thẻ riêng giúp ngách l không xáo trộn các r1/r2/p.
                    this_l = (a2 - 1) * l_rng.random() + 1
                D = abs(leader[j] - population[i][j])
                population[i][j] = leader[j] + D * math.exp(b * this_l) * math.cos(2 * math.pi * this_l)
    # Chưa sửa biên ở đây: mã tác giả sửa ở đầu lượt chấm tiếp theo.
    # Điều này còn ảnh hưởng các cá voi được tham khảo khi sửa tại chỗ.
    return counts
