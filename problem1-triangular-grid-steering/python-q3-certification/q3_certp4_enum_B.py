# -*- coding: utf-8 -*-
"""q3_certp4_enum_B.py — Q3 认证冲刺 右半区 B 全枚举.

网格 B:
  Δ1 ∈ [9.8500, 9.9000] 步 0.0001° (501 值)
  t_slow 官方 0.0001 s 网格 = {3.7924 + k*0.0001 : k ∈ [902,997]} (96 值)
      realized L1 = k*0.0001 * V0 ∈ [10.5007, 11.6066]
  slow ∈ {0, 1}
  共 501 * 96 * 2 = 96192 个官方格式方案.

评分器: 复用 q3_certp3_core.terminal_score (与 cxk.simulate 对终局段逐位等价).
对照: 6 个已知锚点 + 200 组随机样本 vs 完整 cxk.simulate (内存内构造, 不写盘).

只新建本文件与 q3_certp4_enum_B.json / report_q3_certp4_B.md, 不改动既有文件.
用法: python q3_certp4_enum_B.py [--nproc N] [--selftest] [--skip-verify]
"""
import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cxk
import q3_certp3_core as core
import q3_certp4_fast

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "q3_certp4_enum_B.json")
VERIFY_JSON = os.path.join(HERE, "q3_certp4_verify_B.json")

# ---- 网格 ----
D1_MIN, D1_MAX, D1_STEP = 9.8500, 9.9000, 0.0001
D1S = [round(D1_MIN + D1_STEP * k, 4) for k in range(int(round((D1_MAX - D1_MIN) / D1_STEP)) + 1)]
K0, K1 = 902, 997            # t_slow = TB + k*0.0001, k ∈ [K0, K1] (96 值)
KS = list(range(K0, K1 + 1))
V0 = core.V0
TB = core.TB


def t_slow_of_k(k):
    return TB + k * 1e-4


def l1_of_k(k):
    return k * 1e-4 * V0


# ---- 内存内完整 cxk.simulate (不写盘, 逐位等价 core.full_simulate) ----
def full_simulate_mem(d1, L1, slow, lines=None):
    if lines is None:
        lines = core.read_rec_lines()
    ts = round(core.t_slow_of(L1) / 1e-4) * 1e-4
    nl = lines[:99]
    nl.append("R %.4f %.4f" % (core.TB, min(5.0, d1)))
    nl.append("R %.4f %.4f" % (core.TB, d1 - min(5.0, d1)))
    if slow:
        nl.append("- %.4f" % ts)
    else:
        nl.append("R %.4f 0.0000" % ts)
    # 与 cxk.read_plan 相同的解析 (strip + 过滤空行 + 逐行解析)
    ver = nl[0].lstrip('\ufeff')
    heading = float(nl[1])
    events = []
    for ln in nl[2:]:
        toks = ln.split()
        if toks[0] == "+":
            events.append(("spd", float(toks[1]), 1.25))
        elif toks[0] == "-":
            events.append(("spd", float(toks[1]), 0.8))
        elif toks[0] == "R":
            events.append(("turn", float(toks[1]), float(toks[2])))
        else:
            raise ValueError("无法解析的行: %r" % ln)
    res = cxk.simulate(heading, events)
    return res["r"]


# ---- 验证: 锚点 + 随机 vs 完整 cxk.simulate ----
ANCHORS = [
    (9.8305, 3.8874, 447.9733),
    (9.8310, 3.8874, 447.9725),
    (9.8350, 3.8874, 447.9657),
    (9.8500, 3.8871, 447.9601),
    (9.8304, 3.8874, 439.4987),
    (9.8328, 3.8873, 440.4239),
]


