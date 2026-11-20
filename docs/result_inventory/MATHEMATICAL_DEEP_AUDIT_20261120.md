# EOG数理・既知真値成果の再監査（2026-11-20）

**基準main:** `a56d582d5960af4c11fd8714e391a20b547919c2`。**成果物:** 数理結果の根拠・強さ・条件・反証の再分類であり、新しい生態学的得点・新規endpoint・再調整を含まない。  
**元台帳:** [数理一覧](MATHEMATICAL_AND_KNOWN_TRUTH.md)、[数理/実証の区分](README.md)。この文書は既存の凍結プロトコル・結果・投稿主線を置換しない。

## 0. 「SUPPORTED」の読み替え

| 区分 | 成果の意味 | それだけでは言えないこと |
| --- | --- | --- |
| **T（定理・恒等式）** | 宣言された有限集合、観測契約、同じ世界集合について必ず成立する性質。テスト成功は**実装検査** | 新しい数学、生態学的普遍性、生成モデルによる独立支持 |
| **K（非自明なknown-truth結果）** | 事前凍結した生成系内で、符号・量・頻度・優劣などが実際に決まった結果 | 全自然系へその頻度を外挿、真の分散率/因果機構とすること |
| **X（構成的反例・例示）** | 特定条件下で「普遍的に成り立つ」という主張を破る、または可能性を示す | 自然系での頻度、指定の例以外での一般的優劣 |
| **D（事後診断・モデル依存）** | 既に開いた出力を再分類して制限を明確化した結果 | 独立した新しい事前仮説の支持 |
| **F（反証・STOP）** | 当初予測が外れた、効果量基準未達、時点漏洩が発覚、設計上利用不可 | 肯定的結論への付け替え |

**重要:** 既知真値の `0 violations` や `all hypotheses SUPPORTED` は、多くが T（契約検査）。Kの効果量を独立に確認したこととは分ける。**v1–v45は45件の独立生態学的再現ではない**。例えば v21–v26、v39–v45 は同じ768の源ネットワーク設計を再利用し、v10–v17は共通のtopology家族を再利用し、BAMの後続研究も同じ12系768候補を引き継いでいる。

## 1. 科学的に残すべき数理的肯定結果：研究優先度順

