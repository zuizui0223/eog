# Acceptance criteria for the closest-prior manuscript revision

The manuscript is ready to return to release preparation only when all criteria below are met.

## Literature positioning

- Introduction cites the closest source-conditioned connectivity precedents (Prugh 2009; Schooley & Branch 2011; Berlow et al. 2013).
- Introduction cites integrated suitability/connectivity precedents (Ortiz-Rodríguez et al. 2019; Nelli et al. 2022; Van Moorter et al. 2023; Riva et al. 2024; Kim et al. 2024; Felin et al. 2025).
- Introduction or Discussion cites graph/connectivity uncertainty precedents (Ortiz-Rodríguez et al. 2023; Prima et al. 2024; Cushman et al. 2026).
- The verified-reference ledger contains every new DOI.

## Novelty language

The manuscript explicitly says, in substance:

- suitability/connectivity integration is established prior work;
- nearest occupied/source patch and source-weighted connectivity are established prior work;
- sensitivity to dispersal thresholds/connectivity-model choices is established prior work;
- EOG is not proposed as the first connectivity framework;
- the present contribution is the leakage-safe, reference-conditioned **incremental held-out validation** and its audit/falsification architecture.

## Empirical boundary

The following frozen quantities remain unchanged:

- A-Islands declared taxa: 886;
- A-Islands estimable taxa: 845;
- A-Islands primary concordance: 0.6177465917820878;
- A-Islands species output SHA-256: `aca305054d9d14935803f53fc5edb9dc46228c0a6badc00c810bcc8552a1c488`;
- Tanzania species: 60;
- Tanzania primary LOSO log-loss difference: +0.032113119;
- Tanzania result fingerprint: `6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4`.

## Submission packaging

- full CI green on supported Python versions;
- offline submission-package rebuild green;
- no stale generated manuscript assets;
- novelty checklist blockers checked only after the actual manuscript and reference ledger satisfy these criteria.

## Stop rule

Failure to find a priority claim is **not** a reason to invent a new outcome analysis. New outcome work before first submission requires a separately justified validity threat under the no-new-analysis rule.