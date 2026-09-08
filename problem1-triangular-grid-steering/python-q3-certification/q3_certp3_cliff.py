# -*- coding: utf-8 -*-
"""q3_certp3_cliff.py — 任务2: 最优候选附近细扫 + 悬崖边刻画 + 悬崖宽度分布。

细网格(官方可表示格点):
  Δ1 步 0.001°(4位小数可表示); L1 通过 t_slow 0.0001s 时间网格落地, 步长 = V0*1e-4 ≈ 11.64 mm。
  (任务书"L1 步 1mm"与官方格式冲突: 0.0001s 时间网格下 L1 最小步长 11.64mm, 1mm 不可表示; 此处用 11.64mm 如实标注。)

悬崖边: 相邻格点(Δ1 向 / L1 向)分数差 > 1 m。
悬崖宽度: 对每条悬崖边, 在其两端格点之间的连续参数上做细采样(0.1mm / 0.0001°),
  直接测出过渡带宽度(分数从高到低的跨越距离); 全部并行。结果写入 q3_certp3_cliff.json。
"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3_certp3_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
COARSE_JSON = os.path.join(HERE, "q3_certp3_coarse.json")
OUT_JSON = os.path.join(HERE, "q3_certp3_cliff.json")

CLIFF_THRESH = 1.0
D1_STEP = 0.001
L1_STEP = core.V0 * 1e-4        # ~11.64 mm
REFINE_L1 = 0.0001              # 0.1 mm 细采样
REFINE_D1 = 0.0001              # 0.0001°

_ST = None


def _init_worker():
    global _ST
    _ST = core.state()


def _worker(task):
    d1, l1, slow = task
    r = core.terminal_score(d1, l1, slow, _ST)
    return (d1, round(l1, 6), slow, round(r, 6))


def _refine_worker(edge):
    global _ST
    if _ST is None:
        _ST = core.state()
    if edge["direction"] == "l1":
        lo, hi = edge["l1_a"], edge["l1_b"]
        step = REFINE_L1
        n = int(round((hi - lo) / step)) + 1
        xs = [lo + step * k for k in range(n)]
        vals = [core.terminal_score(edge["d1"], x, edge["slow"], _ST) for x in xs]
        return dict(edge, sweep=[(round(x, 7), round(v, 4)) for (x, v) in zip(xs, vals)])
    else:
        lo, hi = edge["d1_a"], edge["d1_b"]
        step = REFINE_D1
        n = int(round((hi - lo) / step)) + 1
        xs = [lo + step * k for k in range(n)]
        vals = [core.terminal_score(x, edge["l1"], edge["slow"], _ST) for x in xs]
        return dict(edge, sweep=[(round(x, 7), round(v, 4)) for (x, v) in zip(xs, vals)])


def run_pool(fn, tasks, nproc, chunksize=8):
    import multiprocessing as mp
    with mp.Pool(nproc, initializer=_init_worker) as pool:
        return pool.map(fn, tasks, chunksize=chunksize)


def load_argmax():
    if not os.path.exists(COARSE_JSON):
        return 9.835, 11.06, 1
    with open(COARSE_JSON, encoding="utf-8") as f:
        data = json.load(f)
    best = data["best"]
    return best[0], best[2], best[3]


def make_fine_tasks(d1c, l1c):
    d1s = [round(d1c - 0.10 + D1_STEP * k, 4) for k in range(201)]
    tc = round(core.t_slow_of(l1c) / 1e-4)
    half = int(round(0.25 / L1_STEP)) + 1
    l1s = sorted(set(round(((tc + k) * 1e-4 - core.TB) * core.V0, 6)
                     for k in range(-half, half + 1)))
    tasks = [(d1, l1, slow) for d1 in d1s for l1 in l1s for slow in (0, 1)]
    return tasks, d1s, l1s


def cliff_edges(grid, d1s, l1s):
    edges = []
    for slow in (0, 1):
        for j, l1 in enumerate(l1s):
            for i in range(len(d1s) - 1):
                a = grid.get((d1s[i], l1, slow)); b = grid.get((d1s[i + 1], l1, slow))
                if a is not None and b is not None and abs(a - b) > CLIFF_THRESH:
                    edges.append(dict(direction="d1", slow=slow, l1=l1,
                                      d1_a=d1s[i], d1_b=d1s[i + 1], s_a=a, s_b=b,
                                      dh=abs(a - b)))
        for i, d1 in enumerate(d1s):
            for j in range(len(l1s) - 1):
                a = grid.get((d1, l1s[j], slow)); b = grid.get((d1, l1s[j + 1], slow))
                if a is not None and b is not None and abs(a - b) > CLIFF_THRESH:
                    edges.append(dict(direction="l1", slow=slow, d1=d1,
                                      l1_a=l1s[j], l1_b=l1s[j + 1], s_a=a, s_b=b,
                                      dh=abs(a - b)))
    return edges


def transition_width(sweep):
    """从细采样序列估过渡带宽度: 高分数(>445)与低分数(<443)之间的跨越距离。"""
    xs = [s[0] for s in sweep]
    vs = [s[1] for s in sweep]
    hi = max(vs); lo = min(vs)
    if hi - lo < 1.0:
        return dict(width=None, crit=None, hi=hi, lo=lo)
    mid = 0.5 * (hi + lo)
    # 找分数跨过 mid 的位置区间
    cross = []
    for i in range(len(vs) - 1):
        if (vs[i] - mid) * (vs[i + 1] - mid) < 0:
            cross.append((xs[i], xs[i + 1]))
    crit = None
    if cross:
        # 取第一个跨越
        xa, xb = cross[0]
        crit = 0.5 * (xa + xb)
    # 过渡带宽度: 从最后一次 >= hi-0.5 到第一次 <= lo+0.5
    last_hi = None; first_lo = None
    for x, v in sweep:
        if v >= hi - 0.5:
            last_hi = x
    for x, v in sweep:
        if v <= lo + 0.5:
            first_lo = x
            break
    width = None
    if last_hi is not None and first_lo is not None:
        width = abs(first_lo - last_hi)
    return dict(width=width, crit=crit, hi=hi, lo=lo)


def main():
    d1c, l1c, slowc = load_argmax()
    print(f"argmax(粗网格) = (Δ1={d1c:.4f}, L1_real={l1c:.4f}, slow={slowc})")
    nproc = 8
    if "--nproc" in sys.argv:
        nproc = int(sys.argv[sys.argv.index("--nproc") + 1])
    maxref = 40
    if "--maxref" in sys.argv:
        maxref = int(sys.argv[sys.argv.index("--maxref") + 1])

    tasks, d1s, l1s = make_fine_tasks(d1c, l1c)
    print(f"细网格: Δ1={len(d1s)} 值 (步 {D1_STEP}°) × L1={len(l1s)} 值 (步 {L1_STEP*1000:.2f}mm) "
          f"× slow=2 → {len(tasks)} 方案")
    t0 = time.perf_counter()
    results = run_pool(_worker, tasks, nproc)
    dt = time.perf_counter() - t0
    print(f"细扫完成: {len(results)} 方案, 耗时 {dt:.1f}s")

    grid = {(d1, l1, slow): r for (d1, l1, slow, r) in results}
    best = max(results, key=lambda x: x[3])
    print(f"细网格最优 = {best[3]:.4f} @ (Δ1={best[0]:.4f}, L1={best[1]:.4f}, slow={best[2]})")

    edges = cliff_edges(grid, d1s, l1s)
    edges.sort(key=lambda e: -e["dh"])
    print(f"\n=== 悬崖边 (相邻格点分数差 > {CLIFF_THRESH} m) ===")
    print(f"悬崖边总数 = {len(edges)}")
    from collections import Counter
    print(f"按方向: {dict(Counter(e['direction'] for e in edges))}")
    if edges:
        dhv = [e["dh"] for e in edges]
        print(f"步高分布: min={min(dhv):.3f} max={max(dhv):.3f} 中位={sorted(dhv)[len(dhv)//2]:.3f} m")
    for e in edges[:15]:
        if e["direction"] == "l1":
            print(f"  L1向 slow={e['slow']} Δ1={e['d1']:.3f}: L1 {e['l1_a']:.4f}→{e['l1_b']:.4f} "
                  f"(间隔{abs(e['l1_b']-e['l1_a'])*1000:.2f}mm) 分数 {e['s_a']:.3f}→{e['s_b']:.3f} Δ={e['dh']:.3f}")
        else:
            print(f"  Δ1向 slow={e['slow']} L1={e['l1']:.4f}: Δ1 {e['d1_a']:.3f}→{e['d1_b']:.3f} "
                  f"分数 {e['s_a']:.3f}→{e['s_b']:.3f} Δ={e['dh']:.3f}")

    # 并行细采样测过渡带宽度 (取步高最大的 maxref 条)
    ref_edges = edges[:maxref]
    print(f"\n=== 悬崖过渡带细采样 (前 {len(ref_edges)} 条, L1步0.1mm / Δ1步0.0001°) ===")
    t1 = time.perf_counter()
    refined = run_pool(_refine_worker, ref_edges, nproc, chunksize=1)
    dt2 = time.perf_counter() - t1
    print(f"细采样完成: {len(refined)} 条悬崖边, 耗时 {dt2:.1f}s")

    widths = []
    for r in refined:
        tw = transition_width(r["sweep"])
        r["tw"] = tw
        if tw["width"] is not None:
            widths.append(tw["width"])
        dirn = r["direction"]
        if dirn == "l1":
            unit = "m"
        else:
            unit = "deg"
        print(f"  {dirn}向 slow={r['slow']} (Δ1={r.get('d1', r.get('l1'))}): "
              f"步高 {r['dh']:.3f}, 过渡带宽度={tw['width'] if tw['width'] is not None else 'N/A'} "
              f"{unit}, 临界={tw['crit']} {unit}")

    if widths:
        wm = sorted(widths)
        print(f"\n=== 悬崖宽度分布 ===")
        print(f"条数={len(widths)}  min={min(widths)*1000:.3f}mm  max={max(widths)*1000:.3f}mm  "
              f"中位={wm[len(wm)//2]*1000:.3f}mm")
        # 分箱
        import numpy as np
        mm = [w * 1000 for w in widths]
        hist, edges_ = np.histogram(mm, bins=[0, 0.5, 1, 2, 5, 10, 20, 50, 100])
        print("  宽度直方图 (mm, 箱界 [0,0.5,1,2,5,10,20,50,100]):")
        for i in range(len(hist)):
            if hist[i] > 0:
                print(f"    [{edges_[i]:.1f}, {edges_[i+1]:.1f}) mm : {hist[i]}")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dict(
            argmax_coarse=[d1c, l1c, slowc], best_fine=list(best[:4]),
            n_tasks=len(tasks), dt_s=dt, dt_refine_s=dt2,
            d1s=d1s, l1s=l1s, cliff_edges=edges,
            refined=[{k: v for k, v in r.items() if k != "sweep"} for r in refined],
            widths_mm=[w * 1000 for w in widths],
        ), f, ensure_ascii=False, indent=1)
    print(f"\n结果已写入 {OUT_JSON}")


if __name__ == "__main__":
    main()