| 科学的な結果・推定対象 | 非自明な証拠（モデル内） | 成立条件／重要な反証 | 判定 |
| --- | --- | --- | --- |
| **① 機構が未同定でも反実仮想の結論を識別できる** | 12生成系/768 truth、完全現在Gで完全BAM状態同定 **25/768**、3解除の正確な応答同定 **174/768**、二値判断同定 **636/768**。機構未同定743の内 **149** は正確な3応答まで同一、**462** は応答地図が違っても二値判断は同一、**132** が二値判断まで不一致 | `G=A∩B∩M` で観測が完全、指定64候補世界・指定3つの理想化制約解除。**633等の数字は普遍的判定率ではない**。全分解へ拡大すると判定同定は激減（後述）。| **K + T** |
| **② 将来の状態は、完全な現在状態の関数とは限らない** | 2,592世界を使う未来の気候・生物・障壁変化では、**気候判断10 truth／障壁判断10 truth**が完全な現在A/B/M/τでも識別不能。気候の該当132未決定truthは1種類の潜在 `A_level` assayで分離できた | 将来の変化が「現在マスク」ではなく**現時点に現れないパラメータ**へ作用する場合。元の「A/B/M軸を現在のマスクから取り除く」反実仮想ではこの種類の潜在性は存在しない。| **K + X** |
| **③ 生態側×観測側の不確実性は必要証拠量に交互作用し得る** | 同一129現在G-fiber×3未来対象=**387**の有限問題で、両側拡張時の最小証拠量が各片側拡張より**厳密に大**となるのは **51/387**。生態世界拡張で初めて観測誤差較正が必要となるのは**9**。| 誤測定世界と観測行動は事前に列挙した決定論的有限モデル。**統計的交互作用や実測検出誤差を推定したのではない**。証拠量の単調性自体はT。| **K + T** |
| **④ 同じ最終分布は動的構造・局所損失応答を決定しない** | v10: A/B/M/G/点別scoreが全て同じ4グラフを**192/192**パネルで構成。14ノード時の平均重要ノード数はchain **12** vs star **0**、1ノード除去後の到達残存率はchain **0.538** vs star **1.000**。v12:同じ静的地図の**12 random topology**が144パネルで非同値となる | 静的状態から**遷移関係・方向・first-passage**を回復できるとは限らない、という構成的反例。グラフ差を実験者が作っており、自然での頻度は未検証。| **X + K** |
| **⑤ 同じ起源数でも配置がcoverageとinsuranceを逆方向に動かす** | v18:2起源の分散配置はcoverage **0.445** vs 集中 **0.404**、集中は最悪起源喪失後保持 **0.693** vs 分散 **0.264**、二方向トレードオフ **280/384**。2分散起源が3集中起源のcoverageを上回る事例 **225/384**。v20:起源数を元へ戻しても置換戦略のcoverageが異なる **718/768**、元のcoverageを超える例 **407/2304** | 既知の静的方向付きネットワークと、事前指定のsource-placement/insurance指標。**再colonization、保全成功確率、遺伝的founder**は推定していない。| **K** |
| **⑥ 最終occupancy・起源・到着年齢は異なる歴史の記憶媒体** | v21:同じ平衡occupancyを持つ768設計のうち**507**で最早到着起源ラベルが異なり、**552**で過渡occupancyが異なる。v23:時間occupancy単独で**579/768**、provenance単独**272/768**、併用**687/768**の歴史同定、なお**81**残留。v24:81残留の**45**で到達年齢差、v25:その45のうち固定lag2現在状態まで変わるのは**12**。v26:別の状態変換なら同じ45/45を区別 | 同じ三起源活性化履歴の有限生成系。**到来年齢に依存するstate mapは仮定**であり、実測成熟・適応・生存率は未検証。併用687と単独集合の単純和集合669との差 **18**は既存集計からの**事後算術導出（追加独立試験なし）**。| **K + D** |
| **⑦ 既知世界集合では、より少ない「問いに直結する証拠」が十分な場合がある** | v13でrandom 12-topology候補の完全同定に平均**3.264**の固定証拠が必要（v11の人工4グラフの1測定shortcutは非一般化）。v14の適応化でpairwise-relationのworst-case平均**2.986**、worst-case厳密節約 **262 row×target**。v9で現時点の世界数を**全く減らさない**バリア/解析規則の診断が将来証明寿命を伸ばす例 **205/272**。| adaptive≦nonadaptiveやtargetを粗くすれば必要証拠が増えないという不等式自体はT。節約の**量、頻度、どの質問が優先**はK。cost世界は合成仮定、自然の調査費ではない。| **K + T** |
| **⑧ 変化後の地図が未同定でも幾何学的方向が同定可能** | 完全現在Gに対応する**129 fiber**でA/B/M解除後の正確な地図同定は**110/96/95**、90%点間spanの方向同定は**119/124/121**。地図未同定・span方向同定は**9/28/26**。M解除では**5 fiber**で正負両方のspan応答が許容される | この129は独立の自然観測ではなく12系の完備G同値集合。多くの同定方向は**ゼロ変化**。q90 pairwise spanは集合包含に対して**単調でない**ので正負両応答は数理的にあり得る（§4）。| **K + X** |
| **⑨ 分析者が選ぶ環境→辺の規則が生態学的符号を反転し得る** | v3:384生成景観、平均**36.6%**の局所可能nodeの到達判定が解析規則依存。環境自己相関の関係はq70 ruleで**−0.180**、固定raw 0.5 ruleで**+0.634**、SD ruleで**+0.213**。一方、障壁密度の効果は3規則で正 | **同じ潜在環境**を使い、解析表現だけを変えた有限実験。法則的な普遍相関は成立しない。v2の事前G2反証を**「復活した」ことにしない**。| **K + F** |

