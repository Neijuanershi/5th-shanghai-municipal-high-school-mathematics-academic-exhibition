/-
第二问下界 "N(n) ≥ 4n+1 (∀ n ≥ 2)" 组合层形式化 —— 离散模型
(设计文档 `Q2_lean_baseline_plan.md` v4.4 第 1 节, 逐字遵守)

注: 设计终版 v4.4 中, 公理 A 为前缀形式(见 `Axioms.lean` 的 `base_nine`)。
语义绑定: 见 `README.md` 第 6 节对应清单; 本文件不引用任何第三问文件。
-/
import Mathlib

noncomputable section

open scoped Classical

/-- 计划: 初始航向 + 转向卡列表。`steps` 的每个元素 `(θᵢ, τᵢ)` 是第 i 张转向卡的
    转角与生效时刻, τ 严格递增(题面: 每张卡转角 ≤ 5°, 语义绑定见 README 第 1 条)。
    路径由原点出发、时刻 0 起、速度归一为 1。 -/
structure Plan where
  heading0 : ℝ
  steps    : List (ℝ × ℝ)

namespace Plan

/-- 卡数。设计文档第 1 节记 `cards : ℕ -- = steps.length`; 此处以定义式访问器实现,
    使 `p.cards = p.steps.length` 为定义相等(记账引理 Counting.lean 直接使用)。 -/
def cards (p : Plan) : ℕ := p.steps.length

end Plan

/-- 不透明谓词(语义绑定 README 第 6.2 条): "p 在时刻 t 已逃出第 k 层栅栏" -/
opaque Escaped : Plan → ℕ → ℝ → Prop

/-- 首次逃出谓词(v4.2: Classical.choose 只能取任意见证, 故"首次"必须谓词化) -/
def FirstEscape (p : Plan) (k : ℕ) (t : ℝ) : Prop :=
  Escaped p k t ∧ ∀ s < t, ¬ Escaped p k s

/-- 方向角 θ 的单位方向向量 -/
def dirVec (θ : ℝ) : ℝ × ℝ := (Real.cos θ, Real.sin θ)

/-- 平面向量加法 -/
def vecAdd (a b : ℝ × ℝ) : ℝ × ℝ := (a.1 + b.1, a.2 + b.2)

/-- 平面向量数乘 -/
def vecSmul (r : ℝ) (a : ℝ × ℝ) : ℝ × ℝ := (r * a.1, r * a.2)

/-- 轨迹重建: 按 τᵢ 分界逐段直线; 第 i 段方向 = heading0 + Σ_{j<i} θⱼ, 速度归一为 1;
    分界点即 steps 的时刻。 -/
def pathPoint (p : Plan) (t : ℝ) : ℝ × ℝ :=
  let rec go (pos : ℝ × ℝ) (heading : ℝ) (time : ℝ) : List (ℝ × ℝ) → ℝ × ℝ
    | [] => vecAdd pos (vecSmul (t - time) (dirVec heading))
    | (θ, τ) :: rest =>
        if τ ≤ t then
          go (vecAdd pos (vecSmul (τ - time) (dirVec heading))) (heading + θ) τ rest
        else
          vecAdd pos (vecSmul (t - time) (dirVec heading))
  go (0, 0) p.heading0 0 p.steps

/-- 格点 m e₁ + n e₂, 其中 e₁ = (20, 0), e₂ = (10, 10√3) -/
def latticePoint (m n : ℤ) : ℝ × ℝ :=
  ((20 : ℝ) * (m : ℝ) + (10 : ℝ) * (n : ℝ), (10 : ℝ) * Real.sqrt 3 * (n : ℝ))

/-- 六边形范数 max(|m|, |n|, |m+n|) —— 第 k 层的层号 -/
def layerIndex (m n : ℤ) : ℕ :=
  max (Int.natAbs m) (max (Int.natAbs n) (Int.natAbs (m + n)))

/-- 第 k 层格点集 = { m e₁ + n e₂ | max(|m|,|n|,|m+n|) = k } (k ≥ 1) -/
def Layer (k : ℕ) : Set (ℝ × ℝ) :=
  { c | ∃ m n : ℤ, c = latticePoint m n ∧ layerIndex m n = k }

/-- 两点距离 -/
def planDist (a b : ℝ × ℝ) : ℝ := Real.sqrt ((a.1 - b.1) ^ 2 + (a.2 - b.2) ^ 2)

/-- 分层 Valid: 轨迹全程与第 1..n 层格点距离 ≥ 9 -/
def Valid (n : ℕ) (p : Plan) : Prop :=
  ∀ k : ℕ, 1 ≤ k → k ≤ n → ∀ t : ℝ, ∀ c : ℝ × ℝ, c ∈ Layer k → planDist (pathPoint p t) c ≥ 9

/-- 区间卡数(v4.2): 半开区间 [t₁, t₂) 内的转向卡数 -/
def CrossCards (p : Plan) (t₁ t₂ : ℝ) : ℕ :=
  (p.steps.filter (fun st => t₁ ≤ st.2 ∧ st.2 < t₂)).length

/-- 区间卡数(闭): [t₁, t₂] 内的转向卡数。
    v4.5 修订: 公理 A 改用本定义 (前缀闭区间化) —— 第二问弦上大转角转向
    可恰发生在首次逃出第 2 层的时刻, 该卡必须计入前缀 9 卡。 -/
def CrossCardsLe (p : Plan) (t₁ t₂ : ℝ) : ℕ :=
  (p.steps.filter (fun st => t₁ ≤ st.2 ∧ st.2 ≤ t₂)).length

/-- 区间卡数(左开右闭): (t₁, t₂] 内的转向卡数。
    v4.5 修订: 公理 B 改用本定义 —— 逐层段右端 = 首次逃出时刻, 该时刻的卡
    (含弦上转向) 归入本层段, 与闭前缀 [0, t₀] 拼合无重叠、无遗漏。 -/
def CrossCardsOC (p : Plan) (t₁ t₂ : ℝ) : ℕ :=
  (p.steps.filter (fun st => t₁ < st.2 ∧ st.2 ≤ t₂)).length
