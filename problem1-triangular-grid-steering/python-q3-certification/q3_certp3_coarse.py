# -*- coding: utf-8 -*-
"""q3_certp3_coarse.py — 任务1: 终局族粗网格全枚举 (Δ1×L1×slow) + top-20 + 分数直方图。

网格: Δ1∈[8.5,11.0] 步 0.05°(51值) × L1∈[10.5,11.6] 步 0.02m(56值, 官方 0.0001s 时间网格落地) × slow∈{0,1}
共 51*56*2 = 5712 个官方格式方案, 用 fast terminal_score(与 cxk.simulate 逐位等价, 见 verify)评估。
结果写入 q3_certp3_coarse.json, 控制台打印 top-20 与直方图。
用法: python q3_certp3_coarse.py [--selftest] [--nproc N]
"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3_certp3_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "q3_certp3_coarse.json")

D1S = [round(8.5 + 0.05 * k, 4) for k in range(51)]    # 8.5 .. 11.0
L1S = [round(10.5 + 0.02 * k, 4) for k in range(56)]   # 10.5 .. 11.6


def realized_l1(L1):
    ts = round(core.t_slow_of(L1) / 1e-4) * 1e-4
    return (ts - core.TB) * core.V0


def make_tasks():
    tasks = []
    for d1 in D1S:
        for L1 in L1S:
            lr = realized_l1(L1)
            for slow in (0, 1):
                tasks.append((d1, L1, lr, slow))
    return tasks


_ST = None


def _init_worker():
    global _ST
    _ST = core.state()


def _worker(task):
    d1, L1, lr, slow = task
    r = core.terminal_score(d1, lr, slow, _ST)
    valid = abs(d1 - min(5.0, d1)) <= 5.0 + 1e-6
    return (d1, L1, round(lr, 6), slow, round(r, 6), valid)


def run(tasks, nproc):
    import multiprocessing as mp
    t0 = time.perf_counter()
    with mp.Pool(nproc, initializer=_init_worker) as pool:
        results = pool.map(_worker, tasks, chunksize=16)
    dt = time.perf_counter() - t0
    return results, dt


def main():
    args = sys.argv[1:]
    nproc = 8
    selftest = False
    if "--nproc" in args:
        nproc = int(args[args.index("--nproc") + 1])
    if "--selftest" in args:
        selftest = True

    tasks = make_tasks()
    print(f"任务数 = {len(tasks)}  (Δ1={len(D1S)} × L1={len(L1S)} × slow=2)")
    print(f"Δ1 范围 [{D1S[0]}, {D1S[-1]}]  L1 范围 [{L1S[0]}, {L1S[-1]}]")
    print(f"nproc = {nproc}")

    if selftest:
        tasks = tasks[:64]
        print(f"[selftest] 只跑前 {len(tasks)} 个任务")
    t0 = time.perf_counter()
    results, dt = run(tasks, nproc)
    wall = time.perf_counter() - t0
    print(f"评估完成: {len(results)} 个方案, 并行耗时 {dt:.1f}s, 总墙钟 {wall:.1f}s "
          f"(约 {wall/len(results)*1000:.0f} ms/方案/核心)")

    # 分数直方图 (0.5 m 箱)
    import numpy as np
    scores = [r[4] for r in results]
    lo = math.floor(min(scores))
    hi = math.ceil(max(scores))
    bins = np.arange(lo, hi + 0.5, 0.5)
    hist, edges = np.histogram(scores, bins=bins)
    print(f"\n=== 分数直方图 (箱宽 0.5 m, 范围 [{lo},{hi}]) ===")
    for i in range(len(hist)):
        if hist[i] > 0:
            print(f"  [{edges[i]:6.1f}, {edges[i+1]:6.1f}) : {hist[i]}")

    # top-20
    results_sorted = sorted(results, key=lambda r: -r[4])
    print(f"\n=== top-20 (按分数降序) ===")
    print(f"{'#':>2} {'Δ1':>7} {'L1名':>6} {'L1实':>9} {'slow':>4} {'score':>9} {'合法':>4}")
    for i, (d1, L1, lr, slow, r, valid) in enumerate(results_sorted[:20]):
        print(f"{i+1:>2} {d1:>7.2f} {L1:>6.2f} {lr:>9.4f} {slow:>4} {r:>9.4f} "
              f"{'OK' if valid else '!!'}")

    # 统计
    valid_results = [r for r in results if r[5]]
    n_valid = len(valid_results)
    n_invalid = len(results) - n_valid
    best = results_sorted[0]
    best_valid = max(valid_results, key=lambda r: r[4]) if valid_results else None
    print(f"\n=== 汇总 ===")
    print(f"合法方案(Δ1≤10, 100卡) = {n_valid}; 非法(Δ1>10 第二转向>5°) = {n_invalid}")
    print(f"全局最优 = {best[4]:.4f} @ (Δ1={best[0]:.2f}, L1名={best[1]:.2f}, "
          f"L1实={best[2]:.4f}, slow={best[3]}, 合法={best[5]})")
    if best_valid is not None:
        print(f"合法域最优 = {best_valid[4]:.4f} @ (Δ1={best_valid[0]:.2f}, "
              f"L1实={best_valid[2]:.4f}, slow={best_valid[3]})")

    if not selftest:
        data = dict(
            d1s=D1S, l1s=L1S, n=len(results), wall_s=wall, dt_s=dt,
            top20=results_sorted[:20], best=results_sorted[0],
            hist_bins=[float(b) for b in edges], hist_counts=[int(h) for h in hist],
            all=results_sorted,
        )
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"\n结果已写入 {OUT_JSON}")


if __name__ == "__main__":
    main()
