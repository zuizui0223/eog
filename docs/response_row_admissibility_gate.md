# Prospective response row-admissibility gate

## Purpose

A fresh once-only empirical validation may encounter upstream rows in which a field used to select or interpret the focal response is blank, `None`, or contains a documented missing-value sentinel.

Those rows must **not** be silently skipped after outcome access.  Conversely, an ordinary upstream missing-data convention should not force every otherwise valid fresh system to be discarded if the convention was independently documented and its treatment was frozen before row-level response access.

`eog.v2.response_row_admissibility` therefore provides a narrow validation contract for this decision.

It is validation infrastructure, not an ecological operator and not a change to Layer A or Layer B.

## Fail-closed default

The existing categorical response-token schema remains unchanged:

- `None` is invalid;
- a token normalizing to empty is invalid;
- an unknown non-empty category is invalid;
- no post-open alias table or fuzzy matching is allowed.

The row-admissibility gate changes nothing unless a fresh attempt explicitly declares a field-level missing policy before row-level outcome access.

## Declaration

For each field whose missingness can affect row inclusion, freeze a `ResponseFieldMissingPolicy` containing:

- field name;
- disposition: `stop` or `exclude_row`;
- whether `None` is a declared missing value;
- whether empty text after the declared normalization is missing;
- any exact literal missing sentinels such as `NA`;
- the narrow normalization used only to recognize those sentinels.

The declaration fingerprint is order-invariant across fields and changes whenever any missing-token or disposition rule changes.

### `stop`

A declared missing token terminates the opened endpoint under the no-retry contract.

This is the safest default.

### `exclude_row`

The row may be excluded **only** because the exact missingness condition and the `exclude_row` disposition were frozen before response access.

The excluded row is not an event or a non-event.  It must be removed before constructing the exact count-gate population.

## Evaluation precedence

For every opened response row:

1. if a field covered by the declaration is physically absent, stop;
2. if any declared missing field has `stop` disposition, stop;
3. otherwise, if any declared missing field has `exclude_row`, exclude the row;
4. otherwise include the row and continue to the frozen categorical-token / endpoint parser.

Unknown non-missing values are **not** reinterpreted as missing.  They pass through this gate and must still satisfy the frozen categorical response-token schema or other response semantics.

## Outcome-access integration

This does not add a seventeenth outcome-access freeze key.

If a fresh endpoint can contain admissibility-relevant missing response fields, the `ResponseRowAdmissibilityDeclaration.fingerprint` must be incorporated into the existing `response_semantics` freeze fingerprint.  The resulting 16-key ledger therefore binds the row population before outcome access while preserving backward compatibility for existing contracts.

The exact count gate remains the first outcome-dependent analytical operation.  It is evaluated on the prospectively admissible rows after declared missing-row exclusions and before any Layer-A update, model fit, or heldout score.

## No rescue rule

A stopped historical endpoint is not rescued by this infrastructure.

In particular, the Portal *Dipodomys merriami* attempt that first revealed an empty species token was already opened under a contract that did not predeclare an exclusion rule.  It remains terminal and cannot be rerun after adding this gate.

The new gate applies only to genuinely fresh endpoints whose missingness policy is frozen independently before their response rows are opened.