原典：
1. [BAM counterfactual](../bam_counterfactual_identifiability_v1_result.md), [target-identifiability theory](../bam_target_identifiability_theory_v1.md)
2. [Future target evidence](../bam_future_target_evidence_v1_result.md), [target quotient](../bam_target_quotient_v1.md)
3. [Joint uncertainty](../bam_joint_uncertainty_lattice_v1_result.md), [joint theory](../bam_joint_uncertainty_theory_v1.md)
4. [Topology v10](../eog_original_idea_marginal_topology_v10_result.md), [v12](../eog_original_idea_random_topology_v12_result.md)
5. [Sources v18](../eog_original_idea_source_placement_v18_result.md), [v20](../eog_original_idea_source_turnover_v20_result.md)
6. [History v21](../eog_original_idea_source_history_memory_v21_result.md), [v23](../eog_original_idea_provenance_observability_v23_result.md), [v25](../eog_original_idea_age_dependent_present_state_v25_result.md), [v26](../eog_original_idea_history_to_state_process_family_v26_result.md)
7. [Adaptive v14](../eog_original_idea_random_relational_v14_result.md), [future-proof v9](../eog_original_idea_future_proof_evidence_v9_result.md)
8. [BAM geometry response envelopes](../bam_geometry_response_envelopes_v1.md)
9. [Analyst worlds v3](../eog_original_idea_analyst_worlds_v3_result.md).

## 2. 重要な厳密数理：**新数学ではない**が、EOGの正しいclaim契約を決める

### T1 — 正の出現記録で排除できる条件

真の出現正集合を `G*`、世界 `w` の許容集合を `G_w` とすると、正情報 `O⊆G*` に対し、世界が残るのは `O⊆G_w` のとき。もし `G*⊆G_w` の過剰に許容的な偽世界があるなら、**正記録をいくら増やしても区別不能**。v1の64/64、12系の768/768ではそのような世界が残り、真のBAM状態の陽性のみ一意同定は **0/768**。**0/768は一般理論の帰結ではなく、この生成候補家族がその構造を持っていた結果**。 [witness theorem](../known_truth_biogeography_result_v1.md), [BAM 12 systems](../../validation/known_truth_bam_v3/result_summary_v3.json)

### T2 — 誰の「同定」かを固定する

証拠と適合する世界集合を `S(e)`、関心対象を `T(w)` とすると、`T` の同定とは `|{T(w): w∈S(e)}|=1`。世界IDの単一性は必要ではない。現在状態 `C(w)` が未来変化対象 `T` を決めるとは限らない：`C(w_1)=C(w_2)` なのに `T(w_1)≠T(w_2)` の dormant-parameter 対照が [Future target evidence](../bam_future_target_evidence_v1_result.md) に存在する。**現在の軸を単純に解除する場合のみ**、現在のA/B/Mマスクから解除後mapが決定する。

### T3 — 世界拡張と「頑健」の意味

同じ観測・同じ適合規則で `W_0⊆W_1` なら生存世界 `S_0⊆S_1`。可能な到達nodeの和集合は拡大しかできず、除外は縮小しかできない。robustに到達可能な集合（積集合）も縮小しかできない。**v6実際の保持**：到達可能 **96.1%**、不可能 **64.8%**。**v7理由**：追加されたcompatible same-source worldsはpermissive **1,583**、restrictive **151**、equivalent **1,315**、incomparable **82**。permissiveは除外を壊しやすく、restrictiveはrobust reachabilityを壊しやすい。**「不可能性は可能性より頑健」ではない**。[v6](../eog_original_idea_world_universe_v6_result.md), [v7](../eog_original_idea_expansion_direction_v7_result.md), [v8](../eog_original_idea_world_growth_v8_result.md)

### T4 — 判定同定率は宣言世界の外まで保証しない

