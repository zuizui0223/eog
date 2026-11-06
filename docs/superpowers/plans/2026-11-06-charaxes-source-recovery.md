# Charaxes same-source transport recovery and geometry Implementation Plan

**Goal:** obtain the two already frozen public files, verify original MD5/size, then evaluate whether original EOG geometry can be meaningfully applied to the observed resource landscape.

**Architecture:** a separately versioned transport repair, not a replacement dataset or a new confirmatory biological test. Preserve PR675 and run40862766046 as v1 SOURCE_STOP_HTTP_406 with zero ecological rows. Hypothesis: the restricted Accept header caused the content-negotiation failure (RFC9110 sections12.5.1 and15.5.7). Change only Accept to */* at the same two official file URLs; no retries, mirrors, credentials, or alternate records. Identity checks remain strict.

**Tech Stack:** Python standard library for transfer; existing EOG comparative geometry for any subsequent explicitly exploratory analysis. Local transport fixtures run before the live action. Raw data are cached in the run artifact after checksum verification, so analysis does not require redownloading.

**Spec and source:** Zenodo20525795, DOI10.5281/zenodo.20525795. C_jasius_readme.csv:1068bytes,MD5=296db7fac71b138ec6d84f99391388e0; C_jasius_reduced_dataset.csv:152897bytes,MD5=6f9f638a1c6966f567c4b7b783a5a47d. URLs https://zenodo.org/api/records/20525795/files/{filename}/content. Only zenodo.org HTTPS redirects allowed before following. Accept-Encoding=identity. Read no more than frozen size+1. Any HTTP/identity failure stops this version and is retained.

## Tasks
- [ ] Write and run failing tests for wildcard Accept, pre-follow redirect restriction, size/MD5 refusal, and verified-file-only persistence.
- [ ] Implement the minimal recovery script, pass all offline tests, commit code and a pull_request-opened-only workflow; do not retrigger on receipt edits.
- [ ] Run once, download the artifact, independently verify its receipt and all source file bytes. If unsuccessful, stop acquisition and continue only with existing known-truth data.
- [ ] If successful, read the whole data dictionary, audit physical columns, repeated units, missingness and observation effort. Distinguish host availability from adult detections and host-derived connectivity from independently measured movement.
- [ ] Before any new ecological scoring, write a dated local exploratory-analysis contract based on verified schema. Use one fixed shared reference, matched sample sizes, and unit-aware resampling. Report denominator, null/negative results and uncertainty; no causal BAM identification or fourth EOG-WF endpoint.
- [ ] Commit reproducible code, derived results and an honest source/claim receipt. Do not overwrite closed manuscript outcomes.

## Review focus
Content type is not source identity; only strict size and MD5 authorize use. Non-UTF8 README may be valid data: detect documented CSV encoding without editing bytes. Do not infer ecological support A from habitat labels. Do not treat trap nondetection as certified absence. Do not mistake 1666 trap records for independent biological replicates. This is retrospective exploratory validation on an already published source, not a preregistered novel prediction test.
