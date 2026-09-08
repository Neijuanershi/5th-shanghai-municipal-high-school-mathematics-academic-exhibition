# -*- coding: utf-8 -*-
# q3_certp4_root_enum_1w.py — root 保险枚举(后台 pwsh 运行,不受子代理停驻影响)
# 用法: python q3_certp4_root_enum_1w.py <d1_lo> <d1_hi> <out_json> [nproc]
# 网格: Δ1∈[d1_lo,d1_hi] 步 0.0001° × L1 官方网格(0.0001 s 步,t_slow∈3.8826..3.8921)
#        × slow∈{0,1}。评分 = q3_certp3_core.terminal_score(已验证与完整 cxk 等价 1e-12)。
# 用 q3_certp4_fast.patch() 把 cxk.min_dist_rot 换成逐位等价的加速版。
# 只新建输出 JSON;不改任何既有文件。
import json
import math
import multiprocessing as mp
import sys
import time

import q3_certp4_fast
import q3_certp3_core as core

q3_certp4_fast.patch()   # 位等价加速(3-5x),P4-A 已验证

V = 10.0 * (1.25 ** 11)          # 116.4153...
KS = list(range(902, 998))       # t_slow = 3.7924 + k*0.0001, L1∈[10.5,11.6]
L1S = [k * 0.0001 * V for k in KS]


def anchor_check():
    ok = True
    for d1, l1, slow, exp in [
        (9.8305, L1S[KS.index(950)], 1, 447.9733),   # k=950 → t_slow=3.8874, L1=11.059456
        (9.8310, L1S[KS.index(950)], 1, 447.9725),
        (9.8350, L1S[KS.index(950)], 1, 447.9657),
        (9.8500, L1S[KS.index(947)], 1, 447.9601),   # k=947 → 3.8871
        (9.8304, L1S[KS.index(950)], 1, 439.4987),
        (9.8328, L1S[KS.index(949)], 1, 440.4239),   # k=949 → 3.8873
    ]:
        s = core.terminal_score(d1, l1, slow)
        d = abs(s - exp)
        flag = "OK" if d < 1e-4 else "FAIL"
        if d >= 1e-4:
            ok = False
        print("  anchor d1=%.4f l1=%.6f slow=%d: score=%.6f exp=%.6f |d|=%.2e %s"
              % (d1, l1, slow, s, exp, d, flag), flush=True)
    return ok


def work(args):
    d1, l1, slow = args
    return (d1, l1, slow, core.terminal_score(d1, l1, slow))


def main():
    d1_lo = float(sys.argv[1])
    d1_hi = float(sys.argv[2])
    out_json = sys.argv[3]
    nproc = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    t0 = time.time()
    print("root 保险枚举: Δ1∈[%.4f, %.4f] 步 0.0001° × L1 官方网格(%d 值) × slow∈{0,1}"
          % (d1_lo, d1_hi, len(L1S)), flush=True)
    print("锚点检查:", flush=True)
    if not anchor_check():
        print("锚点检查失败,中止!", flush=True)
        sys.exit(1)

    d1s = []
    k = 0
    while True:
        v = d1_lo + k * 0.0001
        if v > d1_hi + 1e-12:
            break
        d1s.append(round(v, 4))
        k += 1
    tasks = [(d1, l1, s) for d1 in d1s for l1 in L1S for s in (0, 1)]
    n = len(tasks)
    print("总方案数 = %d, 进程数 = %d" % (n, nproc), flush=True)
    with mp.Pool(nproc) as pool:
        results = pool.map(work, tasks, chunksize=200)

    # 汇总
    best = max(results, key=lambda r: r[3])
    col = {}          # d1 -> 该列 max
    cliffs = []       # 相邻 L1 格点分数差 > 1 m 的边
    for d1, l1, s, score in results:
        if d1 not in col or score > col[d1]:
            col[d1] = score
    for d1 in d1s:
        for i in range(len(L1S) - 1):
            a = next(r[3] for r in results if r[0] == d1 and r[1] == L1S[i] and r[2] == 1)
            b = next(r[3] for r in results if r[0] == d1 and r[1] == L1S[i + 1] and r[2] == 1)
            if abs(b - a) > 1.0:
                cliffs.append(dict(d1=d1, l1_a=L1S[i], l1_b=L1S[i + 1],
                                   s_a=a, s_b=b, dh=b - a))
    top = sorted(results, key=lambda r: -r[3])[:20]
    out = dict(d1_lo=d1_lo, d1_hi=d1_hi, n=n, wall_s=time.time() - t0,
               best=list(best), top20=[list(t) for t in top],
               col_max={str(d): col[d] for d in sorted(col)},
               n_cliffs=len(cliffs), cliffs=cliffs[:50])
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("max = %.6f @ d1=%s l1=%s slow=%s" % (best[3], best[0], best[1], best[2]))
    print("top-5:")
    for t in top[:5]:
        print("   d1=%.4f l1=%.6f slow=%d -> %.6f" % (t[0], t[1], t[2], t[3]))
    print("悬崖边数 = %d" % len(cliffs))
    print("耗时 = %.1f s, 结果已写入 %s" % (out["wall_s"], out_json), flush=True)


if __name__ == "__main__":
    main()
