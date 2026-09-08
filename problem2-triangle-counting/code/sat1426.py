#!/usr/bin/env python3
"""
第二问 SAT 验证程序（最终版）
定理 2.1 的计算机辅助验证。
运行前请删除旧缓存文件 sat_cache_q2_final.json。
"""

from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from itertools import combinations
import time, multiprocessing as mp, os, json
from math import comb

# ---------- 配置 ----------
CACHE_FILE = "sat_cache_q2_final.json"
CACHE_VERSION = "q2-final-20250722"
SOLVER_NAME = "cadical195"          # 正式运行使用 CaDiCaL 1.9.5
TRI_ENCODING = EncType.cardnetwrk   # 三角形基数编码
EDGE_ENCODING = EncType.seqcounter  # 边数基数编码
TRI_ENC_NAME = "cardnetwrk"
EDGE_ENC_NAME = "seqcounter"
# --------------------------

E9 = [0]*85
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

def make_solver():
    return Solver(name=SOLVER_NAME)

def verify_witness(k, m, chosen_edges):
    n = 9 + m
    edge_set = set(H0_set) | chosen_edges
    assert len(edge_set) < E9[k], f"边数 {len(edge_set)} 不小于 E9[{k}]={E9[k]}"
    tri = 0
    tri_by_vert = [0]*n
    for x, y, z in combinations(range(n), 3):
        if ((x,y) in edge_set or (y,x) in edge_set) and \
           ((x,z) in edge_set or (z,x) in edge_set) and \
           ((y,z) in edge_set or (z,y) in edge_set):
            tri += 1
            tri_by_vert[x] += 1; tri_by_vert[y] += 1; tri_by_vert[z] += 1
    assert tri >= k, f"三角形数 {tri} < k={k}"
    for u in range(9, n):
        assert tri_by_vert[u] >= 1, f"自由点 {u} 不在任何三角形中"
    return tri

def build_and_solve(k, m):
    n = 9 + m
    vpool = IDPool()
    solver = make_solver()
    edges = [(i,j) for i in range(n) for j in range(i+1, n)]
    edge_var = {}
    for e in edges:
        if e not in H0_set:
            edge_var[e] = vpool.id(("edge", e))
    all_vars = list(edge_var.values())
    max_extra = E9[k] - 7
    if max_extra < 0:
        solver.delete()
        return False, None
    cnf_edges = CardEnc.atmost(lits=all_vars, bound=max_extra,
                               vpool=vpool, encoding=EDGE_ENCODING)
    solver.append_formula(cnf_edges.clauses)
    free_tri_acts = {u: [] for u in range(9, n)}
    def edge_exists(ed):
        if ed in H0_set: return None
        return edge_var[ed]
    tri_inds = []
    for x, y, z in combinations(range(n), 3):
        e1 = edge_exists(tuple(sorted((x,y))))
        e2 = edge_exists(tuple(sorted((x,z))))
        e3 = edge_exists(tuple(sorted((y,z))))
        opt_vars = [v for v in (e1,e2,e3) if v is not None]
        if not opt_vars: continue
        act = vpool.id(("tri", x, y, z))
        for v in opt_vars: solver.add_clause([-act, v])
        solver.add_clause([act] + [-v for v in opt_vars])
        tri_inds.append(act)
        for u in (x,y,z):
            if u >= 9: free_tri_acts[u].append(act)
    if k > len(tri_inds):
        solver.delete()
        return False, None
    if k == len(tri_inds):
        for act in tri_inds: solver.add_clause([act])
    else:
        cnf_tri = CardEnc.atleast(lits=tri_inds, bound=k,
                                  vpool=vpool, encoding=TRI_ENCODING)
        solver.append_formula(cnf_tri.clauses)
    for u in range(9, n):
        assert free_tri_acts[u], f"自由点 {u} 无候选三角形"
        solver.add_clause(free_tri_acts[u])
    sat = solver.solve()
    witness = None
    if sat:
        model = {v for v in solver.get_model() if v > 0}
        witness = {e for e, var in edge_var.items() if var in model}
    solver.delete()
    return sat, witness

def solve_task(args):
    k, m = args
    sat, witness = build_and_solve(k, m)
    if sat:
        verify_witness(k, m, witness)
        return (k, m, True, witness)
    return (k, m, False, None)

def main():
    tasks = []
    for k in range(1, 85):
        max_m = E9[k] - 7
        for m in range(2, max_m+1):
            tasks.append((k, m))
    assert len(tasks) == 1426, f"任务总数应为 1426，实际 {len(tasks)}"
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        expected_meta = {
            "version": CACHE_VERSION,
            "solver": SOLVER_NAME,
            "edge_encoding": EDGE_ENC_NAME,
            "tri_encoding": TRI_ENC_NAME,
            "expected_tasks": 1426
        }
        if cache.get("meta") != expected_meta:
            print("缓存元数据不匹配，忽略旧缓存")
            cache = {}
    if "results" not in cache:
        cache["results"] = {}
    cache["meta"] = {
        "version": CACHE_VERSION,
        "solver": SOLVER_NAME,
        "edge_encoding": EDGE_ENC_NAME,
        "tri_encoding": TRI_ENC_NAME,
        "expected_tasks": 1426
    }
    new_tasks = [(k,m) for (k,m) in tasks
                 if cache["results"].get(f"{k}_{m}") != "PASS"]
    print(f"总任务数: {len(tasks)}, 待完成: {len(new_tasks)}")
    if not new_tasks:
        expected_keys = {f"{k}_{m}" for k, m in tasks}
        passed_keys = {key for key, value in cache["results"].items() if value == "PASS"}
        assert expected_keys <= passed_keys, "缓存缺少预期 PASS 任务"
        print("缓存中的全部 1426 个预期实例均为 PASS。")
        return
    PROCESSES = 1
    with mp.Pool(processes=PROCESSES) as pool:
        for k, m, sat, witness in pool.imap_unordered(solve_task, new_tasks):
            if sat:
                result = {
                    "k": k, "m": m, "n": 9+m,
                    "forced_edges": sorted(H0_set),
                    "chosen_edges": sorted(witness)
                }
                with open("counterexample.json", "w") as f:
                    json.dump(result, f, indent=2)
                print(f"❌ 发现并保存反例: k={k}, m={m}")
                pool.terminate()
                pool.join()
                return
            else:
                print(f"✔ k={k:2d}, m={m:2d}: UNSAT")
                cache["results"][f"{k}_{m}"] = "PASS"
                temp_file = CACHE_FILE + ".tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_file, CACHE_FILE)
    assert all(cache["results"].get(f"{k}_{m}") == "PASS" for k,m in tasks), \
           "任务未完全通过"
    print("所有 1426 个实例均为 UNSAT。命题 2.1 已通过计算机辅助验证。")

if __name__ == "__main__":
    main()
