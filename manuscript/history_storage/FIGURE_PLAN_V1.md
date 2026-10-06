# Assembly-history storage — Figure plan v1

Target format: Ecology Letters Letter  
Main-text display budget: maximum 6 figures/tables/text boxes  
Planned main figures: **4**

## Figure 1 — Where is assembly history stored?

### Purpose

Introduce the biological question without EOG terminology.

### Layout

Panel A — conceptual schematic

- one manipulated arrival history branches into multiple present-state descriptions;
- three possible storage locations:
  1. ecological identity;
  2. unlabeled abundance architecture;
  3. downstream aggregate/spatial state.

Panel B — two empirical systems

- microbiome:
  fungal arrival history -> fungal composition / rust lesion state;
- grassland:
  functional-group arrival history -> shoot composition / root distribution.

Panel C — analysis logic

- labeled composition;
- identity-stripped same values;
- downstream target.

### Message

> The same history can remain visible in different parts of the present state.

Do not place numerical results here.

---

## Figure 2 — Historical retention is target specific in two independent systems

### Purpose

Carry the primary empirical phenomenon.

### Panel A — microbiome

Targets:

- fungal community composition;
- rust lesion fraction.

Display for each:

- observed partial R²;
- null distribution or compact 95% null interval;
- retained-history excess E.

Key values:

- composition:
  - R² = 0.3697
  - null median = 0.2230
  - E = +0.1467
  - p = 0.0001
- rust:
  - R² = 0.2300
  - null median = 0.2147
  - E = +0.0153
  - p = 0.3893

### Panel B — grassland

Targets:

- shoot functional-group composition;
- full root vertical distribution;
- total shoot biomass as a smaller secondary point.

Key values:

- shoot composition:
  - R² = 0.9529
  - null median = 0.1495
  - E = +0.8034
  - p = 0.0001
- root distribution:
  - R² = 0.1853
  - null median = 0.1509
  - E = +0.0344
  - p = 0.3765
- total shoot biomass:
  - E = +0.0948
  - p = 0.2562

### Preferred visual

Horizontal interval plot:

- x-axis = partial R²;
- grey interval = null 2.5–97.5%;
- black tick/point = null median;
- observed point overlaid;
- annotate E beside each point.

Avoid bar plots.

### Message

> History is not a single system-level quantity: its visibility depends on the present-state target.

---

## Figure 3 — Removing ecological identity reveals different storage channels

### Purpose

This is the manuscript's novelty-bearing figure.

### Panel A — transformation

Show one labeled vector:

- microbiome: [Alternaria, Aureobasidium, Cladosporium, Dioszegia, Fusarium]
- or generic labels A–E;

then the same exact values sorted descending.

Explicit annotation:

- same values;
- same dimensions;
- same experimental unit;
- identity labels removed.

### Panel B — microbiome

Show retained-history excess:

- labeled composition E = +0.1467;
- rank abundance E = +0.1486;
- Shannon E = +0.2523.

Identity-storage gap:

- G = −0.0019.

### Panel C — grassland

Show:

- labeled composition E = +0.8034;
- rank abundance E = +0.1949;
- Shannon E = +0.3800.

Identity-storage gap:

- G = +0.6085;
- rank target retains 24.3% of labeled excess.

### Preferred visual

Paired slopes:

- left = labeled E;
- right = identity-stripped E;
- separate row for each system;
- Shannon shown as small open symbol, not part of primary pair.

### Message

> Microbiome history survives without taxon names; grassland history is much more identity dependent.

---

## Figure 4 — Mechanism audit and localization of the microbiome legacy

### Purpose

Show both scientific self-correction and the narrower positive biological result.

### Panel A — placebo mapping audit

Microbiome:

- distribution of all 120 role-mapping R² values;
- mark correct mapping:
  - rank 53/120;
  - tail fraction 0.4417.

Grassland:

- six mapping R² values;
- correct mapping:
  - rank 6/6.

Message:

> The attractive first-arriver-role explanation is not mapping specific.

### Panel B — leave-one-history-out leverage

Five fungal histories, sorted by D_h:

- Alternaria +0.0611
- Cladosporium +0.0264
- Aureobasidium −0.0088
- Fusarium −0.0229
- Dioszegia −0.0336

Zero reference line.

### Panel C — dominance versus lower-rank storage

Direct Alternaria-versus-rest contrast:

- rank-1 dominance:
  - E = +0.1181
  - p = 0.0002
- lower-rank tail:
  - E = +0.0472
  - p = 0.0316
- Delta E = +0.0709.

### Panel D — host-genotype generality

Twelve genotype-specific Alternaria-minus-Other rank-1 dominance differences:

- 11/12 positive;
- equal-weight mean = +0.0610;
- median = +0.0714.

Add summary text:

- common history R² = 0.1353;
- interaction R² = 0.0342;
- common fraction = 79.8%.

### Message

> The failed role mechanism gives way to a narrower result: Alternaria history has disproportionate, dominance-centered, broadly genotype-shared structural leverage.

---

# Supplementary figures

## Figure S1 — v28 representation sensitivities

- corrected composition;
- raw-count composition;
- source-paper outlier exclusion;
- all structurally valid TP1 samples.

## Figure S2 — v30 exact randomization audit

- Monte Carlo null versus complete enumeration;
- shoot/root contrasts;
- Rz 137 sensitivity.

## Figure S3 — v31 full permutation distributions

- labeled;
- rank;
- Shannon;
- both systems.

## Figure S4 — v32 role-alignment result, retained as failed hypothesis

Show the original role-aligned transformation and result, explicitly labelled:

> mechanistic interpretation superseded by v33.

## Figure S5 — v33 complete mapping tables

- all 120 microbiome mapping scores;
- all six grassland mapping scores.

## Figure S6 — v34-v37 microbiome diagnostics

- deletion panel sizes;
- Alternaria vs rest null distributions;
- dominance/tail null intervals;
- common versus interaction history decomposition.

---

# Figure-data sources

Primary machine-readable sources:

- `validation/eog_original_idea_leopold_history_retention_v28/result_summary_v28.json`
- `validation/eog_grassland_above_below_history_retention_v30/result_summary_v30.json`
- `validation/eog_identity_storage_rank_abundance_v31/result_summary_v31.json`
- `validation/eog_role_mapping_specificity_v33/result_summary_v33.json`
- `validation/eog_history_level_leverage_v34/result_summary_v34.json`
- `validation/eog_dominance_tail_history_storage_v35/result_summary_v35.json`
- `validation/eog_alternaria_binary_components_v36/result_summary_v36.json`
- `validation/eog_alternaria_genotype_generality_v37/result_summary_v37.json`

Where full null distributions are required rather than summary intervals, use the frozen workflow artifact for the corresponding version.

# Style rules

- no EOG acronyms in panel titles;
- emphasize biological targets, not pipeline versions;
- consistent x-axis meaning within panels;
- use observed versus null visually rather than significance stars;
- keep v32 visually subordinate because its mechanism was refuted;
- use v33 as a falsification, not a failure appendix;
- avoid implying that E is Shannon information or mutual information.
