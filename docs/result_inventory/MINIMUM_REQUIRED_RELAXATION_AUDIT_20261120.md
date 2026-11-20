# EOG最小制約緩和（Minimum Required Relaxation）成果監査 — 2026-11-20

**監査基準main:** `d61b9887804d01ef78f020475a8ed127948c6db1`。この文書は[数理監査](MATHEMATICAL_DEEP_AUDIT_20261120.md)の補遺。**新規解析・再得点・観測endpoint追加なし**。従来のEOG-WF閉鎖済み分母 **3 scored / 31 scientific STOP / 3 administrative exclusion** は不変。

## 結論：どこまで肯定的か

- **数理実装／反証可能性（確立）:** 観測positive、事前に宣言した固定source・候補有向グラフ・環境単位・step horizonから、地理／環境／障壁の**非支配的な必要緩和ベクトル集合**を求められる。有限breakpoint族は宣言入力に関して完全列挙でき、native EOG inverse reconstructionと独立したbounded directed BFSの全世界互換判定が一致。
- **自明でない構成例（合格）:** 同じ陽性を説明する3つの競合緩和がパレート前線に現れ、軸別最小値を単純連結した(0,0,0)は実行不能。新たなpositive Cが同一世界集合へ課されると必要地理緩和が変化。
- **生態データへの適用（探索的肯定）:** Åland Glanville 2007–2012（6年・1,814のrecorded zero→positive対象）で、起源候補・寄主スコア・許容例外数に応じて必要地理範囲が大きく変わる**条件付き幾何学的制約**を得た。**実際の分散距離・起源・原因を推定できたわけではない。**
- **未達:** 独立した未開封のsource→target movement・外部遺伝学的真の起源・独立holdoutによるPareto必要緩和の予測妥当性、自然の三軸（地理・環境・障壁）の因果分離、自然界への外挿。

証拠評価の記号：**T**＝有限集合定義/アルゴリズムから成立、**K**＝既知真値の非自明な構成・数量、**E**＝実データの条件付き記述、**D**＝既開示結果の事後感度解析、**F**＝不支持/実行STOP。

## 1. Exact estimand と実装境界（T＋K）

凍結した候補有向グラフ `G`、固定source集合 `S`、observed positive `O`、最大グラフstep `H`、baseline `θ0=(r0,δ0,b0)` に対し、非hard edge `i→j` は地理 `d_geo<=r`、環境 `d_env<=δ`、障壁許可 `b_required<=b` を**全て**満たす時のみ通行可能とする。

```text
Compatible(θ):  全てのpositive O が「同じ宣言source S」から
                H directed steps 以内に到達可能

F*(G,S,O,H;θ0) = ParetoMin{
    (r-r0, δ-δ0, b-b0):
    θ>=θ0, Compatible(θ)=true
}
```

- **何が正確か:** その固定グラフ上で、edgeの可否が切り替わる全閾値（基準と全非hard edge requirement）を直積列挙し、支配されないcompatible点を返す。上限512世界を超える入力はfail closed。候補ルートは**実現可能性のwitness**、過去の移動ではない。
- **何を新数学としないか:** Pareto dominance、critical threshold、directed BFS、minimax/least-cost、falsification frontierは一般的先行あり。EOGの貢献は**observed occurrence conditioned inverse estimand**、単位別の仮定・source・候補グラフ・監査の組合せ。
- **三軸の混同禁止:** 任意の重み `αd_geo+βd_env+γbarrier` で3種類の説明を1つの最適値へ潰さない。異なる軸の個別minimumを取っても同時実行可能性は保証されない。
- **無解の意味:** `no_feasible_world_within_declared_graph_and_step_limit` はグラフ・source・Hの下でのSTOP。自然界で絶対不可能とは言わない。
- **時間の意味:** `H` は**グラフhop数**であり、年数・世代数ではない。既存 `minimum_temporal_relaxation_frontier` は凍結した時系列適合世界をParetoフィルタできるが、それ自体が移動時刻や真の歴史を復元するわけではない。

実装：[finite-world core](../../src/eog/v2/world_reconstruction.py)、[temporal variant](../../src/eog/v2/temporal_relaxation.py)、[occurrence-to-graph benchmark](../../benchmarks/occurrence_conditioned_minrelax_v1.py)、[original pre-score protocol](../../validation/occurrence_conditioned_minrelax_v1/protocol_v1.json)。

## 2. 既知真値で新しく検証できた部分（K＋T）

凍結baseline：地理10 km、環境許容量1 feature unit、緩和可能barrier=0、source A、observed positives A/B、最長3 hop。

