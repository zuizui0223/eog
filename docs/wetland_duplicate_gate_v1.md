# Wetland amphibian native survey-ID conflict: fail-closed source gate

## Exact source

The source is the original amphibian survey CSV in
`zuizui0223/frogcs`, commit
`5e2f0a87c639df373fa2700b29403d2ab417a1cc`,
`research/external/zenodo_15044115/wetland_amp_surv_data.csv`.
SHA256:
`45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`.
The 29-site native site table SHA256 is
`93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

Pre-score protocol:
`25e040c1655a3ddbc449d3afe927e18f00079fc9`.
Verified CI:
https://github.com/zuizui0223/eog/actions/runs/43578553991

## Confirmed row-level conflicts

381 native survey rows but only 379 unique survey IDs.
Two duplicated IDs are **not identical row copies**:

1. `feneketlen-turjan:bottletrap:89` (CSV lines 34 and 37,
   both 2024-03-29). Both have the same site, date, method,
   num=1 and recorded weather. Line 34 has all nine
   species counts zero. Line 37 reports Pelobates fuscus=1,
   Rana dalmatina=1, Lissotriton vulgaris=1, Bufo bufo=4.
2. `tengelyut-2:bottletrap:118` (CSV lines 257 and 265,
   both 2024-04-27). Both have the same site, date, method,
   num=1 and weather. Line 257 has all nine species
   counts zero; line 265 has Pelobates fuscus=3.

These may be distinct traps collapsed to one survey
identifier, corrections, or inconsistent recording.
The CSV alone **cannot distinguish these possibilities**.
The script preserves both full native species vectors
and exact line numbers for adjudication.

There are 379 unique site×date×method opportunities
and 105 site×method groups with at least two dates.
These structural facts do not establish equal effort,
a verified closure period, or that all species zero
counts represent sampled nondetections.

## Decision

`BLOCKED_CONFLICTING_SURVEY_IDENTIFIERS`.

Do not drop, sum or take the maximum of the conflicting
records without a source-supported sampling-unit rule.
Do not fit an occupancy model or claim habitat/detection
effects from this table until sampling metadata resolve
the duplicate identifiers and effort/closure assumptions.

This is a successful source-integrity diagnostic, not a
positive ecological result. No A/B/M, EOG geometry or
new EOG-WF endpoint is inferred.

Machine-readable receipt:
`validation/wetland_duplicate_gate_v1/result_receipt.json`.
