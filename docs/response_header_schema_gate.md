# Bounded response-header schema gate

## Purpose

Fresh empirical validation can fail before any scientific model is fit if the published
metadata schema and the physical response-file header disagree.

A candidate-specific parser must not discover that mismatch only after row-level outcome
access and then repair itself. `src/eog/v2/response_header_schema.py` makes the physical
column-name contract executable **before outcome rows or values are opened**.

This is validation infrastructure, not an ecological operator.

## Relation to the response firewall

`src/eog/v2/response_firewall.py` already provides a bounded first-record reader that
stops at the first physical CR/LF delimiter and refuses to read farther.

The header-schema gate consumes evidence produced under that firewall discipline. It does
not authorize an unbounded read, a second record, or a full response scan.

The transport that acquires the header must preserve the same scientific boundary. A
workflow must not download/read response rows merely because the parser subsequently
looks only at the first line.

## Declaration

`ResponseHeaderSchemaDeclaration` freezes:

- a schema identity;
- the expected physical column names;
- the delimiter;
- whether column order is part of the contract.

Expected names must be unique and non-empty. Aliases are not inferred.

## Evidence

`ResponseHeaderSchemaEvidence` records only:

- the bounded physical header text;
- whether the first terminator was CR or LF;
- bytes consumed by the bounded read;
- explicit flags that no response row or response value has been opened.

The evidence fingerprint binds the header hash and firewall metadata.

## Decisions

Possible statuses are:

- `header_schema_match`;
- `stop_outcome_content_already_opened`;
- `stop_header_parse_error`;
- `stop_header_empty_column`;
- `stop_header_duplicate_columns`;
- `stop_header_schema_mismatch`.

A mismatch reports missing and unexpected physical column names separately. If names are
the same but the declaration freezes exact order, an order change also stops.

## Scientific timing rule

A header mismatch detected through the bounded pre-outcome schema gate may be resolved by
creating a **new prospectively frozen response-semantics contract before outcome rows are
opened**. This is schema verification, not outcome tuning.

Once any response row or response value has been opened, the same mismatch is a terminal
pre-model stop for that independent attempt. It does not authorize aliases, parser repair,
or rerunning the opened endpoint and relabeling it independent.

## Why this gate was added

The southern California giant-kelp complementarity attempt reached once-only outcome
access with a metadata-derived response contract that required:

- `pixel_latitude`;
- `pixel_longitude`.

The physical CSV header instead contained:

- `patch_latitude`;
- `patch_longitude`.

The attempt stopped at header comparison before the exact count gate, model fitting, or
heldout scoring. Under the frozen no-post-open-redesign rule, that attempt is not repaired
and rerun as independent evidence.

The generic lesson is narrower than the candidate failure: published metadata can be
internally inconsistent with the physical file header, so physical schema identity must
be verified prospectively through a bounded non-outcome header gate whenever the source
permits it.
