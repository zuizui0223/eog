# Exact targeted-measurement audit

The v2.2–v3 BAM simulation used deterministic greedy node selection to construct small direct-measurement sets. The theory protocol required an exact hitting-set audit before those counts could be called minimum.

## Audit denominator

- 12 activation-qualified virtual BAM systems
- 768 eligible truth worlds
- exact finite hitting-set solver
- no solver failures

Audit fingerprint:

`cc7f6ed6f51da660aeeb8cff421504ab0b6c6bcae7a86cdd78c7acf15a44afdd`

## Stagewise result

The greedy solution equalled the exact minimum in every truth case for each sequential stage:

- A: 768/768
- B: 768/768
- M accessibility: 768/768
- M arrival: 768/768

Exact maxima:

- A: 1 node
- B: 2 nodes
- M accessibility: 2 nodes
- M arrival after M accessibility: 0 nodes

## Joint A+B correction

The earlier sequential total `greedy_A + greedy_B` is not always the globally minimum mixed A+B design.

Exact joint A+B minimum distribution:

- 0 nodes: 206 truths
- 1 node: 323
- 2 nodes: 191
- 3 nodes: 48

Sequential greedy A+B distribution:

- 0 nodes: 206
- 1 node: 294
- 2 nodes: 215
- 3 nodes: 53

Therefore some truths can be measured more efficiently when A and B diagnostics are designed jointly.

The maximum bound is unchanged:

[
max |Q^*_{A+B}| = 3.
]

## Joint M + arrival result

Exact joint M/arrival design:

- 0 nodes: 565 truths
- 1 node: 200
- 2 nodes: 3

No additional arrival-state measurement is needed after the exact M-accessibility design in this frozen universe.

## Wording rule

Use **exact minimum** for the audited stagewise A/B/M counts and for the joint hitting-set results above.

For historical v2.2/v2.3 artifacts that used greedy construction, retain the artifact unchanged but interpret the old counts through this audit.

Do not infer that these node-count bounds are universal outside the frozen v3 system roster.
