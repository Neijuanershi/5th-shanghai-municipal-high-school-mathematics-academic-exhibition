/-
记账引理 (设计文档 `Q2_lean_baseline_plan.md` v4.4 第 4.1 节; 全证, 无占位)。
  注意: 设计终版 v4.5 的公理 A 为闭区间前缀形式 (`CrossCardsLe`)、公理 B 为左开右闭
  逐层段 (`CrossCardsOC`), 本文件引理与之配套 (半开 `CrossCards` 引理保留备用)。
  ceil 单调 / 次可加; 卡数 ≥ Σ⌈段转角/5°⌉; 区间可加 (半开/左开右闭); Valid n → Valid k。
-/
import Q2Formal.Model

noncomputable section

open scoped Classical

/-- 上取整 ceil : ℝ → ℕ (自证版: 存在性 = 阿基米德性 `exists_nat_ge`,
    最小性 = `Nat.find`)。 -/
def ceilNat (x : ℝ) : ℕ := Nat.find (exists_nat_ge x)

/-- ceil 主性质: x ≤ ceilNat x -/
theorem ceilNat_spec (x : ℝ) : x ≤ (ceilNat x : ℝ) :=
  Nat.find_spec (exists_nat_ge x)

/-- ceil 单调 -/
theorem ceilNat_mono {x y : ℝ} (h : x ≤ y) : ceilNat x ≤ ceilNat y := by
  apply Nat.find_min'
  exact le_trans h (ceilNat_spec y)

/-- ceil 次可加 -/
theorem ceilNat_add_le (x y : ℝ) : ceilNat (x + y) ≤ ceilNat x + ceilNat y := by
  apply Nat.find_min'
  have hx : x ≤ (ceilNat x : ℝ) := ceilNat_spec x
  have hy : y ≤ (ceilNat y : ℝ) := ceilNat_spec y
  calc
    x + y ≤ (ceilNat x : ℝ) + (ceilNat y : ℝ) := add_le_add hx hy
    _ = ((ceilNat x + ceilNat y : ℕ) : ℝ) := by rw [Nat.cast_add]

/-- 5° (弧度) -/
def deg5 : ℝ := (5 : ℝ) / 180 * Real.pi

theorem deg5_pos : 0 < deg5 := by
  unfold deg5
  positivity

/-- 每张卡至多 5° 时, 单卡对 Σ⌈|θ|/5°⌉ 的贡献 ≤ 1 -/
theorem ceil_turn_le_one {θ : ℝ} (h : |θ| ≤ deg5) : ceilNat (|θ| / deg5) ≤ 1 := by
  apply Nat.find_min'
  rw [div_le_iff₀ deg5_pos]
  simpa using h

/-- List 版记账: 若每项 f a ≤ 1, 则 (l.map f).sum ≤ l.length -/
theorem List_sum_le_length {α : Type u} (f : α → ℕ) (l : List α) (h : ∀ a ∈ l, f a ≤ 1) :
    (l.map f).sum ≤ l.length := by
  induction l with
  | nil => simp
  | cons a t ih =>
      have ht : ∀ b ∈ t, f b ≤ 1 := fun b hb => h b (by simp [hb])
      specialize ih ht
      have ha : f a ≤ 1 := h a (by simp)
      simp
      omega

/-- 记账: 卡数 ≥ Σ⌈段转角/5°⌉ (每张卡 ≤ 5° 时) -/
theorem cards_ge_sum_ceil_turns (p : Plan) (hsmall : ∀ st ∈ p.steps, |st.1| ≤ deg5) :
    p.cards ≥ (p.steps.map (fun st => ceilNat (|st.1| / deg5))).sum := by
  have h : ∀ st ∈ p.steps, ceilNat (|st.1| / deg5) ≤ 1 :=
    fun st hst => ceil_turn_le_one (hsmall st hst)
  simpa [Plan.cards] using
    (List_sum_le_length (fun st => ceilNat (|st.1| / deg5)) p.steps h)

/-- Valid 单调: Valid n → Valid k (k ≤ n) -/
theorem valid_mono {n k : ℕ} {p : Plan} (h : k ≤ n) (hv : Valid n p) : Valid k p := by
  intro j hj1 hjk t c hc
  exact hv j hj1 (le_trans hjk h) t c hc

/-- CrossCards 半开区间可加: [t₁,t₂) ⊎ [t₂,t₃) = [t₁,t₃) (需 t₁ ≤ t₂ ≤ t₃;
    端点归属由定义直接给出; 对卡表逐项分类证明) -/
theorem crossCards_add (p : Plan) (t₁ t₂ t₃ : ℝ) (ht₁ : t₁ ≤ t₂) (ht₂ : t₂ ≤ t₃) :
    CrossCards p t₁ t₂ + CrossCards p t₂ t₃ = CrossCards p t₁ t₃ := by
  unfold CrossCards
  induction p.steps with
  | nil => simp
  | cons st t ih =>
      by_cases h1 : t₁ ≤ st.2 ∧ st.2 < t₂
      · by_cases h2 : t₂ ≤ st.2 ∧ st.2 < t₃
        · have : False := (not_lt_of_ge h2.1) h1.2
          cases this
        · have h3 : t₁ ≤ st.2 ∧ st.2 < t₃ := ⟨h1.1, lt_of_lt_of_le h1.2 ht₂⟩
          simp [h1, h2, h3] at ih ⊢
          omega
      · by_cases h2 : t₂ ≤ st.2 ∧ st.2 < t₃
        · have h3 : t₁ ≤ st.2 ∧ st.2 < t₃ := ⟨le_trans ht₁ h2.1, h2.2⟩
          simp [h1, h2, h3] at ih ⊢
          omega
        · have h3 : ¬ (t₁ ≤ st.2 ∧ st.2 < t₃) := by
            intro h
            by_cases hle : t₂ ≤ st.2
            · exact h2 ⟨hle, h.2⟩
            · exact h1 ⟨h.1, lt_of_not_ge hle⟩
          simp [h1, h2, h3] at ih ⊢
          omega

