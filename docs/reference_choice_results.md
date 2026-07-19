# Reference-choice audit results

The frozen audit evaluated external, training-only, pooled-descriptive, and declared contaminated-external reference transformations at n = 60, 120, and 240.

## Verified result

All predeclared valid modes recovered the simulated two-fold dilation:

- minimum broad-versus-compact AUC across external, training-only, and pooled-descriptive references: 1.000;
- median broad/compact span ratios across valid modes: approximately 1.99 to 2.06;
- contaminated external reference AUC: 1.000 at every tested sample size;
- outcome-informed prospective reference construction: rejected by policy validation.

The absolute span values differed by reference mode. Training-only scaling produced larger transformed spans than external or pooled scaling, while the relative broad/compact contrast remained stable. Therefore comparative EOG must report the reference transformation and should emphasize within-reference contrasts rather than comparing absolute transformed span values produced by different references.

## Interpretation

- External references support held-out comparison when independently fixed.
- Training-only references support directional comparison relative to the declared baseline.
- Pooled-descriptive references support symmetric retrospective description only.
- The contaminated-reference result is a limited robustness result for the tested robust median/MAD transformation, not evidence of immunity to arbitrary contamination.
- No reference mode is selected as a universal winner.

The machine-readable decision file records `passes_gate: true`.