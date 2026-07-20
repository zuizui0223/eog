# Reproducible bridge graph construction

`build_bridge_graph` converts declared point or patch states into the candidate graph consumed by `infer_bridge`.

## Inputs

Each `BridgeNode` has a stable identifier, latitude, longitude and environmental-state vector. Optional group and time-order fields are descriptive unless `directed_by_time=True` is declared.

A `BridgeGraphDeclaration` fixes the graph rule:

- geographic radius, k-nearest-neighbour degree, or both;
- optional maximum shared-reference environmental jump;
- optional temporal ordering rule.

Barrier costs are explicit node-pair inputs. The builder does not infer coastlines, ocean resistance, habitat quality or dispersal kernels.

## Determinism

Nodes are sorted by stable ID before indices are assigned. Equal-distance k-nearest ties are resolved by neighbouring node ID. The graph fingerprint includes nodes, reference, declaration, barriers and final edge components.

## Interpretation

The result is a candidate transition graph, not an SDM surface. An omitted edge means that the declared construction rule did not admit that pair; it does not prove ecological impossibility. A retained edge is a permissible comparison under the declaration; it does not demonstrate movement, gene flow or occupancy.

## Recommended workflow

1. Declare source, target and intermediate nodes independently of results.
2. Fit or load one EOG robust environmental reference.
3. Freeze graph-construction parameters and barrier inputs.
4. Build the graph and retain its fingerprint.
5. Run `infer_bridge` for declared population pairs.
6. Vary radius, k, environmental-jump and barrier assumptions in a sensitivity analysis rather than selecting them from the desired path.