| 宣言された代替route | 必要な緩和ベクトル (Δgeo km, Δenv unit, Δbarrier) | 解釈 |
| --- | --- | --- |
| A→X→B | **(0,1,0)** | 環境的な遷移許容量を拡大する説明 |
| A→B | **(20,0,0)** | 大きな単一地理gapを許す説明 |
| A→Y→B | **(0,0,1)** | relaxableな障壁permissionを変更する説明 |

**原典テスト:** 8 breakpoint worldsのうち**7 compatible**、3解がすべて非支配、座標別最小(0,0,0)は共同では不可能。別のpositive C（edge A→Cに15 km必要）を**既存同一グラフ上で追加**すると、12 worldsのcompatibleが**10→7**へ縮小し、frontierは `(20,0,0), (5,1,0), (5,0,1)` に変化。hard-unavailable edgeだけでは**0 compatible**で正しいSTOP。

**本監査の独立再計算:** 凍結protocol JSONを読み、別のJavaScript BFS＋全edge breakpoint直積＋Pareto支配計算で8/7と12/10→7、両frontierを独立確認済み。オリジナル全Python/GitHub Actionsを再実行したわけではない。原典：[benchmark result and scientific boundaries](../occurrence_conditioned_minrelax_v1.md)、[test assertions](../../tests/test_occurrence_conditioned_minrelax_v1.py)。

**数学的な肯定の範囲:** 「固定された候補世界内で、3種類の代替説明が成立し、新しい陽性が必要仮定を狭める」。**生態的に三機構が存在する頻度、実際にどのrouteを通ったか**はこの実験からは出ない。

## 3. Glanville real source：全記録の必要半径は尾部に依存（E＋D）

`S_t` は前年記録陽性パッチ、`T_t` は前年recorded zero→当年recorded positive、`δ` は前年の**ordinal Plantago/Veronica gap**（0–3、固定スコア）、`d(i,j)` は投影座標上の距離（km）。

```text
d_i(δ,S_t) = min{d(i,j): j∈S_t, two_host_gap(i,j)<=δ}
r_0(δ,t) = max_{i∈T_t} d_i

r_k(δ,t) = 最小半径 r で、
    少なくとも |T_t|−k 個のpositive targetsについて
    d_i(δ,S_t)<=r が成り立つもの。
```

候補sourceが存在しない場合 `d_i=+∞` と考え、全部説明する `r_0` は**non-estimable**にする（ゼロ・生態的不可能とは扱わない）。`r_k` は有限距離が十分にあれば上から`k`個の最大必要距離を許容した順序統計量となる。**kを増やすほどr_kが小さくなることはT（自明）**、その**実際の減少量はE（条件付き実測データ記述）**。

**前年source、δ=3（寄主スコアを制限しない）**：

| 年 | positive targets | 全件 `r0` (km) | 最大5%未説明 `r5%` (km) | 観測された減少 |
| --- | ---: | ---: | ---: | ---: |
| 2007 | 349 | 4.443 | 2.296 | 48.3% |
| 2008 | 157 | 2.680 | 1.209 | 54.9% |
| 2009 | 285 | 5.953 | 2.049 | 65.6% |
| 2010 | 102 | 3.310 | 1.300 | 60.7% |
| 2011 | 521 | 8.050 | 2.533 | 68.5% |
| 2012 | 400 | 5.115 | 2.109 | 58.8% |

**追加境界:**
- 主に`δ=1,3`の24 year×source-policy×host-panelでは、**1 positiveのみ**未説明にすると厳密最大半径が25%以上減るケースは**3/24**。ゆえに「1つの極端地点に全て引っ張られる」は不支持。
- strict `δ=0` は**6/12** year×source-policyでhost-identical eligible sourceが無く非推定可能。1%未説明許容で**2/6**、5%許容で**6/6**が有限へ。これは記録の削除でも誤検出判定でもない。
- `δ=3`で前年のみsource集合を過去2年へ広げると、厳密半径は**4/6年で縮小、2/6年で同じ**。source集合を広げれば最小距離が悪化しないのはT。**どの年でどれくらい変わるか**はE。
- 2019年original patch X/YのEPSG3067座標は**km単位**。2017年遺伝表の座標は**m単位**。当初のCRS数値不一致STOPを保持し、単位変換のみ修正して得た初の有効12/12年×source-policyパネル。再解析は探索的・既開示後。

出典：[real-source conditional minrelax](../glanville_minrelax_empirical_unitfix_v2_result.md)、[k-exception sensitivity](../glanville_minrelax_exception_budget_v1_result.md)、[frozen source aggregate](../../validation/glanville_minrelax_empirical_unitfix_v2/frozen_aggregate_summary_v2.json)、[exception aggregate](../../validation/glanville_minrelax_exception_budget_v1/frozen_primary_aggregate_summary_v1.json)。

