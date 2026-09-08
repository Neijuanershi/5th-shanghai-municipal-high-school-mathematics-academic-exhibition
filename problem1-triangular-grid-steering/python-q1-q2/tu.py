#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三角网格障碍物可视化工具
- 原点视为虚拟格点（无障碍圆）
- 所有格点（含原点）只与最近 6 个邻居用绿色虚线连接
- 格点：深红色，带 P_{n,k} 文本标签
- 障碍物：膨胀为半径 9 的淡蓝色圆盘
- 无坐标轴刻度，保留边框
- 用户手动输入输出文件夹
- 支持输出：jpg / jpeg / png / svg
"""
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import rcParams
# ---------- 字体 ----------
rcParams["font.family"] = "DejaVu Sans"
rcParams["font.size"] = 10
rcParams["axes.titlesize"] = 13
rcParams["axes.labelsize"] = 11
rcParams["legend.fontsize"] = 10
# ---------- 几何参数 ----------
E1 = (20.0, 0.0)
E2 = (10.0, 10.0 * math.sqrt(3.0))
INFLATE_RADIUS = 9.0
# 三角网格"最近邻"6 个偏移：(Δm, Δn')
# 距离都为 20 米（正六边形顶点）
NEIGHBOR_OFFSETS = [
    ( 1,  0),   # +e1
    (-1,  0),   # -e1
    ( 0,  1),   # +e2
    ( 0, -1),   # -e2
    ( 1, -1),   # +e1 - e2
    (-1,  1),   # -e1 + e2
]
# ---------- 颜色 ----------
POINT_COLOR = "#8B0000"
EDGE_COLOR = "#2E8B57"
OBSTACLE_FACE = "#B0D4E3"
OBSTACLE_EDGE = "#3B6E91"
LABEL_COLOR = "#3B0A0A"
def offset_to_vector(dm, dn):
    """将 (Δm, Δn') 转换为 (Δx, Δy)。"""
    return (dm * E1[0] + dn * E2[0],
            dm * E1[1] + dn * E2[1])
def layer_n_points(n: int):
    """第 n 层所有格点。"""
    pts = []
    for m in range(-n, n + 1):
        for np_ in range(-n, n + 1):
            if max(abs(m), abs(np_), abs(m + np_)) == n:
                x = 20.0 * m + 10.0 * np_
                y = 10.0 * math.sqrt(3.0) * np_
                pts.append((m, np_, x, y))
    return pts
def polar_angle_deg(x: float, y: float) -> float:
    a = math.degrees(math.atan2(y, x)) % 360.0
    return a
def order_layer(pts):
    """第 n 层格点按极角排序（0° 起）。"""
    indexed = [(polar_angle_deg(x, y), i) for i, (_, _, x, y) in enumerate(pts)]
    indexed.sort()
    return [pts[i] for (_, i) in indexed]
def all_layers_ordered(max_n: int):
    """返回 [(n, k, x, y), ...]，k=1 对应水平轴正方向，逆时针。"""
    result = []
    for n in range(1, max_n + 1):
        raw = layer_n_points(n)
        ordered = order_layer(raw)
        for k, (m, np_, x, y) in enumerate(ordered, start=1):
            result.append((n, k, x, y))
    return result
def neighbor_edges_with_origin(labeled_points):
    """
    三角网格 6 最近邻边（用 (m, n') 索引判定邻居），
    把原点 (0,0,0,0) 作为虚拟格点参与连线。
    返回去重后的边集。
    """
    # 用 (m, n') 索引作 key，避免浮点误差
    index_set = set()
    coord_map = {}
    for (n, k, x, y) in labeled_points:
        # 反算 (m, n')
        # (x, y) = (20m + 10n', 10√3·n')
        # n' = y / (10√3)
        # m = (x - 10n') / 20
        np_ = round(y / (10.0 * math.sqrt(3.0)))
        m = round((x - 10.0 * np_) / 20.0)
        index_set.add((m, np_))
        coord_map[(m, np_)] = (x, y)
    # 原点 (0, 0)
    index_set.add((0, 0))
    coord_map[(0, 0)] = (0.0, 0.0)
    edges = set()
    for (m, np_) in index_set:
        for (dm, dn) in NEIGHBOR_OFFSETS:
            nm = (m + dm, np_ + dn)
            if nm in index_set:
                a = coord_map[(m, np_)]
                b = coord_map[nm]
                edge = (a, b) if a < b else (b, a)
                edges.add(edge)
    return edges
def choose_formats():
    print("\n请选择输出图片格式：")
    print("  1) jpg")
    print("  2) jpeg")
    print("  3) png")
    print("  4) svg")
    print("  5) 全部都生成（默认）")
    mapping = {
        "1": ["jpg"], "2": ["jpeg"], "3": ["png"], "4": ["svg"],
        "": ["jpg", "jpeg", "png", "svg"], "5": ["jpg", "jpeg", "png", "svg"],
    }
    while True:
        choice = input("选项编号 [1-5，回车=全部]: ").strip()
        if choice in mapping:
            return mapping[choice]
        print("无效输入，请重试。")
def ask_output_dir():
    while True:
        path = input("\n请输入输出文件夹路径（回车=当前目录）: ").strip()
        if path == "":
            return os.getcwd()
        path = os.path.expanduser(os.path.expandvars(path))
        if os.path.isdir(path):
            return os.path.abspath(path)
        try:
            os.makedirs(path, exist_ok=True)
            print(f"已创建目录: {os.path.abspath(path)}")
            return os.path.abspath(path)
        except OSError as e:
            print(f"无法创建目录: {e}，请重试。")
def ask_layers():
    while True:
        s = input("请输入层数 n（正整数）: ").strip()
        try:
            n = int(s)
            if n < 1:
                print("层数必须 >= 1。")
                continue
            return n
        except ValueError:
            print("请输入整数。")
def label_offset(x, y):
    dx, dy = 3.0, 3.0
    if x < 0:
        dx = -3.0
    if y < 0:
        dy = -3.0
    return dx, dy
def draw(max_n: int, fmt: str, out_path: str):
    labeled = all_layers_ordered(max_n)
    point_coords = [(x, y) for (_, _, x, y) in labeled]
    edges = neighbor_edges_with_origin(labeled)
    fig, ax = plt.subplots(figsize=(11, 11))
    ax.set_aspect("equal")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    # 1) 三角网格边（含原点）
    for (a, b) in edges:
        ax.plot([a[0], b[0]], [a[1], b[1]],
                color=EDGE_COLOR, linestyle="--",
                linewidth=0.9, alpha=0.75, zorder=1)
    # 2) 障碍物圆盘
    for (x, y) in point_coords:
        circle = patches.Circle(
            (x, y), INFLATE_RADIUS,
            facecolor=OBSTACLE_FACE,
            edgecolor=OBSTACLE_EDGE,
            linewidth=1.0,
            alpha=0.75,
            zorder=2,
        )
        ax.add_patch(circle)
    # 3) 格点（深红色）
    xs = [x for (x, y) in point_coords]
    ys = [y for (x, y) in point_coords]
    ax.scatter(xs, ys, s=28, color=POINT_COLOR,
               edgecolors="white", linewidths=0.4,
               zorder=3, label="格点 P_{n,k}")
    # 4) 原点（黑色十字，无障碍圆）
    ax.scatter([0], [0], s=160, marker="+",
               color="black", linewidths=2.0, zorder=5,
               label="原点")
    # 5) 标签
    for (n, k, x, y) in labeled:
        dx, dy = label_offset(x, y)
        ax.annotate(
            f"P_{{{n},{k}}}",
            xy=(x, y), xytext=(x + dx, y + dy),
            fontsize=8.5, color=LABEL_COLOR,
            ha="center", va="center",
            zorder=4,
        )
    # 6) 坐标范围
    if point_coords:
        r = max(math.hypot(x, y) for (x, y) in point_coords) + INFLATE_RADIUS + 8
    else:
        r = 30
    ax.set_xlim(-r, r)
    ax.set_ylim(-r, r)
    # 7) 去掉坐标轴标尺
    ax.set_xticks([])
    ax.set_yticks([])
    # 8) 标题与图例
    ax.set_title(f"三角网格障碍物图：层数 1 ≤ n ≤ {max_n}，共 {len(labeled)} 个格点")
    ax.legend(loc="upper right", framealpha=0.95)
    # 9) 保存
    save_kwargs = dict(bbox_inches="tight")
    if fmt == "svg":
        plt.savefig(out_path, format="svg", **save_kwargs)
    else:
        plt.savefig(out_path, dpi=160, **save_kwargs)
    plt.close(fig)
def main():
    print("=" * 56)
    print("    三角网格障碍物可视化工具")
    print("=" * 56)
    max_n = ask_layers()
    out_dir = ask_output_dir()
    formats = choose_formats()
    print()
    for fmt in formats:
        out = os.path.join(out_dir, f"obstacle_map_n{max_n}.{fmt}")
        draw(max_n, fmt, out)
        print(f"  ✓ 已生成: {out}")
    print(f"\n输出目录: {out_dir}")
    print("全部完成。")
if __name__ == "__main__":
    main()