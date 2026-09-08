/-
目标定理 + 强归纳 (设计文档 `Q2_lean_baseline_plan.md` v4.4 第 3–4 节; 全证, 无占位)。

证明骨架: 基例 = 公理 A(闭区间前缀形式 `base_nine`, v4.5 修订);
归纳步 = 公理 B + D/E + 左开右闭区间可加, 合成 9 + 4(n−2) = 4n+1。
-/
import Q2Formal.Axioms
import Q2Formal.Counting

noncomputable section

open Classical

/-- Escaped 向下嵌套: 由公理 C 迭代 (n 降到 k)。 -/
lemma escaped_down (p : Plan) (t : ℝ) :
    ∀ {k n : ℕ}, k ≤ n → Escaped p n t → Escaped p k t := by
  intro k n hkn hn
  induction n using Nat.strong_induction_on generalizing k with
  | h n ih =>
    by_cases hk : k = n
    · subst k
      exact hn
    · have hklt : k < n := lt_of_le_of_ne hkn hk
      have hk' : k ≤ n - 1 := by omega
      have hn' : Escaped p (n - 1) t := by
        have h1n : 1 ≤ n := by omega
        have hnn : Escaped p (n - 1 + 1) t := by
          simpa [Nat.sub_add_cancel h1n] using hn
        exact escape_nested p (n - 1) t hnn
      exact ih (n - 1) (by omega) hk' hn'

