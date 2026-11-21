# Charaxes Zenodo — checksum and first physical CSV header gate

This is a **source/schema audit**, not an ecological EOG × BAM analysis.
Original 12×64 synthetic world geometry and the EOG-WF closed 3/31/3
empirical denominator remain unchanged.

## Frozen source identity

Parent Zenodo metadata audit: run
`40862054463`, fingerprint
`b500ca1c05cb4ac591619ff4aee8b4513f78ff300d2a5674d9fe3b576eb95142`.
Expected exactly:

- `C_jasius_readme.csv` 1068 bytes, MD5 `296db7fac71b138ec6d84f99391388e0`;
- `C_jasius_reduced_dataset.csv` 152897 bytes, MD5 `6f9f638a1c6966f567c4b7b783a5a47d`.

Protocol independently committed **before file-content access**:
`validation/charaxes_zenodo_schema_v1/protocol_v1.json` at
`82fcc93096d85f7994304e10bd2a2f81f131d599`.

## Transfer semantics

**Full** file bodies are transferred once each to volatile RAM so
the *full-file* published MD5 digest can be checked. The total
declared transfer is 153,965 bytes. The biological rows are physically
transferred, but are **never parsed, logged, saved or used to score
any ecological endpoint**. The only saved scientific-file content is the
physical first-line column-name vector, plus file size/checksums.

The original paper provides sufficient context for hypotheses about
host cover, habitat type and host-patch connectivity, but this gate does
not qualify those as independent A/B/M axes.

## Outcomes

- `FILES_MD5_VERIFIED_HEADERS_ONLY__ECOLOGICAL_AXES_UNQUALIFIED`:
  file identity confirmed; A/B/M/G data rows still unexamined, further
  source-unit and detection gating required;
- `SOURCE_STOP_*`: one physical transport or parse rule failed; no
  automatic retry/alternate endpoint.

Correct behavior is to preserve a negative/inconclusive source result
rather than recast it as biological evidence or modify the source
after accessing records.
