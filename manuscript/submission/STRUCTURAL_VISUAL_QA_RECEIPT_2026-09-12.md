# Structural/island manuscript — visual QA receipt

Date: 2026-09-12
Scope: presentation-only quality assurance on the committed five-figure submission set. This receipt does not rerun or reinterpret any biological outcome.

## Source figure identities

- Figure 1 reference-conditioned framework: `sha256:4f49a5e23fafd630c38e215453ea15457f1d0ab465efa141ab754dbe5223d126`
- Figure 2 A-Islands reference-conditioned result: `sha256:e401ab9aa0df3d152145d7afd00e7b9e2aaaf728ae42ff2fc8d16ddb0403fc69`
- Figure 3 Tanzania: `sha256:bdb55aa7f66d75aa3b2b1123483dc6775272eba8a11ecd26bffc7a3e7df4eff4`
- Figure 4 cross-system boundary: `sha256:e8a7f87fdbadd1603009e4526776ca4e040926d7fc0d8935918fa4ac377aea24`
- Figure 5 audit trail: `sha256:a39d7003ea9bc3f87da7b00ad191f752c458731c11c088324eb1cc4d506964c1`

## QA performed

All five committed SVGs were raster-rendered at 1200 px and 800 px width, and an additional 800 px grayscale rendering was inspected. The checks were presentation-only:

- no clipping or panel overlap was observed;
- panel labels, titles, axes and primary result annotations remained distinguishable at 800 px width;
- Figure 1 retained its declared-reference → held-out structural probe → earned/redundant/adverse/indeterminate logic without relying on colour alone;
- Figure 2 kept conditional concordance and `C − R3` log-loss increment on visibly separate axes and retained the R0/R1/R2/R3/C ladder;
- Figure 3 retained an explicit zero line plus textual improved/worsened direction labels, so colour is not the sole carrier of sign;
- Figure 4 retained explicit system labels and endpoint names in grayscale;
- Figure 5 remained readable as a provenance table at the inspected widths.

## Boundary

This closes repository-side presentation QA for clipping, overlap, coarse down-scaling and grayscale legibility. It does **not** close submission-day publisher checks. The following remain open until the live Ecological Informatics submission interface is available:

- exact accepted vector/raster file formats;
- any DPI or physical-size requirement imposed by the live system;
- final single-/double-column publisher conversion preview;
- confirmation that publisher conversion preserves symbols, minus signs, intervals and panel labels;
- final colour-vision/accessibility check in the publisher-rendered preview.

No scientific endpoint, reference tier, effect estimate, uncertainty interval, taxon set or claim boundary was modified by this QA.
