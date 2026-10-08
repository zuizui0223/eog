# Helgeland 2025 parent–recruit: offline physical-header bridge v1

**State: real biological files NOT obtained; original `HOLD_PARENT_RECRUIT_TIME_ORIENTATION_UNVERIFIED` remains.** This tool only removes the operational mismatch between the old 2024+2025 four-file extractor (#622–#623) and the separate within-2025 four-file preregistered pathway (#624).

## Source files to obtain (public Dryad, v2 only)

Dataset: [Saatoglu et al. 2025, DOI 10.5061/dryad.qfttdz0sx](https://datadryad.org/dataset/doi%3A10.5061/dryad.qfttdz0sx). The four file IDs are already fixed in the frozen metadata:

| Source | Dryad file ID | Frozen size (bytes) |
|---|---:|---:|
| LRS.txt | 3972793 | 43026 |
| ARS_Survival.txt | 3972792 | 220060 |
| Rectype_LRS.txt | 3972795 | 30984 |
| Rectype_ARS_Survival.txt | 3972794 | 141028 |

Download from Dryad's **published version** externally and place four raw files in a directory *outside* the Git repository:

```text
/private/helgeland-sources/
  fitness_2025/
    LRS.txt
    ARS_Survival.txt
    Rectype_LRS.txt
    Rectype_ARS_Survival.txt
```

The script itself makes **no web/API requests**, never reads downloaded data rows as observations, and never joins IDs. The supplied full files are streamed **as opaque bytes** solely for size and SHA-256 checks; only each *first physical line* is decoded.

## Explicit delimiter

One delimiter for each file must be independently verified and declared. Do NOT infer TAB from `.txt`; the example below is valid **only if the physical separators are actually TAB**:

```bash
python scripts/extract_helgeland_2025_parent_recruit_firstline_v1.py \
  --source-root /private/helgeland-sources \
  --delimiter LRS.txt=TAB \
  --delimiter ARS_Survival.txt=TAB \
  --delimiter Rectype_LRS.txt=TAB \
  --delimiter Rectype_ARS_Survival.txt=TAB \
  --output build/helgeland-2025-parent-recruit.header-only.json \
  --receipt build/helgeland-2025-parent-recruit-header-receipt.json
```

Supported explicit separators: TAB, COMMA, SEMICOLON, WHITESPACE. The extractor rejects unknown/partial delimiters, size or checksum differences from Dryad's frozen v2 metadata, missing prerequisite header roles, duplicate/unsafe headers, symlinked raw source roots, existing output files, and output redirection into the source tree.

**A successful local run upgrades only physical-header identity:** `HEADER_ONLY_BYTE_IDENTITY_VERIFIED__TEMPORAL_HOLD`. It does not change the source-only pre-observation contract or establish parental breeding islands at a birth year, recruit settlement location/timing, common ID domains, island-code mapping, sampling effort, founding/colonization, fitness effects or prospective forecasts.

## Tests and audit boundaries

```bash
python -m pytest -q tests/test_helgeland_2025_parent_recruit_firstline_v1.py
```

The tests use exclusively fabricated text rows. Neither true source files nor their observed phenotypes are checked into GitHub or passed into CI. The original 2024+2025 four-file physical-header workflow remains available independently.
