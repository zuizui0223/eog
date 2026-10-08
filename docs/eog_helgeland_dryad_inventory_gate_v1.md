# Helgeland公開Dryad API監査：ファイル版・一覧のみ（v1）

**状態：SOURCE_METADATA_ONLY。** 本監査は2025年のイエスズメ加入・生存表と、2024年の血統・遺伝データの公開アーカイブについて、Dryadの**公開JSONメタデータだけ**を取得する。生存・繁殖・移入元・遺伝子型・血統の**レコード値は一切開かない**。

親となる適格性判定：`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_directional_origin_preflight_v1.json`。その結論 `HOLD_DIRECTIONAL_INDIVIDUAL_PROXY_ONLY` を上書きしない。

## 目的と入力

公開アーカイブ版と実データの構造を混同しない。Dryadの[公式API仕様](https://github.com/datadryad/dryad-app/blob/main/documentation/apis/README.md)は、DOIからデータセットの公開メタデータ、公開版へのリンク、版別ファイル一覧を取得できる。

対象：
- 2025年の出生島・繁殖／生存記録：[10.5061/dryad.qfttdz0sx](https://doi.org/10.5061/dryad.qfttdz0sx)
- 2024年のSNP血統・関連データ：[10.5061/dryad.80gb5mkxh](https://doi.org/10.5061/dryad.80gb5mkxh)

実際にアクセスを許すURLは、これらDOIのデータセットメタデータと、そこから取得した `/api/v2/versions/{versionId}/files` の**JSON一覧**だけ。 `/download` や個別ファイル内容、個体データ表へのアクセスはスクリプトで禁止している。

## 記録するもの・記録しないもの

| 対象 | この段階の取扱い |
|---|---|
| 公開DOI・Dryad内部dataset ID | JSONから照合 |
| 最新版へのリンク・版番号 | JSONから記録 |
| ファイル名・サイズ・Dryadに登録されたSHA-256 | 存在すれば記録 |
| 予想していたファイル一覧との差 | 違う場合はSTOP、推測修復しない |
| **実ファイルバイトのSHA-256照合** | **未実施** |
| テキストの物理ヘッダーと文字コード | **未実施** |
| 島コード・個体IDの物理結合 | **未実施** |
| 個体・遺伝子・生存・繁殖・分散方向の観測値 | **未読** |
| 初回定着、供給源喪失、将来のheldout評価 | **未認定** |

重要：DryadがAPIで返す `digest` は**ソース側が宣言したチェックサム**であり、独立してダウンロードしたバイトと一致することを検証した意味ではない。そもそも今回、データファイルをダウンロードしない。

メタデータに一部が欠ける・通信に失敗する・想定外のファイル名が返る場合も、`HOLD_INCOMPLETE_METADATA_INVENTORY` またはファイル構造のSTOPに固定する。結果が得られなくても個体データを開く方向へ自動的に進めない。

## 再現

```bash
python -m pytest -q tests/test_helgeland_dryad_api_inventory_v1.py

python scripts/audit_helgeland_dryad_api_inventory_v1.py \
  --output build/helgeland-dryad-metadata-inventory-v1.json
```

GitHub Actions：`.github/workflows/helgeland-dryad-metadata-only-v1.yml`。成果物 `HELGELAND-Dryad-PUBLIC-JSON-METADATA-NO-BIRD-DATA-v1` は**ファイルメタデータだけのJSON**。

## 取得結果（公開JSONのみ・凍結版）

最初のメタデータ取得はGitHub Actions run **37773617718**、成果物ID **11549730385** で成功した。ZIPの登録済みダイジェストは `sha256:c88e93163634701b7df4ae7aa65955d76d413f0907425c9e2d1bdfb3ad7e9ee4`。この成果物のJSONを独立に開いて、以下の情報を確認した。

| ソース | Dryad dataset ID | 公開version ID | 公開版番号 | ファイル数 |
|---|---:|---:|---:|---:|
| 2025年出生・繁殖・生存 | 153974 | **354268** | **v2** | 5 |
| 2024年遺伝・血統 | 125726 | **278334** | **v3** | 5 |

ファイルごとの**名前・Dryad内部file ID・サイズ・ソース登録SHA-256**は `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_source_metadata_frozen_v1.json` に保存した。最大の遺伝子型ファイルは **362,644,229バイト**とAPIが記載しているが、**このファイルはダウンロードしていない**。

この凍結版を `--verify-frozen` で指定すると、公開APIからの取得情報が当初の版番号・ファイルID・サイズ・ダイジェストとすべて一致するかを確認する。公開ソースが新しい版に更新された場合は、理由なしに最新版へ差し替えず、**版不一致として停止**する。通信障害でも、バイト検証や成果を虚偽の合格としない。

```bash
python scripts/audit_helgeland_dryad_api_inventory_v1.py \
  --verify-frozen validation/eog_virtual_world_ecology_synthesis_v1/helgeland_source_metadata_frozen_v1.json \
  --output build/helgeland-dryad-metadata-inventory-v1.json
```

これでも**実ファイルSHA-256の独立検証ではなく、公開元メタデータの同一性を照合しただけ**である。物理ヘッダーと、2024・2025年の個体・島IDの整合は依然未検証。

## 次の真の条件

1. 出生日・移動先の変数が物理ファイルに存在することを、応答値を開かないヘッダー検査で確定する。
2. 2024年血統表と2025年成鳥・加入表のID・島コードの対応を、**観測結果に依存せず**確定する。
3. 起源ラベルが直接巣から分かるか遺伝割当か、推定誤差・利用可能時点を分ける。
4. 居住個体群の有無・絶滅／再定着・調査努力の観測契約を独立に確認する。
5. 公表済みの移民適応度結果を新発見と呼ばず、比較対象と評価期間を確定する。

**この5条件が通るまでは新しい生態学的スコアを出さない。** アーカイブが独立した生物種の資料であっても、それだけで初回定着源の観測証拠になるわけではない。