BAM3つのrelease判断が同定された件数は、64世界 → 2,592世界 → 全BAM同一現在G分解closureで、

| release | 64世界 | 2,592世界 | 無制限同一G分解 |
| --- | ---: | ---: | ---: |
| A | 652 | 646 | **34** |
| B | 705 | 693 | **34** |
| M | 732 | 691 | **34** |

全closureで残る34は外部nodeを持たない `G=X` の自明ケース。現実的2,592候補と理論的に全て許す無制限候補は**生物学的同じ問いではない**。一方「同定できた」は世界の縁に依存し、隠してはならない。全closureではproper `G⊊X` について、単一軸解除で増加する分解・しない分解を構成できる。限界に近いことを数で示す必要があり、無制限ハミング距離1の反例を「現実でもすぐ壊れる」とは言えない。[ecological margin](../bam_ecological_expansion_margin_v1_result.md), [completion margin](../bam_decision_robustness_margin_v1_result.md), [nested-world theory](../bam_nested_universe_target_identifiability_v1.md)

### T5 — 証拠設計の単調性と、実際の節約は別

十分な証拠集合を全て許すなら適応的方策は固定方策を模倣できるので、最適worst-caseコストは適応型が固定型を上回らない。目標を粗くすれば区別すべき世界の対が減るため最小行動数は増えない。**これらは証明すべき新規生態学的発見ではない**。v14の**262**厳密節約、v15のcost変更でfirst-actionが**1,023**変化、v16の**864/864**ゼロ-regret無し、v17のone-bit cost diagnosticで完璧情報価値を**783/864**回収、という頻度・量は**固定した計算問題に対する非自明な数値結果**。[v14](../eog_original_idea_random_relational_v14_result.md), [v15](../eog_original_idea_cost_aware_adaptive_v15_result.md), [v16](../eog_original_idea_cost_uncertain_policy_v16_result.md), [v17](../eog_original_idea_cost_information_value_v17_result.md)

## 3. 最も重要な**例外**：観測positiveをsourceへ再定義すると、世界単調性は使えない

**現在のmainと区別：** 次は **未マージPR #697・#698** の有限グラフ診断であり、本監査では抽象グラフ全列挙を別実装のJavaScriptで再計算した。PR本体のGitHub Actionsとコード変更をmainへ昇格させたわけではない。

3ノードA/B/C、方向付き自己ループなし、6本の可能edge `2^6=64` グラフ、移動は1-step。

- **固定source A**: positives `{A,B,C}` に適合するグラフ **16**。Cを観測集合から外した `{A,B}` は **32**。元集合の16は全部残り、追加16：**集合包含が成立**。
- **self-excluded peer-source**: positives ABC の各点が「他のpositiveのいずれかから到達」を要すると **27** グラフ。positives AB に減らすと **16**。共通 **12**、元から**15喪失**、新しく**4獲得**：**どちらの適合グラフ集合も他方の部分集合でない**。
- 同じ3候補からsourceを未指定にすると、64グラフ×3源候補に対し、compatible rule/source **48組**、少なくとも1源が成立するグラフは**37**、全3源が成立するグラフは**1**（完全有向グラフ）。
- A→B, B→A の2方向の不在を**外部から本当に構造的に確認した**と仮定すると、候補16グラフ中適合は**4**、候補源は**Cのみ**。単なる非検出からedge不在を推定してはならない。

**数理的理由:** fixed-sourceでは `S(O)={w:O⊆R_w(source A)}` でforward modelが固定。一方peer-sourceでは `O` の変更と同時に**sourceとして使えるノード集合そのものも変更**する。これは「同じモデルへ証拠を追加」の条件を満たさない。

**独立監査結果（全64 edge maskのJavaScript exact enumeration）:** `fixedFull=16, fixedGate=32, peerFull=27, peerGate=16, peerIntersection=12, peerLost=15, peerGained=4, sourceConditionalGraphBins=[27,27,9,1], 2-nonedgeCompatible=4`。すべてPR記載算術と一致。**データから自然の分散源を同定したわけではない**。