/-- 首次逃出链: t₂ < t₃ < ... < t_n, 每层 FirstEscape (由公理 D/E 构造, 强归纳)。 -/
lemma firstEscape_chain (p : Plan) : ∀ {n : ℕ}, 2 ≤ n → (∃ t, Escaped p n t) →
    ∃ ts : List ℝ, ts.length = n - 1 ∧
      (∀ k : ℕ, 2 ≤ k → k ≤ n → ∀ hk : k - 2 < ts.length,
          FirstEscape p k (ts[k - 2]'hk)) ∧
      (∀ k : ℕ, 2 ≤ k → k + 1 ≤ n → ∀ hk : k - 2 < ts.length, ∀ hk' : k - 1 < ts.length,
          ts[k - 2]'hk < ts[k - 1]'hk') := by
  intro n hn hesc
  induction n using Nat.strong_induction_on with
  | h n ih =>
    by_cases hn2 : n = 2
    · subst n
      rcases first_exists p 2 hesc with ⟨t₂, hfe⟩
      refine ⟨[t₂], by simp, ?_, ?_⟩
      · intro k hk2 hk hk'
        have : k = 2 := by omega
        subst k
        simpa using hfe
      · intro k hk2 hk hk' hk''
        omega
    · have hn1 : 2 ≤ n - 1 := by omega
      have hesc1 : ∃ t, Escaped p (n - 1) t := by
        rcases hesc with ⟨t₀, h₀⟩
        exact ⟨t₀, escaped_down p t₀ (by omega) h₀⟩
      rcases ih (n - 1) (by omega) hn1 hesc1 with ⟨ts', hlen', hFE', hord'⟩
      rcases first_exists p n hesc with ⟨tn, hfen⟩
      have hfeprev : FirstEscape p (n - 1) (ts'[(n - 1) - 2]'(by omega)) :=
        hFE' (n - 1) (by omega) (by omega) (by omega)
      have hordlast : ts'[(n - 1) - 2]'(by omega) < tn := by
        have h1n : 1 ≤ n := by omega
        have hfenn : FirstEscape p (n - 1 + 1) tn := by
          simpa [Nat.sub_add_cancel h1n] using hfen
        exact first_order p (n - 1) (ts'[(n - 1) - 2]'(by omega)) tn hfenn hfeprev
      refine ⟨ts' ++ [tn], ?_, ?_, ?_⟩
      · have : (ts' ++ [tn]).length = (n - 1 - 1) + 1 := by simp [hlen']
        omega
      · intro k hk2 hk hk'
        by_cases hklt : k < n
        · have hk1 : k ≤ n - 1 := by omega
          have hget : (ts' ++ [tn])[k - 2]'hk' = ts'[k - 2]'(by omega) := by
            apply List.getElem_append_left
          rw [hget]
          exact hFE' k hk2 hk1 (by omega)
        · have : k = n := by omega
          subst k
          have hget : (ts' ++ [tn])[n - 2]'hk' = tn := by
            have hidx : n - 2 = ts'.length := by omega
            simp only [hidx]
            rw [List.getElem_append_right (by omega : ts'.length ≤ ts'.length)]
            simp
          rw [hget]
          exact hfen
      · intro k hk2 hk hk' hk''
        by_cases hk1n : k + 1 = n
        · have : k = n - 1 := by omega
          subst k
          have h1 : (ts' ++ [tn])[(n - 1) - 2]'hk' = ts'[(n - 1) - 2]'(by omega) := by
            apply List.getElem_append_left
          have h2 : (ts' ++ [tn])[(n - 1) - 1]'hk'' = tn := by
            have hidx : (n - 1) - 1 = ts'.length := by omega
            simp only [hidx]
            rw [List.getElem_append_right (by omega : ts'.length ≤ ts'.length)]
            simp
          rw [h1, h2]
          exact hordlast
        · have hk1lt : k + 1 < n := by omega
          have h1 : (ts' ++ [tn])[k - 2]'hk' = ts'[k - 2]'(by omega) := by
            apply List.getElem_append_left
          have h2 : (ts' ++ [tn])[k - 1]'hk'' = ts'[k - 1]'(by omega) := by
            apply List.getElem_append_left
          rw [h1, h2]
          exact hord' k hk2 (by omega) (by omega) (by omega)

/-- CrossCards 自交为空: [t, t) 无卡。 -/
lemma crossCards_self (p : Plan) (t : ℝ) : CrossCards p t t = 0 := by
  have h := crossCards_add p t t t (le_rfl) (le_rfl)
  omega

/-- CrossCardsOC 自交为空: (t, t] 无卡 (v4.5: 链望远镜 m=0 情形用)。 -/
lemma crossCardsOC_self (p : Plan) (t : ℝ) : CrossCardsOC p t t = 0 := by
  have h := crossCardsOC_add p t t t (le_rfl) (le_rfl)
  omega

/-- t ≤ 0 时 [0, t) 无卡。 -/
lemma crossCards_right_nonpos (p : Plan) {t : ℝ} (ht : t ≤ 0) : CrossCards p 0 t = 0 := by
  unfold CrossCards
  rw [List.length_eq_zero_iff, List.filter_eq_nil_iff]
  intro st hst
  intro h
  have hd : 0 ≤ st.2 ∧ st.2 < t := of_decide_eq_true h
  have : st.2 < 0 := lt_of_lt_of_le hd.2 ht
  exact (not_lt_of_ge hd.1) this

/-- 相邻首出时刻对的卡数和: 沿链 t₀ t₁ ... tₘ 累加 CrossCardsOC(tᵢ, tᵢ₊₁]
    (v4.5: 左开右闭, 段右端首逃时刻的卡归本段)。用结构递归取代 range 索引,
    避免 getElem 界证明。 -/
def ccChain (p : Plan) : List ℝ → ℕ
  | [] => 0
  | [_] => 0
  | t₀ :: t₁ :: rest => CrossCardsOC p t₀ t₁ + ccChain p (t₁ :: rest)

theorem ccChain_cons (p : Plan) (t₀ t₁ : ℝ) (rest : List ℝ) :
    ccChain p (t₀ :: t₁ :: rest) = CrossCardsOC p t₀ t₁ + ccChain p (t₁ :: rest) := rfl

/-- 严格递增链的传递: i < j ≤ m 时 ts[i] < ts[j] (对 j - (i+1) 归纳)。 -/
lemma chain_lt_between {m : ℕ} {ts : List ℝ}
    (hord : ∀ k : ℕ, 0 ≤ k → k + 1 < m + 1 → ∀ hk : k < ts.length, ∀ hk' : k + 1 < ts.length,
        ts[k]'hk < ts[k + 1]'hk') :
    ∀ i j : ℕ, i < j → j ≤ m → ∀ hi : i < ts.length, ∀ hj : j < ts.length,
      ts[i]'hi < ts[j]'hj := by
  intro i j hij hjm hi hj
  induction h : j - (i + 1) generalizing i j with
  | zero =>
      have hij' : i + 1 = j := by omega
      have hordi := hord i (by omega) (by omega) hi (by omega)
      simpa only [hij'] using hordi
  | succ d ih =>
      have h1 : ts[i]'hi < ts[i + 1]'(by omega) := hord i (by omega) (by omega) hi (by omega)
      have h2 : ts[i + 1]'(by omega) < ts[j]'hj := by
        apply ih (i + 1) j
        · omega
        · omega
        · omega
      exact lt_trans h1 h2

/-- 望远镜: 相邻左开右闭区间卡数和 = 首尾区间 (逐对 crossCardsOC_add)。 -/
lemma ccChain_telescope (p : Plan) : ∀ (m : ℕ) (ts : List ℝ), ts.length = m + 1 →
    (∀ k : ℕ, 0 ≤ k → k + 1 < m + 1 → ∀ hk : k < ts.length, ∀ hk' : k + 1 < ts.length,
        ts[k]'hk < ts[k + 1]'hk') →
    ∀ (h0 : 0 < ts.length) (hm : m < ts.length),
    ccChain p ts = CrossCardsOC p (ts[0]'h0) (ts[m]'hm) := by
  intro m ts hlen hord h0 hm
  induction ts generalizing m with
  | nil => simp at hlen
  | cons t₀ ts' ih =>
    by_cases hm0 : m = 0
    · subst m
      cases ts' with
      | nil =>
          dsimp [ccChain]
          exact (crossCardsOC_self p t₀).symm
      | cons t₁ rest => simp at hlen
    · cases ts' with
      | nil => simp at hlen; omega
      | cons t₁ rest =>
        have hlen' : (t₁ :: rest).length = m - 1 + 1 := by
          have : (t₁ :: rest).length = m := by
            have := hlen
            simp at this
            omega
          omega
        have hord' : ∀ k : ℕ, 0 ≤ k → k + 1 < (m - 1) + 1 →
            ∀ hk : k < (t₁ :: rest).length, ∀ hk' : k + 1 < (t₁ :: rest).length,
            (t₁ :: rest)[k]'hk < (t₁ :: rest)[k + 1]'hk' := by
          intro k hk0 hk hkA hkB
          have h1 : (t₁ :: rest)[k]'hkA = (t₀ :: t₁ :: rest)[k + 1]'(by omega) := rfl
          have h2 : (t₁ :: rest)[k + 1]'hkB = (t₀ :: t₁ :: rest)[(k + 1) + 1]'(by omega) := rfl
          rw [h1, h2]
          exact hord (k + 1) (by omega) (by omega) (by omega) (by omega)
        have ht₀t₁ : t₀ ≤ t₁ := by
          have : (t₀ :: t₁ :: rest)[0]'(by omega) < (t₀ :: t₁ :: rest)[1]'(by omega) :=
            hord 0 (by omega) (by omega) (by omega) (by omega)
          change t₀ < t₁ at this
          exact le_of_lt this
        have ht₁t₃ : t₁ ≤ (t₀ :: t₁ :: rest)[m]'hm := by
          by_cases hm1 : m = 1
          · subst m
            exact le_rfl
          · have h1m : 1 < m := by omega
            have : (t₀ :: t₁ :: rest)[1]'(by omega) < (t₀ :: t₁ :: rest)[m]'hm :=
              chain_lt_between hord 1 m h1m (by omega) (by omega) hm
            change t₁ < (t₀ :: t₁ :: rest)[m]'hm at this
            exact le_of_lt this
        have h0' : 0 < (t₁ :: rest).length := by omega
        have hm' : m - 1 < (t₁ :: rest).length := by omega
        calc
          ccChain p (t₀ :: t₁ :: rest)
              = CrossCardsOC p t₀ t₁ + ccChain p (t₁ :: rest) := rfl
          _ = CrossCardsOC p t₀ t₁ + CrossCardsOC p t₁ ((t₀ :: t₁ :: rest)[m]'hm) := by
                rw [ih (m - 1) hlen' hord' h0' hm']
                rw [List.getElem_cons_zero]
                cases m with
                | zero => omega
                | succ m' => rfl
          _ = CrossCardsOC p ((t₀ :: t₁ :: rest)[0]'h0) ((t₀ :: t₁ :: rest)[m]'hm) := by
                apply crossCardsOC_add
                · exact ht₀t₁
                · exact ht₁t₃

/-- 逐层 ≥ 4 卡: 公理 B 沿链累加 (层号 k 随链下移而 +1)。 -/
lemma ccChain_ge_four (p : Plan) (n k : ℕ) (hv : Valid n p) :
    ∀ (m : ℕ) (ts : List ℝ), ts.length = m + 1 →
    (∀ j : ℕ, 0 ≤ j → j + 1 ≤ m + 1 → ∀ hj : j < ts.length,
        FirstEscape p (j + k) (ts[j]'hj)) →
    2 ≤ k → k + m ≤ n →
    4 * m ≤ ccChain p ts := by
  intro m ts hlen hFE hk2 hkn
  induction ts generalizing m k with
  | nil => simp at hlen
  | cons t₀ ts' ih =>
    by_cases hm0 : m = 0
    · subst m
      cases ts' with
      | nil => simp [ccChain]
      | cons t₁ rest => omega
    · cases ts' with
      | nil => simp at hlen; omega
      | cons t₁ rest =>
        have hlen' : (t₁ :: rest).length = m - 1 + 1 := by
          have : (t₁ :: rest).length = m := by
            have := hlen
            simp at this
            omega
          omega
        have hFE' : ∀ j : ℕ, 0 ≤ j → j + 1 ≤ (m - 1) + 1 →
            ∀ hj : j < (t₁ :: rest).length,
            FirstEscape p (j + (k + 1)) ((t₁ :: rest)[j]'hj) := by
          intro j hj0 hj hj'
          have hget : (t₁ :: rest)[j]'hj' = (t₀ :: t₁ :: rest)[j + 1]'(by omega) := rfl
          rw [hget]
          have hk' : (j + 1) + k = j + (k + 1) := by omega
          rw [← hk']
          exact hFE (j + 1) (by omega) (by omega) (by omega)
        have hih : 4 * (m - 1) ≤ ccChain p (t₁ :: rest) :=
          ih (k + 1) (m - 1) hlen' hFE' (by omega) (by omega)
        have hCC : 4 ≤ CrossCardsOC p t₀ t₁ := by
          apply layer_four p k t₀ t₁
          · exact hk2
          · exact valid_mono (show k + 1 ≤ n from by omega) hv
          · have hf0 := hFE 0 (by omega) (by omega) (by omega)
            rw [List.getElem_cons_zero] at hf0
            simpa using hf0
          · have hf1 := hFE 1 (by omega) (by omega) (by omega)
            rw [show (1 : ℕ) + k = k + 1 from by omega] at hf1
            rw [List.getElem_cons_succ] at hf1
            rw [List.getElem_cons_zero] at hf1
            exact hf1
        rw [ccChain_cons]
        exact le_trans (by omega : 4 * m ≤ 4 + 4 * (m - 1)) (add_le_add hCC hih)

/-- 目标定理 (设计文档第 3 节, 逐字):
    N_lower_bound (n : ℕ) (hn : 2 ≤ n) :
      ∀ p : Plan, Valid n p → (∃ t, Escaped p n t) → p.cards ≥ 4 * n + 1 -/
theorem N_lower_bound (n : ℕ) (hn : 2 ≤ n) :
    ∀ p : Plan, Valid n p → (∃ t, Escaped p n t) → p.cards ≥ 4 * n + 1 := by
  intro p hv hesc
  rcases firstEscape_chain p hn hesc with ⟨ts, hlen, hFE, hord⟩
  let m : ℕ := n - 2
  have hm_len : ts.length = m + 1 := by dsimp [m]; omega
  have hFE0 : ∀ j : ℕ, 0 ≤ j → j + 1 ≤ m + 1 → ∀ hj : j < ts.length,
      FirstEscape p (j + 2) (ts[j]'hj) := by
    intro j hj0 hj hj'
    have hFEj := hFE (j + 2) (by omega) (by omega) (by omega)
    simpa only [show (j + 2) - 2 = j from by omega] using hFEj
  have hord0 : ∀ k : ℕ, 0 ≤ k → k + 1 < m + 1 → ∀ hk : k < ts.length, ∀ hk' : k + 1 < ts.length,
      ts[k]'hk < ts[k + 1]'hk' := by
    intro k hk0 hk hkA hkB
    have hordk := hord (k + 2) (by omega) (by omega) (by omega) (by omega)
    simpa only [show (k + 2) - 2 = k from by omega, show (k + 2) - 1 = k + 1 from by omega] using hordk
  -- 基例: 前 9 卡 (公理 A, v4.5 闭前缀)
  have hbase : CrossCardsLe p 0 (ts[0]'(by omega)) ≥ 9 :=
    base_nine p (ts[0]'(by omega)) (valid_mono (show 2 ≤ n from hn) hv)
      (hFE0 0 (by omega) (by omega) (by omega))
  -- 逐层 ≥ 4 卡 (公理 B)
  have hlayers : 4 * m ≤ ccChain p ts :=
    ccChain_ge_four p n 2 hv m ts hm_len hFE0 (by omega) (by omega)
  -- 望远镜 + 左开右闭区间可加
  have htel : ccChain p ts = CrossCardsOC p (ts[0]'(by omega)) (ts[m]'(by omega)) :=
    ccChain_telescope p m ts hm_len hord0 (by omega) (by omega)
  have htotal : CrossCardsLe p 0 (ts[0]'(by omega)) + ccChain p ts ≤ p.cards := by
    rw [htel]
    exact crossCardsLe_oc_pair_le p (ts[0]'(by omega)) (ts[m]'(by omega))
  -- 合成 9 + 4(n−2) = 4n + 1
  have hsum : 9 + 4 * m ≤ p.cards := le_trans (add_le_add hbase hlayers) htotal
  dsimp [m] at hsum ⊢
  omega
