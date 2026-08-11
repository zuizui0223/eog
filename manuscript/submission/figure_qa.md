# Structural manuscript figure QA

The committed figure set is SVG-first and is regenerated from frozen repository inputs by `manuscript/build_structural_submission_package.py`.

## Automated QA covered by CI

`tests/test_structural_figure_delivery_qa.py` checks all five submitted SVGs for the following structural properties:

- valid SVG XML;
- explicit positive `width`, `height`, and four-value `viewBox`;
- no externally linked raster/image asset;
- no external HTTP(S) dependency in SVG attributes;
- no text element below the current internal 9-pixel minimum used by the committed designs;
- a committed caption file for every figure;
- a committed accessibility description for every figure;
- non-empty caption/accessibility prose;
- figure paths exactly match the submission manifest.

The offline submission-package builder separately proves that these figure files regenerate from frozen evidence and match the committed scientific outputs.

## Manual QA that must remain open until journal upload

The following cannot be closed responsibly without the live journal instructions and final rendered submission preview:

- [ ] confirm the live journal's accepted vector/raster file types;
- [ ] confirm any minimum DPI requirement for rasterized/exported versions;
- [ ] inspect every figure at the journal's final single-/double-column display width;
- [ ] confirm labels, legends, intervals, and small explanatory text remain readable at that width;
- [ ] inspect grayscale print output;
- [ ] inspect a colour-vision-deficiency simulation or equivalent palette check;
- [ ] confirm no publisher conversion changes minus signs, interval marks, superscripts, or panel labels;
- [ ] confirm the final submission preview retains captions/accessibility information in the required fields/files.

## Scientific visual boundary

Figures must not be revised to imply observed movement, colonisation routes, dispersal probability, or causal connectivity. If editorial redesign changes semantic content rather than typography/layout, the relevant figure contract and regression tests must be updated and reviewed as a scientific change.
