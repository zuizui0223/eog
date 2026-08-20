# Response token schema contract

## Purpose

Fresh once-only empirical validation must freeze not only the meaning of a response
field, but also any deterministic categorical token normalization used to parse it.

A mismatch such as `week1` versus `week 1` is not an ecological result.  If the parser
choice is first changed after row-level response access, however, the attempt is no
longer prospectively frozen.  This contract moves that choice into the response-blind
freeze.

Implementation:

`src/eog/v2/response_schema.py`

Public validation facade:

`eog.v2.validation`

## CategoricalTokenRule

Each categorical response field declares:

- field name;
- the complete allowed canonical categories;
- whether to strip outer whitespace;
- whether to Unicode-casefold;
- whether to remove ASCII whitespace within the token.

No other transformation is performed.  In particular, the generic contract does not
provide fuzzy matching, punctuation stripping, edit-distance repair, numeric coercion,
or post-hoc aliases.

For example, a prospectively frozen `Week` rule may declare canonical categories
`week 1` through `week 4` and set `remove_internal_ascii_whitespace=true`.  Under that
specific frozen rule, `week1`, `Week 1`, and ` week\t1 ` resolve to the same declared
canonical category.  With that flag false, `week1` is rejected.

## Collision rule

Allowed canonical categories must remain one-to-one after normalization.  A declaration
such as canonical values `week 1` and `week1` together with internal-whitespace removal
is invalid because both normalize to the same token.

The declaration fails before outcome use rather than arbitrarily choosing one label.

## ResponseTokenSchemaDeclaration

A schema contains one unique rule per categorical field.  Its fingerprint is invariant
to the order in which field rules are listed, but changes when any scientifically
relevant token-handling choice or allowed category changes.

The schema therefore becomes part of the candidate's existing `response_semantics`
fingerprint.

## Outcome-access integration

The generic `FrozenOutcomeAccessContract` continues to require the same sixteen freeze
keys.  This change deliberately does **not** add a seventeenth key and does not rewrite
historical freeze ledgers.

For new categorical-response attempts:

1. declare and fingerprint the response token schema before row-level access;
2. include that fingerprint in the candidate-specific `response_semantics` freeze;
3. freeze the empirical runner against the same declaration;
4. after authorization, use only that frozen normalization;
5. reject unknown tokens rather than inventing aliases.

If a previously undeclared token is encountered after response opening, stop the
attempt.  A parser repair may inform a later methodology version or genuinely fresh
candidate, but the opened endpoint is not rerun and relabeled independent.

## Scientific boundary

This contract improves prospective data-interface discipline.  It is not an ecological
operator, prediction model, observation model, or novelty claim.  It does not make an
unknown categorical value biologically equivalent to a known one; equivalence exists
only because the exact deterministic text transformation was declared before outcome
access.