PR証拠：[#697](https://github.com/zuizui0223/eog/pull/697), [#698](https://github.com/zuizui0223/eog/pull/698)。

## 4. 元のEOG spanに関する重要な注意（独立算術確認）

EOGの `span` は（共有参照上の）**全ての正の点間距離の90%分位数**であり、convex hullの包含体積ではない。

独立した1次元反例（通常の線形補間quantile）：

- 小集合 `G={0,10}` の正の点間距離は `{10}`、`span90(G)=10`。
- より大きい集合 `H={0,1,2,...,10}`（`G⊂H`）では、55点間距離の `span90(H)=7.6`。
- hullの範囲はどちらも `[0,10]`、直径はどちらも10。

従って**到達分布が包含として拡張しても、90%点間距離spanは縮み得る**。BAM×geometryの[実行結果](../bam_geometry_response_envelopes_v1.md)では、M解除の同一現在G-fiber内でspan差が**−0.20417〜+0.51946**の候補worldが同居するが、hull areaはどれも増大する事例がある。これはspanの欠陥ではなく、**推定対象がextent（外縁）か、点群分散（質量配置込み）か**の違いを示す。

EOGの元の環境幾何学層を将来の反実仮想へつなぐなら、**q90 span、hull、centroid dispersion、geographic componentsを別々に報告**する。1つの「niche expansion」へ統合しない。

## 5. 肯定として昇格しないもの（当初仮説を含む）

| 結果 | 何が成立しなかったか／残す限界 |
| --- | --- |
| 旧v2 `BAM validated` | 義務的partnerが21/21 nodesに存在し、B=partnerがB=noneと同値。A-only witness=0。v2.1で軸活性化を修正してからの結果だけを総合BAMの土台にする。[v2](../known_truth_bam_v2_result.md), [v2.1](../known_truth_bam_v2_1_result.md) |
| BAM v3「Mが常に最後の識別ボトルネック」 | **G2 REFUTED**。少なくとも1生成系ではM直接証拠の前に100%同定。[v3 frozen JSON](../../validation/known_truth_bam_v3/result_summary_v3.json) |
| v6「robust impossibilityはrobust possibilityより持続する」 | **反証**、保持64.8% vs 96.1%。方向別世界拡張を条件にする。[v6](../eog_original_idea_world_universe_v6_result.md) |
| v11の「1 relational actionが十分」 | 人工4 archetypeのみ。random 12 topologyでは最小平均3.264、3〜4測定必要。[v13](../eog_original_idea_random_relational_v13_result.md) |
| v2の環境自己相関→barrier予測G2 | 方向が反転。代替analyst ruleで符号も変化した。**符号の普遍法則ではない**。[v2](../eog_original_idea_virtual_worlds_v2_result.md), [v3](../eog_original_idea_analyst_worlds_v3_result.md) |
| v16の共通cost policy | **864/864**でoracleに対するstrict regretが残る。world非依存の万能行動順位は未成立。[v16](../eog_original_idea_cost_uncertain_policy_v16_result.md) |
| 確率観測を何回でも繰り返せば厳密同定可能 | full-support誤差チャネルなら有限回でsupport-disjoint証明は **0/67**。反復回数の5%判定は**Bhattacharyya上界**の計算であり絶対識別や野外保証ではない。calibration費用節約仮説も **0/67**。[stochastic assay](../bam_stochastic_assay_risk_v1_result.md) |
| v40 confluence priorityが実用的に優越 | 64 random seedとの平均差 **+0.008560bit** は事前最小実質差 **+0.020bit** 未満。64 seedは独立生態系ではない。[v40](../eog_provenance_placement_multiseed_v40.md) |
| v43の12/12歴史alias解消を前向き予測とする | 元の観測庫が対象時刻の**後**を含んだため**retrospective**。v44では真のcutoff `t=2→5` に修正し、未来状態が未同定の**126/768**のうち追加source情報が正なのは **8/126**、平均情報**0.020563bit**（正解確率利得**0.012534**）。実環境のforecast成否ではない。[v43](../eog_minimal_temporal_evidence_v43.md), [v44](../eog_original_idea_asof_time_provenance_v44.md) |
| v45のsource opportunity / target diagnosticity | v44既開示データに基づく**事後再分類**。random policyでpotentially measurable **105/126**のうちtarget-informative **6**、その差**99**は「観測できそう」と「その対象に有用」の非同値例。新規事前仮説の独立検証ではない。[v45](../eog_source_opportunity_vs_target_diagnosticity_v45.md) |
| EOGが既存のグラフ、set cover、robust optimization、partial identificationを数学的に発明 | **支持しない**。定理は既存の集合・グラフ・情報理論の利用。新規性候補は**生物地理的な観測契約・推定対象の分離・外部実証への接続**にある。 |

## 6. 本監査で実施した検証と未実施の検証

**実施:**
- GitHub現行main、各原典`docs/*_result.md`、対応する凍結`validation/*/result*.json`、関連する実装`src/eog/v2/world_reconstruction.py`、`world_forecast.py`、テストのassertを読んだ。
- BAM 768の分母整合: `25+743=768`, `149+462+132=743`, `636+132=768`、世界拡張での単調な減少`A:652≥646≥34; B:705≥693≥34; M:732≥691≥34`を確認。
- v23独立算術: `occupancy ∩ provenance`で独立同定可能な設計は`579−397=182`、少なくともどちらか単独で可能なものは`579+90=669`、併用`687`ゆえ**18**の「単独どちらでも同定できず、組合せで同定」ケースがある。事後の算術再分類でありpredeclared独立結果ではない。
- 抽象3ノード・全64方向グラフを**独立JavaScriptコードで完全列挙**し、未マージPR #697/#698の固定源・peer-source・2方向edge不在条件の全件数が一致。
- `span90`の包含非単調反例を独立計算（2点対11点）で確認。

**未実施:**
- 12生成系/768 BAM worlds・129 fibers・768 source歴史設計について、GitHub Actions由来全行を本監査環境で再計算したとは**主張しない**。これらは凍結集計・原典コード・既存CI証跡の内容照合。
- 数理の**世界初・出版上の新規性**を体系的な網羅文献調査で証明したわけではない。
- 新しいfield dataの解析、EOG-WF第4endpoint、実験介入の因果効果推定は**行っていない**。

## 7. 研究として残す主線

**数理論文の中心命題候補:**

> **現在の分布から生成機構は同定できないことが多い。しかし、反実仮想・動的到達・幾何学的応答の「どの問い」がその不確実性を超えて同定できるかは、世界集合・観測過程・推定対象を宣言すれば厳密に判定できる。**

これを次の3つの独立した検証課題に絞る。

1. **Target-specific identifiabilityの非自明性**：現在G→BAM機構→将来ターゲットの同値類を競合モデルで検証（数理として最有力）。世界集合拡大時にいつ判断が崩れるか、非現実的な全closureと生態学的な局所拡張の両方を明示する。
2. **Distributional history→present-state memory**：同じ最終分布の異なる履歴が、どの実測state（相対構成・優占度・生残等）へ残るかを**独立実験**に接続する。これは数理単体では歴史の存在可能性を示す反例止まり。実験の結果・限界は[実証台帳](EMPIRICAL_RESULTS.md)参照。
3. **Observation design under joint uncertainty**：何を観測すれば未来の判断の同値類を分割できるかをexactに示し、cost・誤検出・source不確実性を明示する。最小assay数の成果を実測可能な動作に移すためには外部校正と独立holdoutが必要。

**後続ではないもの:** 同じ生成系を増やして「45番目の支持された仮説」を作ること、定理を一般生態法則として宣伝すること、凍結済み3 EOG-WF endpointを再開すること。