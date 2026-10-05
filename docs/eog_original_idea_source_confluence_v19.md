# Original EOG source-confluence provenance experiment — v19

## Question

v18 showed that clustered source populations create overlapping flow basins while
dispersed sources expand coverage.

v19 asks what that overlap does to historical information.

At a final reachable node, the static map can identify:

- one compatible source;
- or several compatible sources.

If several sources can reach the node, the final distribution has lost source
provenance.

## Timing as partial provenance recovery

For each node, v19 also records the first-passage depth from each selected source.

The earliest-origin set contains the source or sources reaching the node at minimum
depth.

This can turn a statically ambiguous node into a temporally resolved node when one
source arrives earlier than the others.

It cannot resolve a tie when multiple sources have the same earliest depth.

## Distributional-watershed interpretation

A source basin remains source-specific upstream.

Where basins merge, downstream final occurrence can become compatible with multiple
source histories.

v19 measures:

- how often this happens;
- whether it is concentrated downstream;
- whether clustered sources merge earlier than dispersed sources;
- how much first-passage order restores provenance;
- how much ambiguity remains even after timing is known.

This is the explicit confluence/provenance version of the original EOG watershed idea.
