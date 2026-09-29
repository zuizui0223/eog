# EOG known-truth virtual biogeography — simulation study v1

## Scientific goal

This is a separate post-closure methods-validation line. It does not modify the frozen EOG-WF three-endpoint denominator.

The study asks a simpler and more direct question than real-data predictive complementarity:

> **When the true virtual niche and distribution-forming process are known by construction, can EOG correctly retain compatible truth, eliminate contradicted alternatives, falsify a misspecified finite world universe, and refuse identification when positive occurrences cannot distinguish alternatives?**

The primary endpoint is therefore not AUC or predictive superiority. It is the correctness of finite-world falsification and abstention under known truth.

## Virtual ecology

Each replicate contains:

1. a finite 2-D geographic grid;
2. two continuous environmental coordinates;
3. an explicit virtual niche;
4. a fixed source population;
5. a geographic step limit;
6. an environmental-transition limit;
7. a hard/soft geographic barrier;
8. a finite propagation horizon.

A declared true process generates the complete reachable positive state. EOG does not receive the truth label; it receives only a finite candidate-world universe plus sampled positive occurrences.

## Primary hypotheses and terminal rules

### H1 — truth retention

If the exact true world is included and every supplied occurrence is a true positive, the true world must survive every sequential positive-occurrence prefix.

**Terminal rule:** one counterexample refutes H1 for the declared benchmark universe.

### H2 — discriminating contraction

If every false candidate has at least one true-positive witness occurrence that it cannot support, the complete precomputed witness set must eliminate every false world while retaining truth.

**Terminal rule:** one eligible case that fails to end at exactly the true world refutes H2.

### H3 — omitted-truth universe falsification

If truth is omitted and the positive witness set contains at least one unsupported true occurrence for every candidate, the declared finite universe must contract to the empty set.

**Terminal rule:** one eligible non-empty survivor set refutes H3.

This is finite-universe falsification only. It is not unrestricted biological impossibility.

### H4 — honest non-identification

If two or more genuinely different latent operators support every available positive occurrence, EOG must leave them unresolved.

**Terminal rule:** any unique-world claim in such a case refutes H4.

## Boundary experiment H5 — observation error

The primary core treats supplied positives as valid observations. Therefore a false-positive occurrence outside true finite-horizon support can eliminate the true world.

H5 measures this failure boundary explicitly. It is not repaired inside H1–H4.

The intended conclusion is conditional:

> Exact finite-world falsification is only as trustworthy as the declared occurrence-observation contract.

A later observation-error world layer is justified only if this boundary becomes scientifically necessary.

## Scenario families

The frozen protocol requires the benchmark programme to include:

- continuous environmental bridge;
- environmental bottleneck;
- hard geographic barrier;
- stepping stone;
- long-distance jump;
- observational equivalence;
- omitted truth.

The first canonical fixture combines an environmental spike and a hard barrier. Later factorial expansion must preserve H1–H4 definitions and cannot remove failing fixtures.

## Evaluation objects

Report:

- true-world retention by observation prefix;
- exact compatible-world set after every update;
- false-world elimination;
- finite-universe falsification;
- unresolved/identifiable status;
- number of positive witnesses needed for the terminal decision;
- exhaustive finite-world coverage certificate;
- deterministic scenario/result fingerprints.

Do not summarize the benchmark with AUC.

## What would count as success?

The study is considered methodologically successful only if H1–H4 survive the complete preregistered finite benchmark universe.

If any primary hypothesis fails, the result is retained as a method boundary and the corresponding EOG claim must be narrowed before further complexity is added.

The study is therefore designed to produce a scientifically useful result whether the hypotheses survive or fail.

## Language decision

### Reference implementation: Python

Version 1 stays in Python because the current exact EOG world reconstruction, first-passage operators, fingerprints and tests are already implemented in Python/NumPy. Reimplementing the same logic in C++ before the scientific contract is settled would create two possible sources of truth.

For the v1 study, auditability is more important than raw speed.

### When C++ becomes justified

C++ is allowed only after profiling the frozen Python benchmark. The protocol trigger is:

- target benchmark workload exceeds **60 s wall-clock on CI**, or
- peak memory exceeds **1 GiB**.

If that happens, C++ should be a backend, not a new scientific implementation. It must reproduce all frozen Python fixture classifications and exact compatible-world sets before being used for benchmark results.

The likely long-term architecture is therefore:

```text
Python
  ├─ experiment design
  ├─ manifests / fingerprints
  ├─ result audit
  └─ plotting / manuscript

optional C++ backend
  └─ large repeated graph propagation / enumeration only
```

Do not port to C++ merely because the project is computational.
