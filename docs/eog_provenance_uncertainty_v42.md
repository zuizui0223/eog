# EOG v42 — what stronger source measurements can and cannot repair

## Current result, 2026-10-20

**Continuation of v41 on exactly the same simulated worlds; not an independent field replication.** The 768 latent designs, three activation histories, four complete occupancy snapshots, v26 present-state mappings and v39 selected sites remain fixed. Protocol was committed before scoring at `e59612ac26da5239c6587c176d7179ea9f2191ef`. Source-tag coverage is still 0.60 and conditional misclassification 0.10; tags are idealized earliest-source sets, not observed genetic ancestry.

## The crucial denominator correction

v41 reported 120/189 designs where source observations informed exact history, but only 48/189 where they informed the lag2 maturity map. This does **not** mean the other designs necessarily needed maturity information that source measurements failed to provide.

Among those same 189 designs whose **history** is ambiguous after four complete occupancy snapshots:

| Maturity-target status | Designs |
| --- | ---: |
| Maturity already determined by occupancy alone | **141** |
| Maturity initially uncertain; perfect observations at the existing selected sites suffice | **36** |
| More perfect source-measurement locations would be required | **0** |
| Maturity remains uncertain even with all locations' perfect source tags | **12** |

Thus the maturity-uncertain denominator is **48**, not 189. All 48 receive some maturity information from the unchanged noisy source measurements; 36 become fully determined under perfect same-site observations, while 12 retain an observational-equivalence limit. The 72 v41 history-informative/maturity-uninformative designs are in the **already maturity-determined** group. Their zero incremental target information is not evidence that source data fail at a still-uncertain maturity task.

## Exact nested-evidence partition

For each target T, compare O (occupancy), O+Y (the existing noisy selected tags), O+P_selected (those same tags measured perfectly), and O+P_all (every source tag measured perfectly). The four nonnegative components telescope to H(T|O): information already recovered, loss from missingness/misclassification, loss from unmeasured source locations, and residual uncertainty that this entire source-information class cannot remove. This is an ordered expected-information decomposition, **not a causal variance partition**.

Primary result: lag2 maturity, confluence policy, all 189 occupancy-history-aliased designs.

| Component | Mean bits per design | Share of uncertainty remaining after noisy tags |
| --- | ---: | ---: |
| Already recovered by noisy selected tags | 0.1406477892 | Not part of the remaining-uncertainty denominator |
| Missingness and misclassification at existing sites | **0.0765937453** | **64.4068%** |
| Additional distinguishable information from other perfect source sites | **0** | **0%** |
| Residual after every source tag is perfectly known | **0.0423280423** | **35.5932%** |

Baseline entropy is 0.2595695769 bit; residual after the existing noisy measurements is 0.1189217876 bit. Under the frozen majority rule, the residual is **measurement-loss dominated**, not source-class-floor dominated. Do not equate these entropy fractions with percentages of correctly classified organisms.

The separate expected Bayes target-error calculation yields 0.1058201058 before source observations, 0.0435202134 after the noisy selected tags, and 0.0211640212 with all perfect source tags. These are model-prior-weighted classification errors over the synthetic candidate histories, not field prediction error rates.

## Dependence on the scientific target

The source-class-floor share of remaining entropy is **72.3555% for exact activation history**, **35.5932% for lag2 maturity**, **63.1467% for the transient age-1-to-2 state**, and **55.8931% for the saturated age-class map**. A request for more accurate historical reconstruction and a request for better prediction of current maturity can therefore justify different measurement priorities even in the same landscapes.

All full-source residual counts reproduce their original values: 81 exact-history aliases, 12 lag2 maturity aliases, 45 transient-state aliases and 45 saturated-age aliases. No new age threshold or process was introduced.

## What zero spatial-information loss does NOT establish

For the frozen confluence policy, perfect measurements at its existing at-most-three sites preserve every distinction that the complete perfect source map supplies in these candidate worlds. The original response-blind random policy also has zero perfect-source spatial gap for lag2 maturity. This is **not** evidence that selecting confluences is generally superior; v40's weak targeting effect remains unchanged.

Zero additional *perfect-information* coverage gain also does **not** imply that additional noisy measurements are useless. Replicate or spatially redundant noisy readouts can reduce measurement error, which belongs to the measurement component in this precision-first decomposition. Observation costs, correlated errors, nonrandom missingness and unknown candidate histories have not been modeled or measured.

The 12 source-class-limited maturity cases require a distinguishable observation type, such as timing information, within this declared model. No specific field assay is validated by that statement. They are not evidence that real ancestry universally cannot identify ecological maturation.

## Verification and reproducibility

Eight synthetic analytic tests were written before implementation, failed on missing functions, and then passed locally. The complete GitHub benchmark first reran v41 and matched its entire canonical SHA256 `34f6f2bd94b9b22854eb699c97607ec2b9408f0ea55bcd6d5103a4019581125d`. All 768 designs, 5 targets and 3 policies were then retained as **11,520 unique scenario records**.

Authoritative first successful execution: [Actions 39370012736](https://github.com/zuizui0223/eog/actions/runs/39370012736); artifact **12240343776**. The downloaded ZIP SHA256 was independently verified as `67271f397699e8b2ab472c45cf7463a4469480467c0a06acc32952bd4051be84`. Every CSV row was independently checked for uniqueness, nonnegative entropy/error components, exact telescoping totals and the primary 189-design classification and means.

Full canonical result JSON SHA256: `32887217c613ea92fd20e32d60d0a7e93ef8355c628ea955f968bec98436e273`.
Scenario CSV SHA256: `45cab09343adf58352b93eb6faeff6b6044cbfdac50129800b02d8bbb2f0e8bc`.
Both are locked in `validation/eog_provenance_uncertainty_decomposition_v42/result_locked_v42.json` and required on reruns.

```bash
python -m pytest -q tests/test_eog_provenance_uncertainty_v42.py
python benchmarks/run_eog_provenance_uncertainty_v42.py --output-dir build/v42
```

No original Dryad data were retried, no field-genetic or demographic data were added, and no new EOG-WF endpoint or submission claim was created. The frozen EOG-WF 3 scored /31 STOP /3 administrative exclusions remain unchanged.
