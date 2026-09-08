#!/usr/bin/env python3
"""
第一问 SAT 验证程序（n=10, k≤84）
证明：对于所有 1≤k≤84，E(10,k) = E(9,k)
使用 IDPool 统一管理变量，彻底消除变量编号冲突。
"""

from pysat.solvers import Solver
from pysat.card import CardEnc
from pysat.formula import IDPool
from itertools import combinations
import time, multiprocessing as mp, os, json
from math import comb

# 第一问穷举的 E(9,k) 表
E9 = [0] * 85
E9[1] = 7; E9[2] = 8; E9[3] = 9; E9[4] = 9; E9[5] = 10
E9[6] = 11; E9[7] = 11; E9[8] = 12; E9[9] = 12; E9[10] = 12
E9[11] = 14; E9[12] = 15; E9[13] = 15; E9[14] = 16; E9[15] = 16
E9[16] = 16; E9[17] = 17; E9[18] = 17; E9[19] = 17; E9[20] = 17
E9[21] = 18; E9[22] = 19; E9[23] = 19; E9[24] = 20; E9[25] = 20
E9[26] = 20; E9[27] = 21; E9[28] = 21; E9[29] = 21; E9[30] = 21
E9[31] = 22; E9[32] = 22; E9[33] = 22; E9[34] = 22; E9[35] = 22
E9[36] = 24; E9[37] = 25; E9[38] = 25; E9[39] = 26; E9[40] = 26
E9[41] = 26; E9[42] = 27; E9[43] = 27; E9[44] = 27; E9[45] = 27
E9[46] = 28; E9[47] = 28; E9[48] = 28; E9[49] = 28; E9[50] = 28
E9[51] = 29; E9[52] = 29; E9[53] = 29; E9[54] = 29; E9[55] = 29
E9[56] = 29; E9[57] = 30; E9[58] = 31; E9[59] = 31; E9[60] = 32
E9[61] = 32; E9[62] = 32; E9[63] = 33; E9[64] = 33; E9[65] = 33
E9[66] = 33; E9[67] = 34; E9[68] = 34; E9[69] = 34; E9[70] = 34
E9[71] = 34; E9[72] = 35; E9[73] = 35; E9[74] = 35; E9[75] = 35
E9[76] = 35; E9[77] = 35; E9[78] = 36; E9[79] = 36; E9[80] = 36
E9[81] = 36; E9[82] = 36; E9[83] = 36; E9[84] = 36

H0 = [(0,1),(0,2),(0,3),(0,4),(5,6),(7,8)]
H0_set = {tuple(sorted(e)) for e in H0}

CACHE_FILE = "sat_cache_10_v2.json"

def max_triangles(e):
    """Kruskal–Katona 上界：给定总边数 e，无限制图的最大三角形数"""
    if e < 6: return 0
    a1 = 0
    while comb(a1 + 1, 2) <= e: a1 += 1
    rem = e - comb(a1, 2)
    if rem == 0: return comb(a1, 3)
    else: return comb(a1, 3) + comb(rem, 2)

def build_and_solve(k, target_edges):
    """使用 IDPool 统一管理变量，构建 SAT 实例并求解"""
    n = 10
    vpool = IDPool()
    solver = Solver()

    edges = list(combinations(range(n), 2))

    # 可选边变量
    edge_var = {}
    for e in edges:
        if e not in H0_set:
            edge_var[e] = vpool.id(("edge", e))

    extra = target_edges - 6
    if extra < 0 or extra > len(edge_var):
        solver.delete()
        return False

    # 边数精确约束（使用 vpool 避免变量冲突）
    if extra == len(edge_var):
        for v in edge_var.values():
            solver.add_clause([v])
    else:
        cnf_atmost = CardEnc.atmost(lits=list(edge_var.values()), bound=extra, vpool=vpool)
        cnf_atleast = CardEnc.atleast(lits=list(edge_var.values()), bound=extra, vpool=vpool)
        solver.append_formula(cnf_atmost.clauses)
        solver.append_formula(cnf_atleast.clauses)

    def optional_edge_var(u, v):
        e = tuple(sorted((u, v)))
        if e in H0_set:
            return None
        return edge_var[e]

    tri_indicators = []
    for x, y, z in combinations(range(n), 3):
        opt_vars = [v for v in (
            optional_edge_var(x, y),
            optional_edge_var(x, z),
            optional_edge_var(y, z)
        ) if v is not None]

        if not opt_vars:
            continue

        # 使用 vpool 创建三角形指示变量
        act = vpool.id(("tri", x, y, z))
        for v in opt_vars:
            solver.add_clause([-act, v])
        solver.add_clause([act] + [-v for v in opt_vars])
        tri_indicators.append(act)

    if k > len(tri_indicators):
        solver.delete()
        return False

    # 三角形数至少为 k（使用 vpool 避免变量冲突）
    if k == len(tri_indicators):
        for act in tri_indicators:
            solver.add_clause([act])
    else:
        cnf_tri = CardEnc.atleast(lits=tri_indicators, bound=k, vpool=vpool)
        solver.append_formula(cnf_tri.clauses)

    sat = solver.solve()
    solver.delete()
    return sat

def solve_k(k):
    E9k = E9[k]
    for e in range(6, E9k):
        if max_triangles(e) < k:   # 理论上界排除
            continue
        if build_and_solve(k, e):
            return (k, e, True)
    return (k, None, False)

def main():
    tasks = list(range(1, 85))
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)

    new_tasks = [k for k in tasks if str(k) not in cache]
    print(f"待验证: {len(new_tasks)} 个 k 值")

    with mp.Pool(processes=8) as pool:
        for k, e, found in pool.imap_unordered(solve_k, new_tasks):
            if found:
                print(f"❌ 发现反例: k={k}, e={e}")
                return
            else:
                print(f"✔ k={k:2d}: 验证通过")
                cache[str(k)] = "PASS"
                with open(CACHE_FILE, 'w') as f:
                    json.dump(cache, f)

    print("所有 k 值验证通过。结论：E(10,k) = E(9,k) 对所有 1≤k≤84 成立。")

if __name__ == "__main__":
    main()