/-- 嵌套 ⟹ 可加: 相邻首次逃出时刻给出两段互不重叠的半开区间之和 -/
theorem crossCards_disjoint_add (p : Plan) (t₁ t₂ t₃ : ℝ) (h₁ : t₁ ≤ t₂) (h₂ : t₂ ≤ t₃) :
    CrossCards p t₁ t₂ + CrossCards p t₂ t₃ = CrossCards p t₁ t₃ :=
  crossCards_add p t₁ t₂ t₃ h₁ h₂

/-- CrossCards ≤ 总卡数 -/
theorem crossCards_le_cards (p : Plan) (t₁ t₂ : ℝ) : CrossCards p t₁ t₂ ≤ p.cards := by
  unfold CrossCards Plan.cards
  induction p.steps with
  | nil => simp
  | cons st t ih =>
      by_cases h : t₁ ≤ st.2 ∧ st.2 < t₂ <;> simp [h] at ih ⊢ <;> omega

/-- 两个互不重叠半开区间上的卡数之和 ≤ 总卡数 (各层区间加总用) -/
theorem crossCards_pair_le (p : Plan) (t₁ t₂ t₃ : ℝ) :
    CrossCards p t₁ t₂ + CrossCards p t₂ t₃ ≤ p.cards := by
  unfold CrossCards Plan.cards
  induction p.steps with
  | nil => simp
  | cons st t ih =>
      by_cases h1 : t₁ ≤ st.2 ∧ st.2 < t₂
      · by_cases h2 : t₂ ≤ st.2 ∧ st.2 < t₃
        · have : False := (not_lt_of_ge h2.1) h1.2
          cases this
        · simp [h1, h2] at ih ⊢
          omega
      · by_cases h2 : t₂ ≤ st.2 ∧ st.2 < t₃
        · simp [h1, h2] at ih ⊢
          omega
        · simp [h1, h2] at ih ⊢
          omega

/-- CrossCardsOC 左开右闭区间可加: (t₁,t₂] ⊎ (t₂,t₃] = (t₁,t₃] (需 t₁ ≤ t₂ ≤ t₃;
    v4.5 修订: 逐层段左开右闭, 端点归属由定义直接给出; 对卡表逐项分类证明) -/
theorem crossCardsOC_add (p : Plan) (t₁ t₂ t₃ : ℝ) (ht₁ : t₁ ≤ t₂) (ht₂ : t₂ ≤ t₃) :
    CrossCardsOC p t₁ t₂ + CrossCardsOC p t₂ t₃ = CrossCardsOC p t₁ t₃ := by
  unfold CrossCardsOC
  induction p.steps with
  | nil => simp
  | cons st u ih =>
      by_cases h1 : t₁ < st.2 ∧ st.2 ≤ t₂
      · by_cases h2 : t₂ < st.2 ∧ st.2 ≤ t₃
        · have : False := (not_lt_of_ge h1.2) h2.1
          cases this
        · have h3 : t₁ < st.2 ∧ st.2 ≤ t₃ := ⟨h1.1, le_trans h1.2 ht₂⟩
          simp [h1, h2, h3] at ih ⊢
          omega
      · by_cases h2 : t₂ < st.2 ∧ st.2 ≤ t₃
        · have h3 : t₁ < st.2 ∧ st.2 ≤ t₃ := ⟨lt_of_le_of_lt ht₁ h2.1, h2.2⟩
          simp [h1, h2, h3] at ih ⊢
          omega
        · have h3 : ¬ (t₁ < st.2 ∧ st.2 ≤ t₃) := by
            intro h
            by_cases hle : t₂ < st.2
            · exact h2 ⟨hle, h.2⟩
            · exact h1 ⟨h.1, le_of_not_gt hle⟩
          simp [h1, h2, h3] at ih ⊢
          omega

/-- 闭前缀 [0, t] 与左开右闭链 (t, t'] 无重叠, 卡数和 ≤ 总卡数 (v4.5 修订:
    公理 A 闭前缀 + 公理 B 左开右闭逐层段的合成引理; τ ≤ t 与 t < τ 互斥) -/
theorem crossCardsLe_oc_pair_le (p : Plan) (t t' : ℝ) :
    CrossCardsLe p 0 t + CrossCardsOC p t t' ≤ p.cards := by
  unfold CrossCardsLe CrossCardsOC Plan.cards
  induction p.steps with
  | nil => simp
  | cons st u ih =>
      by_cases h1 : 0 ≤ st.2 ∧ st.2 ≤ t
      · by_cases h2 : t < st.2 ∧ st.2 ≤ t'
        · have : False := (not_lt_of_ge h1.2) h2.1
          cases this
        · simp [h1, h2] at ih ⊢
          omega
      · by_cases h2 : t < st.2 ∧ st.2 ≤ t'
        · simp [h1, h2] at ih ⊢
          omega
        · simp [h1, h2] at ih ⊢
          omega
