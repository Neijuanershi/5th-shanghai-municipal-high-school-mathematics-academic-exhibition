#!/usr/bin/env python3
"""
第一问 n=9 完备枚举程序（修正版）
输出 E(9,k) (k=1..84)
使用 Numba 加速，8进程并行
"""

import numpy as np
from math import comb
import time, multiprocessing as mp, json, os

try:
    from numba import njit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    print("Numba 未安装，将使用纯 Python 回退（较慢）")
    def njit(func):
        return func

# 强制子图 H0
H0 = [(0,1),(0,2),(0,3),(0,4),(5,6),(7,8)]
N = 9
EDGES = [(i,j) for i in range(N) for j in range(i+1,N)]
EDGE_IDX = {e:idx for idx,e in enumerate(EDGES)}
M = len(EDGES)          # 36
H0_IDX = frozenset(EDGE_IDX[e] for e in H0)
H0_MASK = sum(1<<e for e in H0_IDX)
N_H0 = 6

# 预计算三角形的三个边编号及其位掩码
TRI_EDGES = []
TRI_MASKS = []
for a in range(N):
    for b in range(a+1,N):
        for c in range(b+1,N):
            e1 = EDGE_IDX[(a,b)]; e2 = EDGE_IDX[(a,c)]; e3 = EDGE_IDX[(b,c)]
            TRI_EDGES.append((e1, e2, e3))
            TRI_MASKS.append((1<<e1)|(1<<e2)|(1<<e3))

VARIABLE_INDICES = [i for i in range(M) if i not in H0_IDX]   # 30 条可选边

def count_triangles(mask):
    return sum(1 for tm in TRI_MASKS if (mask & tm) == tm)

# Numba 核心搜索
@njit
def numba_dfs(start_pos, selected, cur_mask, cur_tri, tri_state,
              rem_indices, need, k, tri_ptr, tri_data):
    if cur_tri >= k:
        return True, cur_mask, cur_tri
    if selected == need:
        return False, 0, 0
    for i in range(start_pos, len(rem_indices)):
        e = rem_indices[i]
        new_mask = cur_mask | (1<<e)
        new_tri = cur_tri
        new_state = tri_state.copy()
        s, eend = tri_ptr[e], tri_ptr[e+1]
        for idx in range(s, eend):
            tid = tri_data[idx]
            new_state[tid] += 1
            if new_state[tid] == 3:
                new_tri += 1
        found, fm, ft = numba_dfs(i+1, selected+1, new_mask, new_tri,
                                  new_state, rem_indices, need, k,
                                  tri_ptr, tri_data)
        if found:
            return True, fm, ft
    return False, 0, 0

def search_worker(args):
    prefix, rem, need, k, graph = args
    if not isinstance(rem, np.ndarray):
        rem = np.array(rem, dtype=np.int64)
    mask = graph['H0_MASK']
    tri_state = np.zeros(graph['TRI_COUNT'], dtype=np.int64)
    cur_tri = 0
    for e in range(graph['M']):
        if (mask>>e) & 1:
            for idx in range(graph['TRI_PTR'][e], graph['TRI_PTR'][e+1]):
                tid = graph['TRI_DATA'][idx]
                tri_state[tid] += 1
                if tri_state[tid]==3:
                    cur_tri += 1
    for e in prefix:
        mask |= (1<<e)
        for idx in range(graph['TRI_PTR'][e], graph['TRI_PTR'][e+1]):
            tid = graph['TRI_DATA'][idx]
            tri_state[tid] += 1
            if tri_state[tid]==3:
                cur_tri += 1
    if cur_tri >= k:
        return True, mask, cur_tri
    ok, fm, ft = numba_dfs(0, 0, mask, cur_tri, tri_state, rem, need, k,
                           graph['TRI_PTR'], graph['TRI_DATA'])
    return (True, fm, ft) if ok else (False, 0, 0)

def bruteforce_one(k, graph, max_c=None, start_c=0, verbose=True, pool=None):
    if graph['H0_TRI'] >= k:
        return graph['N_H0'], graph['H0_TRI'], graph['H0_MASK']
    VA = graph['VAR_ARRAY']
    if max_c is None:
        max_c = len(VA)
    start_c = max(start_c, 1)
    for c in range(start_c, max_c+1):
        total = comb(len(VA), c)
        if verbose:
            print(f"  k={k}: 尝试 c={c} 条新边 (共 {total:,} 种组合) ...", end=" ", flush=True)
        firsts = VA[:len(VA)-c+1]
        tasks = [([e], VA[np.where(VA==e)[0][0]+1:], c-1, k, graph) for e in firsts]
        results = pool.map(search_worker, tasks)
        for ok, mask, t in results:
            if ok:
                if verbose:
                    print("✓")
                return graph['N_H0'] + c, t, mask
        if verbose:
            print("无解")
    return None, None, None

def main():
    # 构建图结构（边到三角形的映射）
    edge_to_tris = [[] for _ in range(M)]
    for ti, tri_edges in enumerate(TRI_EDGES):
        for edge_idx in tri_edges:
            edge_to_tris[edge_idx].append(ti)
    ptr, data = [0], []
    for e in range(M):
        for t in edge_to_tris[e]: data.append(t)
        ptr.append(len(data))
    graph = {
        'N': N, 'M': M, 'N_H0': N_H0, 'H0_MASK': H0_MASK,
        'H0_TRI': count_triangles(H0_MASK),
        'VAR_ARRAY': np.array(VARIABLE_INDICES, dtype=np.int64),
        'TRI_COUNT': len(TRI_MASKS),
        'TRI_PTR': np.array(ptr, dtype=np.int64),
        'TRI_DATA': np.array(data, dtype=np.int64),
        'EDGES': EDGES
    }

    pool = mp.Pool(processes=min(mp.cpu_count(), 8))
    print(f"开始 n=9 枚举 (k=1..84)")
    results = {}
    for k in range(1, 85):
        e, t, mask = bruteforce_one(k, graph, max_c=30, start_c=0,
                                    verbose=False, pool=pool)
        results[k] = {'E': e, 'T': t, 'mask': int(mask) if mask else 0}
        print(f"k={k:2d}: E={e:2d}, T={t:2d}")
    pool.close(); pool.join()

    # 输出表格
    print("\nE(9,k) 表:")
    for k in range(1,85):
        print(f"k={k:2d}: E={results[k]['E']:2d}")

if __name__ == "__main__":
    main()
