# Hypothesis survey CSV contract

This workflow ranks field-survey candidates where predeclared bridge hypotheses disagree. It does not estimate occupancy, occurrence, colonization, posterior model probability, or expected information gain.

## Inputs

### `scenarios.csv`

Required columns:

| Column | Meaning |
|---|---|
| `scenario_id` | Unique sensitivity-scenario identifier. |
| `connected` | Boolean. Accepted values are `true/false`, `yes/no`, `y/n`, or `1/0`. |
| `minimum_cost_nodes` | Ordered node IDs separated by `|`. Empty only when disconnected. |
| `minimum_bottleneck_nodes` | Ordered node IDs separated by `|`. Empty only when disconnected. |

Connected scenarios must declare both complete source-to-target paths. Disconnected scenarios must declare neither path. Disconnected scenarios remain in the family denominator, so support is a robustness frequency across all declared scenarios rather than only successful ones.

### `families.csv`

Required columns:

| Column | Meaning |
|---|---|
| `hypothesis_id` | Unique ecological hypothesis family. |
| `scenario_id` | Scenario assigned to that family. |
| `path_mode` | `minimum_cost`, `minimum_bottleneck`, or `union`. |

A scenario belongs to one family by default. Every row for one hypothesis must use the same path mode. Complete scenario assignment is required unless the CLI flag `--allow-unassigned-scenarios` is supplied.

### `candidates.csv`

Required columns:

| Column | Meaning |
|---|---|
| `node_id` | Unique candidate site or graph node. |
| `survey_effort` | Finite non-negative existing effort. |
| `accessibility_cost` | Finite non-negative cost or burden on a declared scale. |
| `already_surveyed` | Boolean indicating whether the candidate is already covered. |

Accessibility values must be comparable across candidates. Their scale is not standardized automatically.

## Ranking calculation

For each candidate, the pipeline calculates:

- `support_range`: maximum minus minimum node support across hypotheses;
- `mean_pairwise_separation`: mean absolute support difference across all hypothesis pairs;
- `survey_deficit`: one minus effort divided by the maximum effort in the candidate set, capped to `[0, 1]`;
- `accessibility_cost`: directly subtracted using the configured penalty weight.

The default score is:

```text
discrimination_score =
    support_range
  + mean_pairwise_separation
  + survey_deficit
  - accessibility_cost
```

Already-surveyed candidates are capped at a score of zero. Ties are resolved deterministically by `node_id`.

## Outputs

### `hypothesis_survey_ranking.csv`

| Column | Meaning |
|---|---|
| `rank` | Deterministic 1-based rank. |
| `node_id` | Candidate ID. |
| `discrimination_score` | Weighted decision-support score. |
| `support_range` | Largest hypothesis support contrast. |
| `mean_pairwise_separation` | Mean pairwise support contrast. |
| `most_separated_hypotheses` | Hypothesis pair with the largest contrast, joined by `|`. |
| `survey_deficit` | Relative lack of prior effort. |
| `accessibility_cost` | Declared cost used in scoring. |
| `already_surveyed` | Original candidate status. |

### `hypothesis_survey_manifest.json`

The manifest records SHA-256 hashes for all three inputs, configured weights, complete-assignment policy, unassigned scenarios, informative and zero-information candidates, and sensitivity, adapter, ranking, and pipeline fingerprints.

The manifest is the audit record. A ranking CSV without its matching manifest should not be treated as a frozen analysis result.

## Canonical example

Run:

```bash
eog-hypothesis-survey \
  --scenarios examples/hypothesis_survey/scenarios.csv \
  --families examples/hypothesis_survey/families.csv \
  --candidates examples/hypothesis_survey/candidates.csv \
  --output-dir results/hypothesis_survey
```

The ranking must match `examples/hypothesis_survey/expected_ranking.csv`. The example is synthetic and tests the workflow contract; it is not ecological evidence.