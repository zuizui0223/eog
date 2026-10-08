# Helgeland：物理ヘッダー取得用の独立ローカル検証ゲート（提案）

**現時点の観測状態は依然 `HOLD_PHYSICAL_HEADERS_NOT_ATTESTED` です。** このPRは取得済みの本物のヘッダーや新しい生態学的結果を含みません。実ソースのダウンロードも自動では行いません。

## 先行する境界

- PR #620：Dryadの2つの公開データセットについて、公開バージョン・10ファイルの名前・サイズ・**ソース登録**SHA-256を凍結済み。
- PR #621：2025年の `LRS.txt` / `ARS_Survival.txt` と2024年の `GGAM_data_GeneticArchitecture.txt` / `SNPpedigree_GeneticArchitecture.txt` について、列名の照合契約と、結果に触れないHOLD判定をmainへ統合済み。
- **本PR**：元ファイルが外部で別途取得された後だけ、ローカル4ファイルの**全バイトをSHA-256用の不透明なバイト列として読み**、Dryad側の登録SHA-256・サイズと照合する。意味のある文字列として読むのは**それぞれの物理的な先頭1行だけ**。行データをパースしない。

## なぜ全ファイルSHA-256を検査するか

見かけが同じ列名の偽のファイルを、Dryad上の正規ファイルと誤認しないためです。ファイル全体をバイト単位で読み、公開元に登録されたSHA-256と照合します。**これはファイルバイトへのアクセスです**。ただし鳥の個体行・繁殖・生存・SNP値をレコードとしてデコード・分析することとは区別します。

このスクリプトにHTTPクライアント、APIトークン管理、ダウンロード機能、出力用の生物学的スコアはありません。実データをGitHubにコミットすることも認めません。

## ローカル構成

Gitリポジトリの外に、別途正規の公開版（2025 v2・2024 v3）から得られた4ファイルを配置：

```text
/private/helgeland-sources/
  fitness_2025/
    LRS.txt
    ARS_Survival.txt
  pedigree_2024/
    GGAM_data_GeneticArchitecture.txt
    SNPpedigree_GeneticArchitecture.txt
```

**ファイル拡張子からTAB等の区切り記号を推測しません。** 4ファイルとも事前に根拠を確認して区切りを宣言します。次はあくまでTABが正しいと確認できた**場合の例**であり、元ファイルの区切り記号が実際にTABであるという報告ではありません。

```bash
python scripts/extract_helgeland_verified_firstline_v1.py \
  --source-root /private/helgeland-sources \
  --delimiter fitness_2025/LRS.txt=TAB \
  --delimiter fitness_2025/ARS_Survival.txt=TAB \
  --delimiter pedigree_2024/GGAM_data_GeneticArchitecture.txt=TAB \
  --delimiter pedigree_2024/SNPpedigree_GeneticArchitecture.txt=TAB \
  --output build/helgeland.header-only.json \
  --receipt build/helgeland-firstline-receipt.json
```

ソースファイルのサイズ・全バイトハッシュ・厳密な列名・ヘッダー長・区切りを検査し、**4ファイルすべて一致した場合のみ**2つのJSONを作成する。1ファイルでも不一致ならエラーで止まり、証拠ファイルを新規出力しない。

`*.header-only.json` は既存の `qualify_helgeland_header_attestations_v1.py` に入力可能。最も強い判定でも `HEADER_NAMES_ATTESTED_KEYS_STILL_UNJOINED` に留まり、次は **2024/2025年の個体ID同一性・島コード辞書・出生地推定の誤差・利用可能時点・島ごとの努力量** を独立に検証する。

## 認めない主張

- 先頭行しかデコードしなくても、ソース全体のバイトはSHA-256計算のために読みます。したがって「source bytes unaccessed」は主張しません。
- Dryadの登録SHA-256との一致は**データ元のバージョン同一性**を補強するだけであり、2024年・2025年の個体が結合可能なことや同じ島コード体系を使うことを示しません。
- 単独の `natal.island → adult.island` は初回の島への定着源の直接証明ではありません。
- 将来の観測情報を使う後ろ向き起源復元を、将来時点で利用可能な予測因子へ自動変換しません。
- 実際のヘッダー・ハッシュの照合を完了する前に、生態学的な新結果・EOG-WFの新endpoint・論文の追加を主張しません。

## 出力保護（2026-10-08追加）

- `--output` と `--receipt` は必ず異なる**未作成のファイルパス**を指定する。既存のJSONへの上書きは禁止し、再実行時は別名にする。
- 元ファイルのディレクトリと、そのsymlink aliasの下へ結果を書けない。元ファイルが置かれるディレクトリ経路のsymlinkも拒否する。
- 検証完了後の書込みはexclusive creationで実行し、例外で作成途中の新しい出力が残らないようにする。

## CI

`pytest tests/test_helgeland_verified_firstline_v1.py` では**模擬ヘッダーと模擬行データのみ**を利用し、サイズ改変・等長バイト改変・シンボリックリンク・列名欠損・区切りの誤宣言などを検証します。実際の鳥・生存・SNPレコードはGitHub Actionsへ持ち込みません。
