# Comparative EOG reference-choice protocol

Comparative EOG requires one transformation fitted before groupwise geometry is calculated. The reference construction is part of the estimand and must be declared before inspecting the comparative result.

## Permitted modes

### External

Fit from an independent environmental background or archived calibration sample. This supports held-out comparison in the declared reference units when the external sample was fixed before evaluation.

### Training-only

Fit from a declared baseline or training group, freeze the transformation, and apply it to held-out groups. This supports directional comparison relative to the baseline reference. It is not symmetric between groups.

### Pooled-descriptive

Fit from all groups being compared. This is allowed for symmetric retrospective description only. It must not be described as prospective validation or transfer.

## Invalid construction

A reference is invalid when it is selected, trimmed, weighted, or otherwise changed after viewing the target outcomes or after choosing the version that maximizes separation. External and training-only references cannot contain evaluation groups. A pooled reference cannot be labeled prospective.

## Required reporting

Every analysis must archive:

- reference mode;
- analysis intent;
- source description;
- whether fitting occurred before evaluation;
- whether evaluation groups were included;
- whether outcomes informed reference construction;
- fitted medians, MAD scales, constant-feature mask, and feature order.

## Sensitivity

Contamination, location shift, unequal sample size, and alternate predeclared valid references are sensitivity analyses. Disagreement among valid references is reported as reference dependence, not resolved by selecting the strongest result.

## Claim boundary

Shared-reference span is comparative extent in the declared transformed coordinates. It is not environmental tolerance, an occupied boundary, suitability, or evidence that one reference is universally correct.