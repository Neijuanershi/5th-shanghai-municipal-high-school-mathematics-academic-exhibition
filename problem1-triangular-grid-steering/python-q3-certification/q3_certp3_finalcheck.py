# -*- coding: utf-8 -*-
"""q3_certp3_finalcheck.py — 终局核验: 舍入事实 + 细网格最优的 certify_plan 合法性。"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3_certp3_core as core
import cxk
import q3_cert_merge_sa3 as cert

HERE = os.path.dirname(os.path.abspath(__file__))
st = core.state()

print("=== 舍入事实核验 ===")
# 连续 argmax (9.832764°, 11.052704m) 的官方格式舍入
# Δ1 -> 9.8328 (4位小数); L1=11.052704 -> t_slow=3.887342 -> 3.8873 -> realized L1=11.0478
r = core.terminal_score(9.8328, 11.0478, 1, st)
print(f"  舍入 (Δ1=9.8328, L1=11.0478, slow=1) → {r:.4f}  (已知: 440.42)")
r = core.terminal_score(9.8328, 11.0595, 1, st)
print(f"  对照 (Δ1=9.8328, L1=11.0595, slow=1) → {r:.4f}")
r = core.terminal_score(9.831, 11.0595, 1, st)
print(f"  细网格最优 (Δ1=9.831, L1=11.0595, slow=1) → {r:.4f}")
r = core.terminal_score(9.835, 11.06, 1, st)
print(f"  已知最优 (Δ1=9.835, L1=11.06, slow=1) → {r:.4f}  (已知 447.9657)")

print("\n=== certify_plan 合法性核验 ===")
for tag, d1, L1 in [("细网格最优", 9.831, 11.0595),
                    ("已知最优", 9.835, 11.06),
                    ("纪录", 9.88, 11.05)]:
    tmp = os.path.join(HERE, f"q3_certp3_fc_{tag}.txt")
    core.build_plan(d1, L1, 1, tmp)
    c = cert.certify_plan(tmp)
    os.remove(tmp)
    ray = c["ray"]
    if "error" in ray:
        rd = f"异常 {ray.get('error')}"
    else:
        rd = f"r_lo={ray['r_lo']:.4f} r_hi={ray['r_hi']:.4f} width={ray['r_hi']-ray['r_lo']:.4f}"
    finite_ok = (not c["any_collision"]) and (c["worst_cert"] > 9.0)
    print(f"  [{tag}] (Δ1={d1}, L1={L1}, slow=1): cxk={c['sim']['r']:.4f} | "
          f"有限段 {'PASS' if finite_ok else 'FAIL'} (min cert={c['worst_cert']:.4f}) | 射线 {rd}")
