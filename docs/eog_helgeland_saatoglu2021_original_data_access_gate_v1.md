# Helgeland 2021 individual-origin data: official-source byte access gate (2026-10-19)

**Result: 2021 Dryad bird/genetic source bytes remain unavailable through the normal published public file-stream route.** This is an external access *blocker*, not an ecological negative result or a defect of the existing EOG model.

## Why this gate was run once

The prior code/method source gate [#651](https://github.com/zuizui0223/eog/pull/651) verifies the public *2021 Saatoglu author R script* and source-declared five Dryad original files, but **not** the original 2021 individual-data file bodies. The paper uses genetic assignment calibrated by ecological capture/mark/recapture. Claiming measured genetics-versus-detection performance without those files would be unsupported.

The single live test in [PR #652](https://github.com/zuizui0223/eog/pull/652) uses only the official Dryad download links advertised by the source inventory. It has a strict **README-first** gate to avoid touching individual-level bird/genetic records unless the genuine data dictionary itself can be obtained and SHA256-verified.

## Measured real outcome

[GitHub Actions run 39235926635](https://github.com/zuizui0223/eog/actions/runs/39235926635) succeeded as a **diagnostic** and yielded artifact **12179481227**, named \`HELGELAND-SAATOGLU2021-DRYAD-PUBLIC-ACCESS-DIAGNOSTIC-NO-BIRD-DATA\`. Its ZIP SHA256 is \`a19baf7a32f1bf4689da7c622efb1b4ac78ba509fcddc4541351f5badc14c7ef\`, independently inspected. Exact aggregate-only receipt: \`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_saatoglu2021_public_byte_probe_observed_frozen_v1.json\`.

- Official source: [Saatoglu et al. 2021 Dryad DOI 10.5061/dryad.xgxd254h1](https://datadryad.org/dataset/doi:10.5061/dryad.xgxd254h1); dataset ID 72603, version 130231.
- Attempted public README file: \`Geneticassignment_README.txt\`, original file ID 815564; official published public \`/downloads/file_stream/815564\` path.
- **HTTP 403 ACCESS_DENIED_STOP**. The source's declared byte length and SHA256 could not be checked against any returned scientific source bytes. The validator stopped there.
- **0 of 5** original Dryad data/README files verified. No original individual IDs, genetic assignment outcomes, pairwise Fst values, physical headers or ecological model scores read.
- **No authentication bypass, challenge solver, stealth, alternate content host, or unauthorized credentials**. No source file body was persisted to repository, CI artifacts or user output.

The meaning of the 403 is narrow: **this specific standard public file-stream route was inaccessible to this runner at the time of test**. We have NOT proven that every legitimate way of obtaining these openly catalogued files is impossible. The official API public route was not retried after 403; do not describe it as independently failed.

## Scientific status and stop rule

The successful CI demonstrates only that the *access diagnostic code* can recognize a genuine refusal without misclassifying it as 2021 biological data. It does **not** validate a genetic origin, distinguish migrant from resident, estimate any individual assignment error, prove equal island-year survey opportunity, or identify source-of-first-colonisation.

The same 2026 retrospective positive \`capt/obs\` dataset already produced its defensible result under #649: 118/1,272 named-eleven-island first-vs-next-year observed same/different code discordances. The published 2021 recruit comparison is not independent new ecology. STOP looping through old 2026 record filters or authentication probes.

For future authorized access, original five files are documented with source-declared SHA256 digests in:
\`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_saatoglu2021_provenance_preflight_v1.json\`.
If publicly accessible originals or authorized files become available, the next step is independently verifying byte identity of all five **before** inspecting physical headers and distinguishing observed versus genetically assigned natal source. Even then, do not infer historical first-arrival source or source–sink dynamics without independently defined event histories and survey opportunities.

**No fourth EOG-WF endpoint, no reopened paired manuscript science.** Active EOG scientific mainline should return to its preregistered known-truth original-reachability predictions and/or the frozen Methods in Ecology and Evolution submission-preparation lane.
