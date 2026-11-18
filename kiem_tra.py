"""Những ví dụ nhỏ biết trước đáp án: python kiem_tra.py"""
import random
from src.n4_hoang_yen_du_lieu import load_problem, default_settings, decode, bounds, a_value
from src.n3_phuc_khang_danh_gia import evaluate, evaluate_benchmark, crosses_gate
from src.n5_quynh_ngan_buoc_woa import repair_population
from src.n6_van_lam_woa import woa


def main():
    problem = load_problem("khe_hep")
    route = [[10,50],[20,50],[30,50],[40,50],[50,50],[60,30],[70,30],[80,30],[90,30],[95,40]]
    whale = []
    for point in route:
        whale.extend([point[0],point[1],5])
    report = evaluate(whale,problem)
    assert report["valid"] and report["through_gate"]
    assert report["total"] < 220
    blocked = whale.copy()
    blocked[1] = 29
    blocked[4] = 29
    blocked[7] = 29
    assert not evaluate(blocked,problem)["valid"]
    for K in [6,8,10]:
        problem["active_lights"] = K
        beacons=decode(whale,problem)
        count=0
        for beacon in beacons:
            if beacon["active"]:count+=1
        assert count==K and len(whale)==30
    assert a_value(0,800,"linear")==2
    assert abs(a_value(799,800,"linear")-0.0025)<0.0000001
    pop=[[-5,0.5,6]]
    repair_population(pop,[0,0,0],[1,1,1],"clip",random.Random(7))
    assert pop==[[0,0.5,1]]
    s=default_settings();s["iterations"]=120
    bench={"function":"sphere","dimensions":30,"lower":-100,"upper":100}
    result=woa(evaluate_benchmark,bench,s)
    assert result["evaluations"]==30*120
    assert result["best_overall"]["evaluation"]["score"]<0.000001
    repeat=woa(evaluate_benchmark,bench,s)
    assert result["best_overall"]==repeat["best_overall"]
    assert result["history"]==repeat["history"]
    print("Qua kiểm tra: khe có đường hợp lệ, bão, pin, 30 biến, số đèn, a, biên, seed và benchmark.")


if __name__=="__main__":
    main()
