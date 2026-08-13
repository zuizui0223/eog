# EOG v2.1 Thalassia hemprichii pre-genetic admission contract

## Status

**Stage 1 response-free geography is admitted and archived. Microsatellite contents remain unauthorized until Stage 2 predictors are byte-frozen.**

Study: Hernawan et al. (2017), *Historical processes and contemporary ocean currents drive genetic structure in the seagrass Thalassia hemprichii in the Indo-Australian Archipelago*, DOI `10.1111/mec.13966`.

Primary data identity: Dryad `10.5061/dryad.404rm`.

The University of Western Australia research repository independently records the same Dryad dataset and explicitly lists Zenodo record `4937634` as an `Access Dataset` route. The Edith Cowan University institutional repository likewise exposes the same two released workbook names under the Dryad DOI. Therefore Zenodo `4937634` is permitted as an archival transport mirror only when its API metadata title and exact expected file names agree before any file use.

Released sources are separated:

- `GPS site IAA.xlsx` — response-free sampling-site GPS metadata;
- `Genalex_Th3all_IAA.xlsx` — response-bearing microsatellite genotype workbook;
- `Th_SNP_data_UdhiHernawan_Chapter3.phy` — SNP sequence source, outside the primary microsatellite validation.

Dryad/ECU metadata states that genotype site IDs correspond to the site IDs in the GPS workbook and that the study used a panel of 16 microsatellite markers.

The first direct Dryad `file_stream` attempt on PR #144 returned only approximately 4.2-kB intermediate HTML objects for both workbook endpoints and stopped at transport-size checks. No GPS workbook cell, microsatellite workbook structure, genotype, or genetic response was accessed in that attempt.

## Hard response firewall

Before Stage 2 is fully frozen:

Permitted:

- resolve and verify Zenodo `4937634` metadata through its public API;
- require the record title to contain `Thalassia hemprichii` and require the exact released file names before download;
- download/read the full GPS workbook;
- record GPS workbook file identity, worksheet names, cells, site IDs and coordinates;
- download the microsatellite workbook as an opaque byte stream only for file existence, size and checksum/SHA-256;
- verify any released Zenodo checksum/size against the downloaded bytes;
- delete the opaque genetic file before artifact upload.

Prohibited:

- opening the microsatellite workbook container;
- inspecting its ZIP member names, worksheet names, cell values, site/sample labels or allele values;
- computing FST, genetic distances, clusters or migration;
- reading the SNP file to reconstruct microsatellite sample identities;
- using exact published genetic values to choose nodes, graph topology, candidate references or EOG settings.

The Stage-1 GPS audit code does not accept a genetic-file path; it receives only opaque genetic size/SHA-256 strings.

## Stage 1 admission — PASS

Authoritative workflow `31667178363` = success; artifact `9168352573`, digest `sha256:281795b720741a28eeb70a6191a80696d8ac519c3d539488243538add6e586aa`.

Zenodo release identities:

- GPS: 10,091 bytes; MD5 `22801051462bdccbe2f0a9f29c4b3940`; SHA-256 `b97e910aa7f9fb52aeeebf434a5480e91995575bc77178d73503d4462fcd9132`;
- microsatellite workbook: 118,400 bytes; MD5 `ec25c053161d4d62b86c860193475784`; SHA-256 `aaaab9e302c9be8cf4e108d2aee5867c0b64ed70b6d3b81bad4d60168ee7f2f3`.

The GPS workbook has one `IAA` sheet with `No / Site name / Code / Lat / Long`. All 17 sampling rows have finite coordinates. Primary population IDs are frozen to the `Code` column:

`BIA, TUA, AMB, KEN, BIT, PAL, JEP, PAR, BAN, NAT, KUP, MAT, DRI, PAD, CK, MI, Ex2`.

The response-free geography is archived under `benchmarks/frozen/thalassia_response_free/`:

- coordinate CSV SHA-256 `7311e561ec2dbeecc57b0b6d8b83b4819697f23480303bcb4478e5750660ce49`;
- coordinate fingerprint `334948e6af43c50d5fb7bfec3396065a1c39d64e0bab7eb5f4a767a42249245d`;
- Stage-1 manifest fingerprint `12a34c597dbf4130ad1dcda8a9822504291a0ac7d4f34fa31c43d8d373d49764`.

These nodes/coordinates may not be regenerated or changed after genetic-response access.

## Stage 2 boundary

Before `Genalex_Th3all_IAA.xlsx` may be opened internally, Stage 2 must byte-freeze:

- all 17 nodes and the archived coordinates above;
- deterministic dateline-safe projection/geometry rules;
- complete conventional candidate family `geographic`, `gabriel_shortest_path`, `gabriel_current_flow` unless one is mathematically non-applicable before response access;
- exact-eventual EOG continuous distance + disconnection on the same response-free graph;
- #143 nested outer/inner population-held-out conventional-reference selector, with EOG excluded from selection;
- common ridge penalty `1.0`;
- response transform `FST/(1-FST)`;
- exactly 10,000 held-out-population bootstrap resamples, seed `20260813`;
- complete predictor/reference/operator fingerprints and a predeclared GO/NO-GO rule.

## Stage 3 boundary

Only after the Stage-2 predictor bundle is archived may the microsatellite workbook be opened once for a separately committed schema/response contract.

The exact raw microsatellite parser, clone-handling rule and pairwise FST estimator must be declared before genotype cells are opened. If those cannot be specified mechanically from source-method information and workbook schema without inspecting observed FST, the dataset becomes non-estimable rather than being adapted post hoc.

No post-response site deletion, graph/reference candidate removal or EOG retuning is allowed. Any GO, null, adverse, non-estimable or indeterminate result remains visible.

## Claim boundary

Primary genetics are symmetric isolation/connectivity. Pairwise FST cannot validate the study's asymmetric gene-flow/current-direction narrative; a directional endpoint requires a separate frozen contract.
