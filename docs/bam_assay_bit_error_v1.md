# Original EOG × BAM: robust geometric decisions with one erroneous assay reading

## Current objective and status

This add-on tests the next failure mode of the merged one-missed-current-G
benchmark. It asks whether a change in the original EOG **positive-pairwise
90th-percentile environmental span** after the ideal removal of M can be
*certified* when an A, B or M site-level binary measurement may be incorrect.

This is an **exploratory analysis of the SAME 12 constructed landscapes,
768 already-exposed parameter worlds and 129 true G classes**. It is not
a new empirical validation, a calibrated measurement-error model, or a
fourth EOG-WF prediction endpoint.

Pre-score protocol: \`validation/bam_assay_bit_error_v1/protocol_v1.json\`,
commit \`31f0f391ebd2c818092dade2ef891d53dae5bc46\`.

## Strict distinction between observation and measurement uncertainty

The current-G observation D is unchanged from the previous benchmark:
\`D = G\` or \`D = G\setminus\{i\}\` for any truly occupied cell i.
All other cells are certified unoccupied, with no false-positive D.
Exactly **2,627 distinct (landscape,D) observation patterns** are
examined. The perfect-current-G comparator remains 121/129 target-
direction-identified classes.

**New source of error:** a chosen nonadaptive panel can include multiple
readings of an individual A/B/M constraint-state bit at a node. Of all
the binary readings in the panel, **at most one may be inverted**.
An incorrect reading is never treated as proof that the true candidate
world is impossible. The model does NOT assume an independent Bernoulli
error rate and does not supply a confidence or credible probability.
Repeated readings of the *same site* can correct this individual flip
but NOT a persistent systematic error common to all repeats.

A 'reading' is one binary assay event; the number of **distinct
axis/node tests** is recorded separately and should not be called the
number of independent field sites, survey visits or living organisms.

## Exact mathematical characterization

For two candidate A/B/M mask triples that predict **different signs**
of the M-release EOG span response, their predicted binary assay
sequences must be at Hamming distance at least **3** to tolerate one
arbitrary erroneous reading. Otherwise their possible one-error
observations overlap, so at least one observation remains undecidable.
Conversely, pairwise distance >=3 is sufficient for a bounded error of1.

We solve, separately for each observed D, an **exact, equal-cost
nonadaptive integer multicover**:

\[
\min\sum_j x_j,\qquad
\sum_{j:\,b_j(u)\ne b_j(v)}x_j\ge3
\quad\forall(u,v)\text{ with distinct target signs},
\]
with integer \`0 <= x_j <= 3\`, where j ranges over A/B/M×grid
node, x_j is the repeat count, and each distinct A/B/M mask triple is
included once. An otherwise identical zero-error model uses a
separation requirement of1.

The implementation uses \`scipy.optimize.milp\` and refuses nonoptimal
solutions. A second independent check enumerates every candidate true
mask, the exact predicted answer pattern, and every possible one-bit
flipped answer string. It fails if any retained alternative has a
different EOG target direction. The solver is NOT optimizing an
adaptive query tree; no universal minimum adaptive read count is claimed.

## Descriptive results from the fixed model universe

In this finite roster, **2,483** observed D classes already have a
unanimous M-response direction; they require zero additional assays
regardless of assay measurement error. The other **144** require
additional evidence.

| Observed-D classes | Minimum readings with perfect assays | Minimum to tolerate one bad reading |
|---|---:|---:|
| 2,483 | 0 | 0 |
| 87 | 1 | **3** |
| 53 | 2 | **6** |
| 4 | 3 | **9** |

The counts are exact for the restricted **nonadaptive repeatable**
assay-panel problem in this finite candidate family, rather than a
population distribution. In this roster, the minimum one-error panel
is 3× the corresponding optimal zero-error panel for all144 initially
ambiguous observations, although that equality is not claimed for
arbitrary BAM model families.

For comparison against previous one-miss true-G robustness, requiring
the target direction to be identified for **every possible D** from
each true G:

| Maximum individual readings | Robust true-G classes (of129) |
|---|---:|
| 0–2 | **86** |
| 3–5 | **117** |
| 6–8 | **121** |
| 9 | **129** |

This is a stronger guarantee than a probabilistic "usually correct"
classifier, but only because the error budget is known and bounded
and the finite hypothetical world universe is treated as complete.

The earlier **noise-free adaptive** result required at most3 site
queries under one missed G. It is not numerically equivalent to this
**nonadaptive** one-error result; the distinction between query
adaptivity, distinct sites and repeated individual readings must stay
visible.

## Methodological consequence

Under one possible bad binary reading, **one or two raw readings cannot
safely resolve initially conflicting geometric response signs**,
irrespective of where they are taken. A single confidently informative
A/B/M site can, however, be read three times to distinguish two
opposite-response finite candidate states under the one-reading error
bound. This provides an explicit error-correcting extension of the
EOG→BAM-worldset→target-response→additional-information workflow.

It does NOT establish that three real field visits at one site will
solve the problem. All three measurements could share an inaccurate
calibration, be made under a state change, or have correlated
misclassification; these violate the bounded single-reading error
assumption.

## Reproducibility and controls

\`\`\`bash
python -m pytest -q tests/test_bam_one_bit_error_v1.py
python benchmarks/bam_one_bit_error_v1.py \
  --output-dir /tmp/bam_assay_bit_error
\`\`\`

The run must use the original known-truth generator and the original
M-release span definitions, preserve 12×64/129/2,627 denominators,
deduplicate identical A/B/M masks, check integer optimality, and
independently enumerate all possible one-error readings for each
reported panel. Every result, including null and ambiguous fibres, is
retained in the archived full per-D output.

**Still outside scope:** realistic site-specific effort and
probabilistic detection in G, systematic or time-correlated A/B/M
measurement errors, measurement costs and observer learning, and
unmodelled natural mechanisms. These remain separate prospective
scientific dependencies rather than assumptions silently added here.
