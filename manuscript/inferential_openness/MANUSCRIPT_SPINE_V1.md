# From open data to open inference: where ecological workflows lose identifiability

**Working target:** Ecological Informatics  
**Alternative:** Methods in Ecology and Evolution — Perspective/Research Article  
**Status:** cross-project manuscript spine v1

## Core claim

Public availability is not the same as inferential readiness.

Across a prospectively governed ecological workflow, candidate systems can fail before any predictive or biological endpoint is legally interpretable because the released evidence does not reproduce the source identity, registry, geometry, temporal denominator, response linkage, negative-state semantics, or calibration required by the claim.

This paper measures those barriers with a finite denominator rather than collecting anecdotal examples.

## Empirical audit 1 — EOG candidate funnel

The frozen EOG-WF candidate ledger contains:

- 3 scored predictive endpoints;
- 31 scientific/protocol STOPs;
- 3 administrative exclusions.

Administrative exclusions are outside the scientific denominator.

The scientific workflow denominator is therefore 34 candidate attempts: 3 scored and 31 terminal STOPs.

This is **not** a random sample of ecological datasets and must not be interpreted as a prevalence estimate for ecology as a field.

### Fine-grained STOP taxonomy

The 31 scientific/protocol STOPs are frozen as:

- source_transport: 4
- publication_registry_reproduction: 3
- geometry_registry: 2
- metadata_identity_or_transport: 2
- physical_source_separation: 2
- response_linkage: 2
- temporal_registry: 2
- bounded_archive_transport: 1
- full_response_schema_or_linkage: 1
- metadata_identity_or_interface: 1
- response_blind_archive_range_transport: 1
- response_blind_physical_header_schema: 1
- response_blind_zip_inventory: 1
- response_blind_zip_presign_transport: 1
- response_header: 1
- response_independent_baseline_covariate_value: 1
- response_independent_calendar_value: 1
- response_independent_geometry_registry: 1
- source_transport_dns: 1
- surveyed_negative_semantics: 1
- temporal_context_estimability: 1

### Four operational barrier layers

For communication, these 31 stops can be grouped without changing the original terminal labels.

**Layer A — transport / source identity: 11**
- source_transport 4
- metadata_identity_or_transport 2
- bounded_archive_transport 1
- metadata_identity_or_interface 1
- response_blind_archive_range_transport 1
- response_blind_zip_presign_transport 1
- source_transport_dns 1

**Layer B — registry / geometry / temporal denominator: 10**
- publication_registry_reproduction 3
- geometry_registry 2
- temporal_registry 2
- response_independent_calendar_value 1
- response_independent_geometry_registry 1
- temporal_context_estimability 1

**Layer C — physical separation / linkage / schema: 8**
- physical_source_separation 2
- response_linkage 2
- full_response_schema_or_linkage 1
- response_blind_physical_header_schema 1
- response_blind_zip_inventory 1
- response_header 1

**Layer D — semantic / covariate validity: 2**
- surveyed_negative_semantics 1
- response_independent_baseline_covariate_value 1

The grouped counts sum exactly to 31.

### Response-access localization

The STOP ledger also localizes how early the pipeline failed:

- **29/31 STOPs (93.5%)** occurred with no biological response access;
- **1/31** stopped after response-header access only;
- **1/31** stopped after one full-response opening because the frozen deployment/response linkage failed;
- therefore **30/31 STOPs occurred before any biological response row value was used for a scored endpoint**.

This matters for interpretation. The dominant observed bottleneck was not poor model performance after analysis; it was the inability to reconstruct a claim-ready source/registry/linkage architecture before biological response opening.

## Empirical audit 2 — 284b calibration boundary

EOG asks whether a public system can be reconstructed into a valid scored prediction endpoint.

284b asks a later question: even after the biological relation and source architecture are plausible, is the observation state needed to contradict the relation actually identifiable?

In the Level-C v3 architecture screen:

- 12 candidates were screened;
- 2 candidates were architecture-qualified;
- candidate hunting then hard-stopped.

The retained systems were:

- *Cremastra appendiculata* var. *variabilis* — effective pollination function;
- *Belonocnema treatae* / live-oak budbreak — required host-resource function.