def run_verify():
    print("=" * 70)
    print("验证: terminal_score vs 完整 cxk.simulate (内存内, 不写盘)")
    print("=" * 70)
    worst = 0.0
    worst_info = None
    rows = []
    # 6 个锚点 (均 slow=1, 与纪录一致)
    for d1, ts, expect in ANCHORS:
        L1 = (ts - TB) * V0
        fast = core.terminal_score(d1, L1, 1)
        full = full_simulate_mem(d1, L1, 1)
        diff = abs(fast - full)
        rows.append(("anchor", d1, ts, 1, fast, full, expect))
        if diff > worst:
            worst = diff
            worst_info = ("anchor", d1, ts, 1, fast, full, expect)
        print("anchor d1=%.4f ts=%.4f slow=1: fast=%.6f full=%.6f |Δ|=%.2e "
              "expect=%.4f" % (d1, ts, fast, full, diff, expect))
    # 200 随机样本 (覆盖网格 B 及其邻域, slow 0/1)
    random.seed(20240617)
    for i in range(200):
        d1 = round(random.uniform(9.80, 9.95), 4)   # 4 位小数, 与官方角度网格一致
        k = random.randint(898, 1000)
        ts = t_slow_of_k(k)
        L1 = l1_of_k(k)
        slow = random.choice([0, 1])
        fast = core.terminal_score(d1, L1, slow)
        full = full_simulate_mem(d1, L1, slow)
        diff = abs(fast - full)
        rows.append(("rand", d1, ts, slow, fast, full, None))
        if diff > worst:
            worst = diff
            worst_info = ("rand", d1, ts, slow, fast, full, None)
    print("-" * 70)
    print("锚点 fast vs 已知值:")
    for tag, d1, ts, slow, fast, full, expect in rows[:6]:
        if expect is not None:
            print("  d1=%.4f ts=%.4f: fast=%.6f vs 已知=%.4f  Δ=%.2e"
                  % (d1, ts, fast, expect, abs(fast - expect)))
    print("-" * 70)
    print("最差 |fast - full| = %.3e @ %s" % (worst, worst_info))
    n_bad = sum(1 for r in rows if abs(r[4] - r[5]) > 1e-9)
    print("|fast-full| > 1e-9 的样本数 = %d / %d" % (n_bad, len(rows)))
    ok = worst <= 1e-11
    print("结论: " + ("通过 (最差偏差 %.3e m ≤ 1e-11, 即 1e-12 量级, 与 cxk.simulate 等价)" % worst
                    if ok else "未通过, 需排查"))
    # 保存验证摘要, 供完整枚举 --skip-verify 复用
    try:
        summary = dict(
            ok=ok, worst=worst,
            n_total=len(rows), n_bad=sum(1 for r in rows if abs(r[4] - r[5]) > 1e-9),
            anchors=[dict(d1=r[1], t_slow=r[2], slow=r[3], fast=r[4], full=r[5], expect=r[6])
                     for r in rows[:6]],
        )
        with open(VERIFY_JSON, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False)
        print("验证摘要已写入 %s" % VERIFY_JSON)
    except Exception as e:
        print("(验证摘要写盘失败: %s)" % e)
    return ok, worst, rows


# ---- 并行枚举 ----
_ST = None


def _init_worker():
    global _ST
    q3_certp4_fast.patch()   # 位等价快速 min_dist_rot (已核 0/200000 逐位相同)
    _ST = core.state()


def _worker(task):
    d1, k, l1, slow = task
    r = core.terminal_score(d1, l1, slow, _ST)
    return (d1, k, slow, r)


def make_tasks():
    tasks = []
    for d1 in D1S:
        for k in KS:
            l1 = l1_of_k(k)
            tasks.append((d1, k, l1, 0))
            tasks.append((d1, k, l1, 1))
    return tasks


def run(tasks, nproc):
    import multiprocessing as mp
    with mp.Pool(nproc, initializer=_init_worker) as pool:
        results = pool.map(_worker, tasks, chunksize=32)
    return results


# ---- 分析 ----
def analyze(results):
    # results: list of (d1, k, slow, score)
    best = max(results, key=lambda r: r[3])
    top20 = sorted(results, key=lambda r: -r[3])[:20]

    # 每列(固定 Δ1) max
    col_max = {}
    for d1, k, slow, score in results:
        if d1 not in col_max or score > col_max[d1][3]:
            col_max[d1] = (d1, k, slow, score)

    # 每列悬崖边: 相邻 k (同一 Δ1, 同一 slow) 分数差 > 1 m
    # 先按 (d1, slow, k) 建索引
    idx = {}
    for d1, k, slow, score in results:
        idx[(d1, slow, k)] = score
    cliff_edges = []
    for d1 in D1S:
        for slow in (0, 1):
            for k in KS[:-1]:
                k2 = k + 1
                s1 = idx[(d1, slow, k)]
                s2 = idx[(d1, slow, k2)]
                step = s2 - s1
                if abs(step) > 1.0:
                    cliff_edges.append(dict(
                        d1=round(d1, 4),
                        slow=slow,
                        k_left=k, k_right=k2,
                        t_slow_left=round(t_slow_of_k(k), 4),
                        t_slow_right=round(t_slow_of_k(k2), 4),
                        l1_left=round(l1_of_k(k), 6),
                        l1_right=round(l1_of_k(k2), 6),
                        score_left=round(s1, 6),
                        score_right=round(s2, 6),
                        step=round(step, 6),
                    ))
    return best, top20, col_max, cliff_edges


