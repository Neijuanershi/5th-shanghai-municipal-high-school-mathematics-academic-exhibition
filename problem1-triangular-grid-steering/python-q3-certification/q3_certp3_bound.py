# -*- coding: utf-8 -*-
"""q3_certp3_bound.py — 任务3: 粗认证上界 U_coarse + 任务4: top-3 certify_plan 核验。

U_coarse = max_found + 2 * (粗网格相邻格点分数差最大值)。
明确标注: 这是"采样级粗界, 非严格认证界"(网格间不可见改进用相邻差分×2 粗包络, 非 Lipschitz 证明)。
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3_certp3_core as core
import cxk

HERE = os.path.dirname(os.path.abspath(__file__))
COARSE_JSON = os.path.join(HERE, "q3_certp3_coarse.json")
CLIFF_JSON = os.path.join(HERE, "q3_certp3_cliff.json")

KNOWN = [("连续 argmax (9.832764°,11.052704) 不可表示", 447.9733, "舍入后 440.42"),
         ("族内 cxk 最优 (9.835°,11.06,1)", 447.9657, "可表示"),
         ("纪录 q3_campaign_best_saA.txt", 447.8980, "可表示")]


def load_coarse():
    with open(COARSE_JSON, encoding="utf-8") as f:
        return json.load(f)


def coarse_max_adj_diff(data):
    """粗网格相邻格点分数差最大值 (Δ1 向 + L1 向 + slow 向)。"""
    d1s = data["d1s"]
    l1s = data["l1s"]  # nominal L1
    allres = data["all"]  # list of [d1, L1_nom, L1_real, slow, score, valid]
    grid = {(r[0], r[1], r[3]): r[4] for r in allres}
    maxd = 0.0
    arg = None
    for d1 in d1s:
        for L1 in l1s:
            for slow in (0, 1):
                a = grid.get((d1, L1, slow))
                if a is None:
                    continue
                # slow 向
                b = grid.get((d1, L1, 1 - slow))
                if b is not None and abs(a - b) > maxd:
                    maxd = abs(a - b); arg = ("slow", d1, L1, slow, a, b)
                # L1 向
                j = l1s.index(L1)
                if j + 1 < len(l1s):
                    b = grid.get((d1, l1s[j + 1], slow))
                    if b is not None and abs(a - b) > maxd:
                        maxd = abs(a - b); arg = ("L1", d1, L1, slow, a, b)
                # Δ1 向
                i = d1s.index(d1)
                if i + 1 < len(d1s):
                    b = grid.get((d1s[i + 1], L1, slow))
                    if b is not None and abs(a - b) > maxd:
                        maxd = abs(a - b); arg = ("Δ1", d1, L1, slow, a, b)
    return maxd, arg


def certify_top3(data, n=3):
    """对 top-3 候选跑 q3_cert_merge_sa3.certify_plan。返回报告列表。"""
    try:
        import q3_cert_merge_sa3 as cert
    except Exception as e:
        return [f"certify_plan 不可用: {e}"]
    allres = sorted(data["all"], key=lambda r: -r[4])
    # 取合法(Δ1≤10) top-3, 去重(d1, L1_real, slow)
    seen = set()
    tops = []
    for r in allres:
        if not r[5]:
            continue
        key = (r[0], round(r[2], 6), r[3])
        if key in seen:
            continue
        seen.add(key)
        tops.append(r)
        if len(tops) >= n:
            break
    reports = []
    for i, r in enumerate(tops):
        d1, L1nom, L1real, slow, score, valid = r
        tmp = os.path.join(HERE, f"q3_certp3_top{i+1}.txt")
        try:
            core.build_plan(d1, L1nom, slow, tmp)
            c = cert.certify_plan(tmp)
            reports.append(dict(d1=d1, L1nom=L1nom, L1real=L1real, slow=slow,
                                score=score,
                                finite_ok=(not c["any_collision"]) and (c["worst_cert"] > 9.0),
                                ray=c["ray"], sim=c["sim"]["r"]))
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
    return reports


def main():
    data = load_coarse()
    allres = data["all"]
    valid = [r for r in allres if r[5]]
    best_valid = max(valid, key=lambda r: r[4])
    best_all = max(allres, key=lambda r: r[4])

    max_found = best_valid[4]
    max_adj, arg = coarse_max_adj_diff(data)
    U_coarse = max_found + 2.0 * max_adj

    print("=== 任务3: 粗认证上界 U_coarse ===")
    print(f"max_found (粗网格合法域最优) = {max_found:.4f} @ "
          f"(Δ1={best_valid[0]:.2f}, L1名={best_valid[1]:.2f}, L1实={best_valid[2]:.4f}, slow={best_valid[3]})")
    print(f"粗网格全局最优(含非法Δ1>10) = {best_all[4]:.4f} @ (Δ1={best_all[0]:.2f}, slow={best_all[3]})")
    print(f"粗网格相邻格点分数差最大值 = {max_adj:.4f} m  (方向={arg[0]})")
    print(f"U_coarse = max_found + 2 × {max_adj:.4f} = {U_coarse:.4f} m")
    print(f"\n[标注] U_coarse={U_coarse:.4f} 是采样级粗界, 非严格认证界。")
    print("  原理: 相邻格点分数差的最大值 ×2 作为网格间不可见改进的粗包络; 未用 Lipschitz 常数严格证明。")

    print("\n=== 与已知值对照 ===")
    for label, val, note in KNOWN:
        print(f"  {label}: {val:.4f}  ({note})")
    print(f"  max_found(粗网格) = {max_found:.4f}")
    if os.path.exists(CLIFF_JSON):
        with open(CLIFF_JSON, encoding="utf-8") as f:
            cj = json.load(f)
        bf = cj.get("best_fine")
        if bf:
            print(f"  细网格最优(任务2) = {bf[3]:.4f} @ (Δ1={bf[0]:.4f}, L1={bf[1]:.4f}, slow={bf[2]})")

    print("\n=== 任务4: top-3 certify_plan 核验 ===")
    reports = certify_top3(data, 3)
    if isinstance(reports, list) and reports and isinstance(reports[0], str):
        print("  " + reports[0])
    else:
        for r in reports:
            ray = r["ray"]
            if "error" in ray:
                ray_desc = f"异常 {ray.get('error')}"
            else:
                ray_desc = f"r_lo={ray['r_lo']:.4f} r_hi={ray['r_hi']:.4f} width={ray['r_hi']-ray['r_lo']:.4f}"
            print(f"  Δ1={r['d1']:.3f} L1={r['L1real']:.4f} slow={r['slow']} "
                  f"score={r['score']:.4f} | 有限段{'PASS' if r['finite_ok'] else 'FAIL'} "
                  f"| 射线 {ray_desc} | cxk={r['sim']:.4f}")

    # 输出汇总(供报告用)
    print("\n=== 汇总键值 ===")
    print(f"max_found={max_found:.6f}")
    print(f"max_adj_diff={max_adj:.6f}")
    print(f"U_coarse={U_coarse:.6f}")


if __name__ == "__main__":
    main()