Both then failed the prospectively frozen candidate-specific calibration audit.

For both systems:

- independent calibration stream: fail;
- known-state support: fail;
- detection performance: not evaluable;
- hard negative authorized: false;
- focal value opening authorized: false.

The joint v5 decision was:

- candidates passing all C1–C6: 0;
- hard invariant opening authorized: false;
- soft cross-check opening authorized: false;
- process knockout authorized: false;
- new candidate search authorized: false.

The important point is not that either biological relation was false. The negative state required to falsify the relation was not calibrated well enough to be interpreted as biological absence.

## Inferential-openness ladder

The combined evidence motivates a five-layer ladder.

1. **Transportable source**  
   Can the declared bytes/source/version be retrieved under the frozen route?

2. **Reproducible registry**  
   Can the site, deployment, geometry and temporal denominator be rebuilt without reading the response?

3. **Separated and linkable response architecture**  
   Can response records be linked to the declared units without using forbidden mixed/media tables or ad hoc schema repair?

4. **Semantically admissible observation state**  
   Does zero/non-detection mean a surveyed negative rather than missingness, malformed metadata or an invalid covariate state?

5. **Calibrated inferential state**  
   Is the false-negative/sensitivity behavior known well enough that a negative observation can support the biological claim being tested?

A dataset can be openly downloadable yet fail any later layer.

## Why this is not a failure paper

The unit of evidence is not “projects that did not work.”

The contribution is the prospective denominator and terminal-state discipline:

- candidate identities were finite;
- response access was staged;
- STOPs were retained rather than repaired after outcomes;
- predictive STOPs were never relabelled as adverse results;
- missing/uncalibrated biological states were never relabelled as absences;
- candidate hunting was hard-stopped.

Thus the paper estimates **workflow yield under a declared inferential contract**, not publication success.

## What can be claimed quantitatively

Allowed:

> In the frozen EOG workflow, 31 of 34 scientific candidate attempts terminated before a scored predictive endpoint; the barrier distribution was 11 transport/source-identity, 10 registry/geometry/time, 8 separation/linkage/schema, and 2 semantic/covariate stops.

Allowed:

> In a separate 284b Level-C screen, two architecture-qualified biological systems both lacked candidate-specific calibration sufficient to identify the negative function state, so neither biological dependency endpoint was opened.

Not allowed:

> 91% of ecological datasets are unusable.

Not allowed:

> open ecological data are generally irreproducible.

Not allowed:

> the two 284b systems violate their biological dependencies.

## Main ecological-data implication

The practical unit of openness for ecological inference is not a downloadable file.

It is a reproducible chain from source identity to biological state semantics.

The next-generation data-availability statement should therefore distinguish at least:

- retrievable bytes;
- registry/geometry/time reconstruction;
- response linkage;
- survey-negative semantics;
- observation-process calibration.

## Figure plan

### Figure 1 — inferential-openness ladder
Five layers from source transport to calibrated biological state.

### Figure 2 — EOG funnel
34 scientific attempts:
- 31 STOP
- 3 scored endpoints

Show the 31 STOPs by the four grouped barrier layers, with the original fine labels in Supplement. Add a response-access inset: 29 no response, 1 header-only, 1 full-response-before-terminal-stop.

### Figure 3 — where STOPs occur before response
Candidate flow by response access:
- none
- header only
- full response once
- scored endpoint

This distinguishes public-data access from actual biological outcome opening.

### Figure 4 — 284b calibration boundary
12 screened → 2 architecture-qualified → 0 negative-state calibrated → 0 focal hard endpoints opened.

### Figure 5 — data availability vs inferential availability
Conceptual matrix showing why a public URL alone does not certify inferential readiness.

## Proposed title options

1. **From open data to open inference: a prospective audit of ecological evidence pipelines**
2. **Public ecological data are not automatically inferentially ready**
3. **Where open ecological workflows stop: transport, registry, semantics and calibration**
4. **Inferential openness in ecology requires more than data availability**

## Current conclusion

> **Ecological data become inferentially usable only when a chain of source, registry, linkage, semantic and calibration requirements is reproducible. Prospectively retaining terminal STOPs makes those hidden requirements measurable rather than invisible.**
