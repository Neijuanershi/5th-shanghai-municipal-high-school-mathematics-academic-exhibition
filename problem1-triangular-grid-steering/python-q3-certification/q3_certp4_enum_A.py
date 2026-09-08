# -*- coding: utf-8 -*-
"""q3_certp4_enum_A.py — Q3 左半区 A 官方可表示网格全枚举 (checkpoint/resume + 8 进程, chunksize=1)。

网格 A:
  Δ1 ∈ [9.8000, 9.8500) 步 0.0001° (500 值)
  t_slow = 3.7924 + k*0.0001, k ∈ [902, 996] (95 值; L1 ∈ [10.5, 11.6] 闭区间落地)
  slow ∈ {0, 1}   -> n = 500*95*2 = 95000

评分器: q3_certp3_core.terminal_score (与 cxk.simulate 逐位等价, 见 q3_certp4_verifyA.py)。

checkpoint: 逐条追加结果到 q3_certp4_enum_A.results.jsonl; 重启自动跳过已完成方案。
最终聚合写 q3_certp4_enum_A.json。
"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3_certp3_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "q3_certp4_enum_A.results.jsonl")
OUT_JSON = os.path.join(HERE, "q3_certp4_enum_A.json")

TB = core.TB
V0 = core.V0
L1_STEP = V0 * 1e-4
D1_LO, D1_HI, D1_N = 9.8000, 9.8500, 500
K_LO, K_HI = 902, 996
CLIFF_THRESH = 1.0

D1S = [round((98000 + i) * 1e-4, 4) for i in range(D1_N)]
KS = list(range(K_LO, K_HI + 1))
TSLOW = [round(TB + k * 1e-4, 4) for k in KS]
L1S = [round(k * 1e-4 * V0, 6) for k in KS]

_ST = None


def _init_worker():
    global _ST
    import q3_certp4_fast
    q3_certp4_fast.patch()   # 位等价快速 min_dist_rot (200000 点逐位核对 0 差异)
    _ST = core.state()


def _score(task):
    i, k, s = task
    r = core.terminal_score(D1S[i], k * 1e-4 * V0, s, _ST)
    return (i, k, s, r)


def _card_lines(d1, t_slow, slow):
    x = round(d1 - 5.0, 4)
    if slow:
        return [f"R {TB:.4f} 5.0000", f"R {TB:.4f} {x:.4f}", f"- {t_slow:.4f}"]
    return [f"R {TB:.4f} 5.0000", f"R {TB:.4f} {x:.4f}", f"R {t_slow:.4f} 0.0000"]


def load_done():
    done = set()
    if os.path.exists(RESULTS):
        with open(RESULTS, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                i, k, s, r = json.loads(ln)
                done.add((i, k, s))
    return done


def aggregate(t_wall_s, nproc):
    rows = []
    with open(RESULTS, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    n = len(rows)
    grid = {(i, k, s): r for (i, k, s, r) in rows}
    rows.sort(key=lambda x: -x[3])
    bi, bk, bs, br = rows[0]

    col_max = []
    for i in range(D1_N):
        best = max((grid[(i, k, s)], k, s) for k in KS for s in (0, 1))
        r, k, s = best
        col_max.append(dict(d1=D1S[i], r=round(r, 6), k=k, t_slow=TSLOW[KS.index(k)],
                            l1=round(k * 1e-4 * V0, 6), slow=s, X=round(D1S[i] - 5.0, 4)))

    col_check = []
    for lbl, exp in [("9.8305", 447.9733), ("9.8310", 447.9725)]:
        d1 = float(lbl)
        if d1 in D1S:
            got = col_max[D1S.index(d1)]["r"]
            col_check.append(dict(d1=lbl, expected=exp, got=got,
                                  diff=round(got - exp, 6), ok=bool(abs(got - exp) <= 5e-4)))
        else:
            col_check.append(dict(d1=lbl, expected=exp, got=None, diff=None, ok=False))

    cliff_l1 = []
    for i in range(D1_N):
        for s in (0, 1):
            for a in range(len(KS) - 1):
                ka, kb = KS[a], KS[a + 1]
                ra, rb = grid[(i, ka, s)], grid[(i, kb, s)]
                if abs(ra - rb) > CLIFF_THRESH:
                    cliff_l1.append(dict(d1=D1S[i], slow=s, k_a=ka, k_b=kb,
                                         l1_a=round(ka * 1e-4 * V0, 6), l1_b=round(kb * 1e-4 * V0, 6),
                                         t_a=TSLOW[a], t_b=TSLOW[a + 1],
                                         s_a=round(ra, 6), s_b=round(rb, 6), dh=round(abs(ra - rb), 6)))
    cliff_d1 = []
    for k in KS:
        for s in (0, 1):
            for i in range(D1_N - 1):
                ra = grid[(i, k, s)]; rb = grid[(i + 1, k, s)]
                if abs(ra - rb) > CLIFF_THRESH:
                    cliff_d1.append(dict(k=k, slow=s, d1_a=D1S[i], d1_b=D1S[i + 1],
                                         l1=round(k * 1e-4 * V0, 6), t_slow=TSLOW[KS.index(k)],
                                         s_a=round(ra, 6), s_b=round(rb, 6), dh=round(abs(ra - rb), 6)))
    cliff_l1.sort(key=lambda e: -e["dh"])
    cliff_d1.sort(key=lambda e: -e["dh"])

    top20 = []
    for rank, (i, k, s, r) in enumerate(rows[:20], 1):
        d1 = D1S[i]
        top20.append(dict(rank=rank, d1=d1, X=round(d1 - 5.0, 4), k=k,
                          t_slow=TSLOW[KS.index(k)], l1=round(k * 1e-4 * V0, 6),
                          slow=s, r=round(r, 6), cards=_card_lines(d1, TSLOW[KS.index(k)], s)))

    out = dict(
        grid=dict(d1_lo=D1_LO, d1_hi=D1_HI, d1_step=0.0001, d1_n=D1_N,
                  k_lo=K_LO, k_hi=K_HI, k_n=len(KS),
                  l1_lo_m=L1S[0], l1_hi_m=L1S[-1], l1_step_mm=round(L1_STEP * 1000, 6),
                  t_slow_lo=TSLOW[0], t_slow_hi=TSLOW[-1], slow=[0, 1], n=n),
        wall_s=round(t_wall_s, 3), nproc=nproc,
        max=dict(d1=D1S[bi], X=round(D1S[bi] - 5.0, 4), k=bk, t_slow=TSLOW[KS.index(bk)],
                 l1=round(bk * 1e-4 * V0, 6), slow=bs, r=round(br, 6),
                 cards=_card_lines(D1S[bi], TSLOW[KS.index(bk)], bs)),
        top20=top20, col_max=col_max, col_check=col_check,
        col_check_all_ok=all(c["ok"] for c in col_check),
        cliff_l1_n=len(cliff_l1), cliff_l1=cliff_l1,
        cliff_d1_n=len(cliff_d1), cliff_d1=cliff_d1,
    )
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"\n=== 结果 (n={n}) ===", flush=True)
    print(f"max = {br:.6f} @ d1={D1S[bi]:.4f} (X={D1S[bi]-5.0:.4f}) "
          f"t_slow={TSLOW[KS.index(bk)]:.4f} (L1={bk*1e-4*V0:.6f}) slow={bs}", flush=True)
    print(f"col_check: {col_check}  all_ok={out['col_check_all_ok']}", flush=True)
    print(f"cliff: L1向 {len(cliff_l1)} 条, d1向 {len(cliff_d1)} 条", flush=True)
    if cliff_l1:
        print(f"  L1向最大步高 {cliff_l1[0]['dh']:.3f} m", flush=True)
    if cliff_d1:
        print(f"  d1向最大步高 {cliff_d1[0]['dh']:.3f} m", flush=True)
    print("=== top-5 ===", flush=True)
    for t in top20[:5]:
        print(f"  #{t['rank']} d1={t['d1']:.4f} X={t['X']:.4f} t_slow={t['t_slow']:.4f} "
              f"L1={t['l1']:.6f} slow={t['slow']} r={t['r']:.6f}", flush=True)
    print(f"结果已写入 {OUT_JSON}", flush=True)


def main():
    import multiprocessing as mp
    nproc = 8
    if "--nproc" in sys.argv:
        nproc = int(sys.argv[sys.argv.index("--nproc") + 1])

    done = load_done()
    total = D1_N * len(KS) * 2
    remaining = [(i, k, s) for i in range(D1_N) for k in KS for s in (0, 1)
                 if (i, k, s) not in done]
    print(f"total={total} done={len(done)} remaining={len(remaining)}", flush=True)

    t_enum = 0.0
    if remaining:
        t0 = time.perf_counter()
        with open(RESULTS, "a", encoding="utf-8") as fout:
            with mp.Pool(nproc, initializer=_init_worker) as pool:
                cnt = 0
                for res in pool.imap_unordered(_score, remaining, chunksize=1):
                    fout.write(json.dumps(res) + "\n")
                    cnt += 1
                    if cnt % 5000 == 0:
                        fout.flush()
                        print(f"  ... {len(done)+cnt}/{total} "
                              f"({100.0*(len(done)+cnt)/total:.1f}%)", flush=True)
            fout.flush()
        t_enum = time.perf_counter() - t0
        print(f"枚举 wall {t_enum:.1f}s for {len(remaining)} tasks", flush=True)
    else:
        print("全部已枚举, 直接聚合", flush=True)

    aggregate(t_enum, nproc)


if __name__ == "__main__":
    main()
