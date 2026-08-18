# Hydrilla two-layer EOG-WF validation attempt

## Final status

> **`gate0_stop_source_transport_blocked`**

The Hydrilla candidate stopped before any response, geometry, colonization, or extinction row was opened. It is not evidence for or against `symmetric_world_support_summary_v1`.

## Why the candidate was screened

The published James River rock-pool study was unusually strong on response estimability:

- 506 randomly selected pools;
- five monitoring years, 2017–2021;
- more than 5,000 surveys;
- 147 pools with Hydrilla detections;
- 133 reported colonization events;
- 55 extinction events;
- 147 persistence events;
- repeat surveys and a detection-aware dynamic occupancy analysis.

These aggregate results were used only to establish that a prospectively frozen event-count gate was plausible after Chiricahua failed with eight calibration first detections. No EOG-specific result was known or used to tune the design.

## Frozen source

- Dryad DOI: `10.5061/dryad.jsxksn0fn`
- publication DOI: `10.1002/ece3.11558`
- resolved Dryad version ID: `296642`
- expected files: seven, all present in public API metadata

Public API metadata exposed file names, sizes, SHA-256 digests, file IDs, and official download relations. That metadata was frozen without source-data row access.

## Transport attempts

### 1. Official per-file route

Workflow `32093871518` reached the Dryad file download endpoint and received HTTP `401 Unauthorized` before any file content was returned.

### 2. Official full-dataset bundle route

After correcting a linked-version metadata adapter, workflow `32094591434` reached the public dataset bundle endpoint and received:

```json
{"error":"Unauthorized, must have current bearer token"}
```

- artifact ID: `9309483998`
- artifact ZIP SHA-256: `4d8538aa01668fa7cf1079fd31e4f25b2a813f8da404a9d9164f52f3d74e402d`
- result fingerprint: `8d39874422089f100a41f28838c0d34ebf990f996a3258d3ec2a73ad15709fbf`

## Response-firewall state

- response rows opened: **false**
- response values parsed: **false**
- geometry rows parsed: **false**
- EOG worlds constructed: **false**
- Layer-B prediction evaluated: **false**

The two intervening failures were technical and explicitly diagnosed:

1. the initial individual-file transport returned 401;
2. the first bundle implementation misread Dryad's linked-version JSON representation before source access; the adapter alone was corrected, after which the official bundle route itself returned 401.

## Scientific boundary

The candidate cannot proceed merely because its event count is attractive. The complete 506-pool geometry had to be frozen from exact public bytes before response access. Because the bytes were unavailable through both official public routes, structural Gate 1 was never run.

Do not:

- use an authenticated private bearer token and call the result public/reproducible;
- work around browser challenges;
- use a response-bearing mirror;
- reconstruct complete geometry from response rows;
- substitute nearest-neighbour or distance-to-river summaries for full geometry;
- reopen Hydrilla later in this sequence and call it fresh independent confirmation.

This branch preserves the transport evidence. The PR is closed unmerged so candidate-specific machinery does not expand production `main`.
