# Paper-ready EOG-WF manuscript assets

These files are generated from the frozen fresh-endpoint synthesis, candidate-flow ledger and Tampa terminal certificate. They do not rerun biological response processing or model fitting.

## Frozen scientific boundary

- fresh scored endpoints: **3**;
- scientific/protocol STOPs: **31**;
- administrative exclusions: **3**;
- observed endpoint pattern: **favorable / favorable / adverse**;
- product boundary: `structural_diagnostic_plus_context_dependent_predictive_complement`;
- candidate hunting: **hard-stopped**;
- primary submission route: **Methods in Ecology and Evolution**.

## Generated files

- `fresh_endpoint_results.csv` — manuscript endpoint table;
- `candidate_flow_table.csv` — full prospective candidate ledger projection;
- `candidate_funnel_summary.csv` — STOP counts by terminal stage;
- `figure_1_two_layer_architecture.svg` — Layer A / Layer B architecture;
- `figure_2_candidate_funnel.svg` — prospective validation denominator;
- `figure_3_endpoint_performance.svg` — endpoint-wise paired log-loss differences;
- `figure_4_louisiana_decoupling.svg` — structural falsification vs predictive complementarity;
- `methods_results_core.md` — evidence-backed Methods/Results core;
- `submission_boundary.json` — final claim and journal boundary;
- `generation_manifest.json` — input/output SHA-256 audit.

Rebuild with:

```bash
python manuscript/build_paper_ready_eogwf.py --output-dir build/paper_ready_eogwf
```
