#!/usr/bin/env python3
"""
第四问：连通且三角形边不交的最少边数 F(n,k) 精确求解器
用法：直接运行，按提示输入 n,k（逗号分隔），例如 9,5 或 9,5,600
依赖：ortools>=9.0
"""

import sys
from collections import deque
from itertools import combinations
from ortools.sat.python import cp_model

# 强制子图 H0（全部升序排列）
FORCED_EDGES = [(0, 1), (0, 2), (0, 3), (0, 4), (5, 6), (7, 8)]

def verify_solution(n, k, edges):
    """独立验证边集是否满足全部条件"""
    # 统一边为升序
    def norm(e):
        return (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
    edges = [norm(e) for e in edges]
    edge_set = set(edges)

    # 1. 强制边检查
    for u, v in FORCED_EDGES:
        if (u, v) not in edge_set:
            return False, f"强制边 ({u},{v}) 缺失"

    # 2. 连通性检查（BFS）
    adj = [[] for _ in range(n)]
    for u, v in edge_set:
        adj[u].append(v)
        adj[v].append(u)
    visited = [False] * n
    queue = deque([0])
    visited[0] = True
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                queue.append(v)
    if not all(visited):
        unvisited = [i for i, vis in enumerate(visited) if not vis]
        return False, f"图不连通，未访问顶点: {unvisited}"

    # 3. 三角形边不交检查 & 统计三角形数
    edge_triangle_count = {e: 0 for e in edge_set}
    triangle_count = 0
    for a, b, c in combinations(range(n), 3):
        if (a, b) in edge_set and (a, c) in edge_set and (b, c) in edge_set:
            triangle_count += 1
            edge_triangle_count[(a, b)] += 1
            edge_triangle_count[(a, c)] += 1
            edge_triangle_count[(b, c)] += 1
    for e, cnt in edge_triangle_count.items():
        if cnt > 1:
            return False, f"边 {e} 被 {cnt} 个三角形共享，违反边不交"

    # 4. 三角形数检查
    if triangle_count < k:
        return False, f"三角形数 {triangle_count} < k={k}"

    return True, f"验证通过：边数={len(edge_set)}, 三角形数={triangle_count}, 连通, 强制边完整, 边不交"

def solve_F(n, k, time_limit=300):
    """
    求解 F(n,k)。返回 (status, edge_count, edges)
    status: 'OPTIMAL', 'FEASIBLE', 'INFEASIBLE', 'UNKNOWN'
    """
    if n < 9:
        raise ValueError("n 必须 >= 9")
    if k <= 0:
        raise ValueError("k 必须 >= 1")

    # 最大边不交三角形数上界（考虑 n≡5 mod 6 的修正）
    # 当 n ≡ 1,3 (mod 6) 时上界为 floor(n(n-1)/6) 且可达（Steiner 三元系）；
    # 当 n ≡ 5 (mod 6) 时实际最大值为上界减 1；
    # 其余同余类上界仍为 floor(n(n-1)/6)，但并非全部可达。
    # 此处使用保守上界仅用于快速剪枝，不影响正确性（过高估计时求解器会完整判定）。
    def max_tri(n):
        base = (n * (n - 1)) // 6
        return base - 1 if n % 6 == 5 else base
    if k > max_tri(n):
        return "INFEASIBLE", None, None

    model = cp_model.CpModel()
    all_edges = list(combinations(range(n), 2))
    edge_vars = {e: model.NewBoolVar(f'e_{e[0]}_{e[1]}') for e in all_edges}

    # 强制边
    for u, v in FORCED_EDGES:
        model.Add(edge_vars[(u, v)] == 1)

    # 连通性：单商品流，容量 n-1
    flow_vars = {}
    for u, v in all_edges:
        flow_vars[(u, v)] = model.NewIntVar(0, n-1, f'f_{u}_{v}')
        flow_vars[(v, u)] = model.NewIntVar(0, n-1, f'f_{v}_{u}')
        model.Add(flow_vars[(u, v)] + flow_vars[(v, u)] <= (n-1) * edge_vars[(u, v)])

    for node in range(1, n):
        in_flows = []
        out_flows = []
        for neighbor in range(n):
            if neighbor == node:
                continue
            # 由于 flow_vars 包含所有方向，直接使用即可
            in_flows.append(flow_vars[(neighbor, node)])   # neighbor -> node
            out_flows.append(flow_vars[(node, neighbor)])  # node -> neighbor
        model.Add(sum(in_flows) - sum(out_flows) == 1)

    # 三角形变量
    triangle_vars = {}
    for a, b, c in combinations(range(n), 3):
        tri = model.NewBoolVar(f'tri_{a}_{b}_{c}')
        e_ab = edge_vars[(a, b)]
        e_ac = edge_vars[(a, c)]
        e_bc = edge_vars[(b, c)]
        model.Add(tri <= e_ab)
        model.Add(tri <= e_ac)
        model.Add(tri <= e_bc)
        model.Add(tri >= e_ab + e_ac + e_bc - 2)
        triangle_vars[(a, b, c)] = tri

    # 边不交：每条边至多属于一个三角形
    edge_to_tris = {e: [] for e in all_edges}
    for (a, b, c), tri in triangle_vars.items():
        edge_to_tris[(a, b)].append(tri)
        edge_to_tris[(a, c)].append(tri)
        edge_to_tris[(b, c)].append(tri)
    for e, tris in edge_to_tris.items():
        if tris:
            model.Add(sum(tris) <= 1)

    model.Add(sum(triangle_vars.values()) >= k)
    model.Minimize(sum(edge_vars.values()))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = False

    status = solver.Solve(model)
    status_name = solver.StatusName(status)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        edges = [(u, v) for (u, v), var in edge_vars.items() if solver.Value(var) == 1]
        return status_name, int(solver.ObjectiveValue()), edges
    else:
        return status_name, None, None

def main():
    print("=== 第四问：F(n,k) 精确求解器 ===")
    print("请输入 n,k (用逗号分隔，可附加时间限制秒数，例如 9,5 或 9,5,600)：")
    try:
        parts = input().strip().split(',')
        n = int(parts[0])
        k = int(parts[1])
        time_limit = float(parts[2]) if len(parts) >= 3 else 300.0
    except:
        print("输入格式错误")
        return

    if n < 9 or k <= 0:
        print("n 必须 >=9, k >=1")
        return

    print(f"求解 F({n},{k})，时间限制 {time_limit} 秒...")
    print(f"完全图边数: {n*(n-1)//2}，总三角形数: {n*(n-1)*(n-2)//6}")
    print(f"边不交三角形松上界: {n*(n-1)//6}")
    status, val, edges = solve_F(n, k, time_limit)
    print(f"状态: {status}")
    if status == "OPTIMAL":
        print(f"✅ F({n},{k}) = {val}")
    elif status == "FEASIBLE":
        print(f"ℹ️  F({n},{k}) ≤ {val}")
    elif status == "INFEASIBLE":
        print(f"F({n},{k}) = ∞")
    else:
        print("未完成")

    if edges is not None:
        print(f"边集: {sorted(edges)}")
        ok, msg = verify_solution(n, k, edges)
        print(f"验证: {'✅' if ok else '❌'} {msg}")

if __name__ == "__main__":
    main()