## 4. 起源の不確実性は何を壊すか（E＋D、真の起源ではない）

**Glanville latent-source sensitivity:** `1814` positive transitionsのうち、r=2 km、δ=3で、前年記録陽性sourceによる説明は**1708**。前年記録ゼロの候補を、既に見たtarget地点に有利に1年あたり10箇所ずつ選ぶと**1800**まで説明可能。追加92件は**仮想源を使う説明能力の上限に近い反実仮想**であり、92件の見逃し発見ではない。前年ゼロのうちt−2陽性sourceを候補に制限すれば、同じ条件で**1756**にとどまる。高密度許容/見逃し率の推定値はない。[latent-source audit](../glanville_latent_source_audit_v1_result.md)

**Specific origin vs existential support:** publisher-identical DiLeo 2022 genetic family fileから、同一Åland対象で厳密に照合できたものは**163 assignment rows、100 distinct target patch-years**（元のEOG対象2008–2012は**1465**）。r=2 km、δ=1では、任意の前年sourceで説明可能なtargetは**91/100**、特定の遺伝的**推定**起源で少なくとも一つ説明可能なのは**50/100**。r=5 km、δ=3では**100/100対93/100**。前者が後者以上になることは候補集合の包含から**T**。その差を「EOGが実際の起源を誤予測」とみなすのも不正。[genetic origin host-world v2](../glanville_genetic_host_world_v2_result.md)

**条件付きsource pairingの独立性の程度:** Genetically assigned origin labelsを同じ年内で組み替える1,999回の帰無に比べ、実際の割当源-目的地は`mean median log(1+km)`が**0.8552 vs 1.5806、片側p=0.0005**（5/5年で近い）。二寄主ordinal gapは**1.320 vs 1.459、片側p=0.030**だが、地理距離をそろえた候補源との比較では**割当源のhost gap優越は見られない**（matched差 +0.0556/+0.0681、二つの候補源定義）。これは**選ばれた遺伝割当源同士の条件付きペアリングの性質**であり、真の飛翔記録・元のGENECLASS2完全reference roster・実際のsource choice因果効果ではない。[conditional pairing v3](../glanville_conditional_pairing_null_v3_result.md)

**結論:** 最小制約緩和`r*`は「少なくともひとつ候補sourceが説明できる」存在量。実際の起源を当てる estimand ではない。現状のÅland遺伝資料もそのsource truthを認証していない。source仮定の不確実性と検出過程を外すと、`r*`を分散距離の生物学的下限と呼ぶのは過剰。

## 5. 次に証明・検証すべきこと（現在の主線を増やしすぎない）

1. **数学の追加証明ではなくsource-uncertaintyの扱い:** 固定sourceなら完全breakpoint frontier。代替source集合を入れる場合は`sourceごとに別のfrontier`と共通部分・和を区別し、少なくとも1世界で実行可能（existential）と全適格源仮説で実行可能（universal）を混同しない。source政策がpositive集合とともに変われば、fixed-source単調性を無断適用しない。
2. **前向きなecological estimandを1つだけ固定:** holdoutのpositive遷移先を開く前に、source候補の独立記録／検出努力／候補patch graph／host尺度／時点／例外budgetを凍結し、`Pareto relaxationの予測する必要条件`が独立のsource→target移動・遺伝出自等と整合するか評価。実測origin confidenceを無視しない。
3. **一枚図に必要な最低限の比較:** `F*(Δgeo,Δenv,Δbarrier)`、実データ`r0`と`r5%`、代替起源ロスターでの`r*`、genetic source pairingのconditional nullを**別の推定対象**として並べる。後者を前者の独立検証として図に混ぜない。

**Novelty boundary:** graph connectivity/percolation、Pareto fronts、minimum relaxation/breakdown frontierの数学的アルゴリズムは既存。現状のEOGの科学的貢献は、**観測positiveに条件付け、複数の生態学的必要仮定を非混合のPareto集合として監査可能に返し、`unresolved`と`no feasible candidate world`を条件付きで正しく表現する推定契約**。自然界における実際の緩和軸・因果を発見したとする主張は未証明。

**本監査の再検証:** (1) 凍結protocolから独立JavaScript有限breakpoint+BFS+Paretoの全組合せを再計算して native期待値 **8/7、12/10→7** と各frontierを照合、(2) Glanvilleの公刊原データ由来の**凍結集計JSON**と結果報告を照合、(3) 原典コード・tests・PR #699–#701/#707–#708の既存記録を確認。**実際のÅland rawデータや12年分の全transitionを本監査の実行環境で再得点していない。**
