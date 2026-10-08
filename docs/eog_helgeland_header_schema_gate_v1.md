# Helgeland：実ファイルを開く前のヘッダー・ID照合契約 v1

**状態：`HOLD_PHYSICAL_HEADERS_NOT_ATTESTED`。** 2025年の出生島・繁殖・生存データと2024年の遺伝・血統データについて、公開Dryadの**版・ファイルID・サイズ・登録SHA-256**はすでに凍結している。一方、**実ファイルの先頭行そのものは未取得であり、個体・島のID対応も未確定**。

この段階の目的は、生物学的な成果を増やすことではなく、最初のヘッダーを安全に受け取ったとき、何を根拠に適格性判定するかを事前に固定すること。

## 必要な4ファイルと公開READMEでの役割

| 元データ | 対象ファイル | 文字列として必要な列名（公開READMEから） |
|---|---|---|
| 2025 v2 | `LRS.txt` | `ID`, `natal.island`, `adult.island`, `year`, `LRS` |
| 2025 v2 | `ARS_Survival.txt` | `ID`, `obs.year`, `natal.island`, `recruits`, `survival` |
| 2024 v3 | `GGAM_data_GeneticArchitecture.txt` | `ID`, `natal.island`, `hatch.year`, `Dispersal.status` |
| 2024 v3 | `SNPpedigree_GeneticArchitecture.txt` | `individual`, `dam`, `sire` |

上表は**公開README上の変数定義**であり、実ファイルの物理ヘッダーを確認したという意味ではない。区切り文字もまだ分からないため、**TSVと断定せず**、ヘッダーを独立に抽出した際にTAB/COMMA/SEMICOLON/WHITESPACEのどれかを明示する。

## 識別できることとできないこと

1. **文字列の一致**：ヘッダーの `ID` が存在するか確認できる。だが2024年の `ID` と2025年の `ID` が同じ個体を表すかは、列名だけでは証明できない。
2. **列名の別名**：`SNPpedigree` の `individual` を、前提なく `ID` に自動変換しない。現時点では結合候補に留める。
3. **島コード**：`natal.island` が両表にあっても、同じ島コード辞書か不明。島コード27の原文表記 `Hestmannøly` を推測で修正しない。
4. **生物学的結果**：方向付き出生分散の元になる個体行、繁殖・生存、遺伝情報、初回定着、供給源喪失はすべて未評価。
5. **時間的な独立性**：遺伝的起源推定が未来の再捕獲情報を使用したか不明。将来予測と、後ろ向きの出自復元を混同しない。

## 実行可能な監査

`scripts/qualify_helgeland_header_attestations_v1.py` は**生物データ本体を読む機能を持たない**。必要に応じて、別途取得された**最初のヘッダー行だけ**を構造化した小さなJSON（外部抽出証跡・固定ファイルID・版ID付き）を入力する。現在はその証跡が存在しないので、引数なしで実行すると必ず `HOLD_PHYSICAL_HEADERS_NOT_ATTESTED` を記録する。

```bash
python -m pytest -q tests/test_helgeland_header_schema_gate_v1.py

python scripts/qualify_helgeland_header_attestations_v1.py \
  --output build/helgeland-header-schema-hold-v1.json
```

後に本物のヘッダー証跡を入力して4件の列名が一致したとしても、判定は `HEADER_NAMES_ATTESTED_KEYS_STILL_UNJOINED` に留める。これは**ソースの実バイトを別途ハッシュ検証したことでも、個体・島IDの値を照合したことでもない**。このスクリプトは外部が提示したヘッダー証跡の真正性を暗号学的に証明するものではない。

**Dryad公開APIの版・ファイル一覧だけでは物理ヘッダーを返さない。** [公式REST API説明](https://github.com/datadryad/dryad-app/blob/main/documentation/apis/README.md)。ファイル本体の取得には別途認証が必要となる環境もあるため、観測値を不用意に取得しないよう、**この監査にはダウンロード・HTTP Range取得機能を入れていない**。

## 次に解決すべき点

4ファイルのヘッダー証跡、2024・2025年の個体・島IDの対応を観測値抜きで確認する証拠、出生島の観測方法と誤差を得てから、初めて*観測過程の適格性*を再評価する。生態学的な差・因果効果・モデル精度のスコア計算へは進まない。

**科学的結論を更新しない。** 仮想世界v18–v23の凍結結果、EOG-WFの3/31/3分母、旧Glanvilleの結果、Helgelandの `HOLD_DIRECTIONAL_INDIVIDUAL_PROXY_ONLY` をすべて維持する。

契約：`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_header_schema_contract_v1.json`