def fmt_result(r):
    d1, k, slow, score = r
    return dict(
        d1=round(d1, 4),
        X=round(d1 - 5.0, 4),
        k=k,
        t_slow=round(t_slow_of_k(k), 4),
        L1=round(l1_of_k(k), 6),
        slow=slow,
        score=round(score, 6),
    )


def card_lines(r):
    d1, k, slow, score = r
    X = round(d1 - 5.0, 4)
    ts = round(t_slow_of_k(k), 4)
    lines = ["R %.4f 5.0000" % TB, "R %.4f %.4f" % (TB, X)]
    if slow:
        lines.append("- %.4f" % ts)
    else:
        lines.append("R %.4f 0.0000" % ts)
    return lines


def main():
    args = sys.argv[1:]
    nproc = 8
    selftest = False
    skip_verify = False
    if "--nproc" in args:
        nproc = int(args[args.index("--nproc") + 1])
    if "--selftest" in args:
        selftest = True
    if "--skip-verify" in args:
        skip_verify = True
    verify_only = "--verify-only" in args

    q3_certp4_fast.patch()   # 主进程也启用位等价快速 min_dist_rot

    print("网格 B: Δ1∈[%.4f, %.4f] 步 %.4f (%d 值)" % (D1_MIN, D1_MAX, D1_STEP, len(D1S)))
    print("       t_slow = %.4f + k*0.0001, k∈[%d,%d] (%d 值)" % (TB, K0, K1, len(KS)))
    print("       realized L1 ∈ [%.6f, %.6f], slow∈{0,1}" % (l1_of_k(K0), l1_of_k(K1)))
    print("       方案数 = %d * %d * 2 = %d" % (len(D1S), len(KS), len(D1S) * len(KS) * 2))
    print("nproc = %d, selftest = %s" % (nproc, selftest))

    verify_ok, worst, verify_rows = (True, 0.0, [])
    if not skip_verify:
        verify_ok, worst, verify_rows = run_verify()
        if not verify_ok:
            print("!! 验证未通过, 终止.")
            sys.exit(3)
        if verify_only:
            print("\n[verify-only] 验证通过, 退出.")
            return
    else:
        # 复用先前 verify-only 保存的摘要
        try:
            with open(VERIFY_JSON, encoding="utf-8") as f:
                vs = json.load(f)
            verify_ok = bool(vs.get("ok", False))
            worst = float(vs.get("worst", 0.0))
            verify_rows = [("anchor", a["d1"], a["t_slow"], a["slow"], a["fast"], a["full"], a["expect"])
                           for a in vs.get("anchors", [])]
            print("[skip-verify] 已从 %s 加载验证摘要: ok=%s worst=%.3e n_bad=%s"
                  % (VERIFY_JSON, verify_ok, worst, vs.get("n_bad")))
            if not verify_ok:
                print("!! 复用摘要显示验证未通过, 终止.")
                sys.exit(3)
        except Exception as e:
            print("!! 无法加载验证摘要 (%s), 请先运行 --verify-only." % e)
            sys.exit(3)

    tasks = make_tasks()
    if selftest:
        tasks = tasks[:4096]
        print("[selftest] 只跑前 %d 个任务" % len(tasks))

    t0 = time.perf_counter()
    results = run(tasks, nproc)
    wall = time.perf_counter() - t0
    print("评估完成: %d 个方案, 墙钟 %.1f s (%.2f ms/方案/核心)"
          % (len(results), wall, wall / max(len(results), 1) * nproc * 1000))

    best, top20, col_max, cliff_edges = analyze(results)

    print("\n=== 全局最优 ===")
    b = fmt_result(best)
    print("max = %.6f @ Δ1=%.4f (X=%.4f), t_slow=%.4f (k=%d), L1=%.6f, slow=%d"
          % (b["score"], b["d1"], b["X"], b["t_slow"], b["k"], b["L1"], b["slow"]))

    print("\n=== top-20 ===")
    print("%2s %7s %7s %4s %9s %4s %9s" % ("#", "Δ1", "X", "k", "t_slow", "slow", "score"))
    for i, r in enumerate(top20):
        f = fmt_result(r)
        print("%2d %7.4f %7.4f %4d %9.4f %4d %9.4f"
              % (i + 1, f["d1"], f["X"], f["k"], f["t_slow"], f["slow"], f["score"]))

    print("\n=== top-20 卡片行 (第 100/101/102 行) ===")
    for i, r in enumerate(top20):
        f = fmt_result(r)
        cl = card_lines(r)
        print("#%02d (Δ1=%.4f X=%.4f t_slow=%.4f slow=%d score=%.4f):"
              % (i + 1, f["d1"], f["X"], f["t_slow"], f["slow"], f["score"]))
        print("   " + " | ".join(cl))

    print("\n=== 每列(固定 Δ1) max ===")
    for d1 in D1S:
        c = col_max[d1]
        print("Δ1=%.4f -> max %.6f @ k=%d (t_slow=%.4f, L1=%.6f, slow=%d)"
              % (d1, c[3], c[1], round(t_slow_of_k(c[1]), 4), round(l1_of_k(c[1]), 6), c[2]))

    print("\n=== 悬崖边 (相邻 k 分数差 >1 m) ===")
    print("共 %d 条" % len(cliff_edges))
    for e in cliff_edges[:200]:
        print("Δ1=%.4f slow=%d k %d->%d (t %.4f->%.4f, L1 %.4f->%.4f): "
              "%.4f -> %.4f (步高 %.4f)"
              % (e["d1"], e["slow"], e["k_left"], e["k_right"],
                 e["t_slow_left"], e["t_slow_right"], e["l1_left"], e["l1_right"],
                 e["score_left"], e["score_right"], e["step"]))

    # 已知锚点核验: Δ1=9.85 且 t_slow=3.8871 (k=947) 必须 = 447.9601
    k_anchor = 947
    anchor_hit = [r for r in results if abs(r[0] - 9.85) < 1e-9 and r[1] == k_anchor and r[2] == 1]
    anchor_ok = False
    if anchor_hit:
        a = anchor_hit[0]
        anchor_ok = abs(a[3] - 447.9601) < 1e-4
        print("\n=== 已知锚点核验 ===")
        print("Δ1=9.85, t_slow=3.8871 (k=%d, slow=1): 本网格得分 = %.6f, 已知 = 447.9601, 相符=%s"
              % (k_anchor, a[3], anchor_ok))
    else:
        print("\n!! 网格未包含锚点 (Δ1=9.85, k=947, slow=1), 需排查!")
    if not anchor_ok:
        print("!! 锚点不符, 停止. (不写 JSON)")
        sys.exit(4)

    if not selftest:
        data = dict(
            grid=dict(
                d1_min=D1_MIN, d1_max=D1_MAX, d1_step=D1_STEP, n_d1=len(D1S),
                k0=K0, k1=K1, n_k=len(KS), t_slow_step=1e-4,
                t_slow_min=round(t_slow_of_k(K0), 4), t_slow_max=round(t_slow_of_k(K1), 4),
                l1_min=round(l1_of_k(K0), 6), l1_max=round(l1_of_k(K1), 6),
                slow_values=[0, 1],
            ),
            n=len(results),
            wall_s=round(wall, 6),
            verify=dict(
                ok=verify_ok,
                worst_fast_vs_full=worst,
                anchors=[dict(d1=r[1], t_slow=r[2], slow=r[3], fast=r[4], full=r[5], expect=r[6])
                         for r in verify_rows[:6]],
            ),
            best=fmt_result(best),
            top20=[fmt_result(r) for r in top20],
            top20_card_lines=[card_lines(r) for r in top20],
            col_max=[dict(d1=round(d1, 4), k=col_max[d1][1],
                          t_slow=round(t_slow_of_k(col_max[d1][1]), 4),
                          l1=round(l1_of_k(col_max[d1][1]), 6),
                          slow=col_max[d1][2], score=round(col_max[d1][3], 6))
                     for d1 in D1S],
            cliff_edges=cliff_edges,
            n_cliff_edges=len(cliff_edges),
            anchor_check=dict(
                d1=9.85, k=k_anchor, t_slow=3.8871, slow=1,
                score=round(anchor_hit[0][3], 6) if anchor_hit else None,
                expect=447.9601, match=anchor_ok,
            ),
        )
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print("\n结果已写入 %s" % OUT_JSON)


if __name__ == "__main__":
    main()
