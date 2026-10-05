# Original EOG source-turnover experiment — v20 result

## Result

All eight preregistered hypotheses were supported.

The main result is:

> **restoring the number of source populations does not restore one unique
> distributional function.**

The identity and placement of the replacement source determines what part of the lost
function returns.

Authoritative execution:

- run: `37252676696`;
- job: `111583338511`;
- artifact: `11321427773`;
- artifact digest:
  `sha256:33683defb2e172ee4ea73f6aff84cb807e0d3557e21252d2300b1997f50ab1b3`;
- result fingerprint:
  `39d9ab48d9260f325eb802abcbf237e451e36128208148b079735237221f30ad`.

## Same source count, different recovered function

Each experiment began with a three-source network.

The source whose loss produced the largest coverage shock was removed, leaving two
sources.  One replacement source was then added, restoring the count to three.

The three response-independent replacement rules produced different reachable coverage
in **718/768** estimable starting-design rows.

So source count recovery was not functional recovery.

## Replacement can both under-recover and overcompensate

Across the 2,304 replacement strategy-cases:

- **407** exceeded the original pre-loss coverage;
- in **352/768** starting-design rows, all three replacement rules remained below the
  original coverage.

Thus a source replacement can produce:

- incomplete recovery;
- approximate recovery;
- or a new network that reaches more landscape than the original.

There is no single “restore source number = restore old distribution” mapping.

## The coverage–insurance tradeoff reappeared after turnover

The v18 tradeoff survived the loss-and-replacement experiment.

In **370/768** design-rows:

- dispersed replacement gave greater coverage;
- clustered-near-survivor replacement gave greater worst-source-loss insurance.

### Starting from clustered three-source networks

Mean replacement coverage:

- clustered-near-survivors: **0.415**;
- dispersed-far-from-survivors: **0.446**.

Mean worst-source-loss retention:

- clustered-near-survivors: **0.736**;
- dispersed-far-from-survivors: **0.666**.

### Starting from dispersed three-source networks

Mean replacement coverage:

- clustered-near-survivors: **0.312**;
- dispersed-far-from-survivors: **0.423**.

Mean worst-source-loss retention:

- clustered-near-survivors: **0.553**;
- dispersed-far-from-survivors: **0.451**.

The functional choice after turnover therefore remains target-dependent.

## Local replacement is not always restoration

Replacing the lost source near its former location sounds like the natural restoration
rule, but it was not uniformly best.

For networks that began clustered, dispersed replacement most often maximized coverage.

For networks that began dispersed, local-near-lost replacement most often maximized
coverage.

Meanwhile clustered-near-survivor replacement was especially strong for rebuilding
insurance in originally dispersed networks.

So the best replacement geometry depends on the pre-loss network configuration and the
function being restored.

## Source turnover creates spatial legacy

This extends v18 and v19.

- v18: source placement controls coverage and insurance.
- v19: source placement controls confluence and loss of provenance.
- v20: after source loss, restoring the count does not erase the geometric legacy of
  which source disappeared and where the replacement is placed.

The source network therefore has **history dependence** even on a static transition
landscape.

A scalar source-population count cannot represent that state.

## Claim boundary

This is structural reachability, not demographic recovery.

No replacement strategy is a conservation recommendation by itself.  A real
application would need establishment probability, abundance, habitat quality, costs and
other biological constraints.
