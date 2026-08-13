# EOG v2 Zhoushan pond-frog response-free coordinate freeze

## Status

**Coordinates frozen before any pairwise FST table or microsatellite genotype file is accessed.**

This document closes the geography-selection stage for the independent Zhoushan candidate described in `docs/eog_v2_zhoushan_frog_pre_genetic_contract.md`.

The exact selected nodes are stored in:

`benchmarks/frozen/zhoushan_frog_response_free/population_coordinates.csv`

No coordinate in that file may be replaced, moved, merged or dropped after the genetic response becomes visible. Any later coordinate sensitivity must use only the perturbation rule predeclared below.

## Biological nodes

The 27 node IDs are the three mainland sites and 24 islands declared by Wang et al. (2014), DOI `10.1111/mec.12634`:

- mainland: Guoju, Xiepu, Yuanhua;
- islands: Meishan, Fodu, Liuheng, Huni, Xiashi, Mayi, Taohua, Dengbu, Zhujiajian, Putuoshan, Zhoushan, Damao, Cezi, Jintang, Dapengshan, Changbai, Xiushan, Dayushan, Daishan, Dongji, Qushan, Sijiao, Shengshan, Huaniao.

The source paper states that line transects covered accessible habitat across each sampled island/site. Therefore the graph node is explicitly a **population/site representative point**, not an asserted capture-coordinate centroid.

## Response-free evidence used

### Released transect workbook

Stage-1 run `31654548790` accessed only Zenodo `Raw transects .xlsx` and never the microsatellite file.

The workbook confirms all 24 island names but contains no coordinate/GPS fields and omits the three mainland transect sites. Its negative result is frozen in `docs/eog_v2_zhoushan_frog_pre_genetic_metadata_result.md`.

### Public gazetteer probe

Stage-1b run `31654792433` queried OpenStreetMap/Nominatim within the declared study region without genetic access.

- artifact ID: `9163976443`;
- artifact digest: `sha256:30224dc5777f3576937223b19edf114fc9a70c4844c0b6616756c684788031a9`;
- response-free candidate fingerprint: `7c0e3ab6af21b55a1e541b20a57357f20551d5a1d3ed5d24c4d90f7d48d1f74e`.

The probe itself performed no coordinate selection.

### Non-genetic fallback gazetteers

Where the response-free OSM probe lacked a direct island entity or returned only a settlement/admin object, the following public GeoNames-backed records were preselected before genetic access:

- Huni Shan — GeoNames `1886850`;
- Putuo Shan — GeoNames `1798437`;
- Dapeng Shan — GeoNames `1813726`;
- Sijiao — GeoNames `1794244`;
- Yuanhua town — OSM node `1699762355`, also GeoNames `1786088`.

The source-paper Figure 1 is used only as a qualitative geographic cross-check. An automated ResearchGate image-download probe returned HTTP 403, so the figure asset is not the reproducible primary coordinate source.

## Frozen coordinate-selection hierarchy

The hierarchy was declared and applied without genetic outcomes:

1. direct OSM `place=island` centroid from the archived Nominatim candidate run;
2. GeoNames island centroid when no direct OSM island entity was returned or a settlement/admin object was less appropriate;
3. mainland sample sites use response-free town/admin centroids;
4. Dongji and Huaniao use representative administrative centroids when a single direct island centroid was not available from the frozen OSM probe.

The hierarchy is not revisited after response attachment.

## Coordinate-representation sensitivity

The primary analysis uses the coordinates exactly as frozen in the CSV.

Because several nodes represent sampling distributed across an island/site rather than an exact capture coordinate, a response-independent coordinate sensitivity is predeclared:

- ordinary island centroid: radius `5 km`;
- mainland town centroid: radius `3 km`;
- large-island or archipelago representative centroid: radius `10 km`.

If coordinate sensitivity is later run, each node may be moved only to the eight compass directions at exactly its frozen radius, one node at a time, with all other coordinates fixed. The graph/reference/EOG construction must be rerun for each perturbation and reported as a sensitivity only. The primary coordinate set is never replaced by whichever perturbation predicts genetics best.

## Stage-2 predictor contract

Before any exact FST response is opened, the following are frozen from the coordinate CSV:

- great-circle geographic distance (IBD);
- local tangent-plane Gabriel graph;
- geographic edge support `exp(-d / median_Gabriel_edge_length)`;
- `loss_support = 0.5`, matching the already-confirmed exact-eventual genetic construction;
- effective-resistance/current-flow strong-reference distance on the response-free Gabriel conductance graph;
- exact-eventual EOG continuous genetic distance and explicit disconnection indicator;
- environmental distance set to zero, with IBE explicitly **non-applicable** rather than invented;
- response transform fixed to `FST / (1 - FST)`;
- ridge penalty fixed to `1.0`;
- leave-one-population-out prediction: every pair involving the held-out node is excluded from training;
- inferential unit for robustness is the held-out population.

Primary empirical contrast after response attachment:

`strong_reference + EOG − strong_reference` held-out MSE, where negative favours EOG.

Promotion from this dataset requires all of:

1. all 27 frozen populations are represented in the exact pairwise response, or any missing-response exclusions are mechanically required without graph changes;
2. the current-flow strong reference is not worse than IBD in pooled LOPO MSE;
3. the equal-weight mean held-out-population MSE difference `(strong + EOG) − strong < 0`;
4. the upper 95% percentile bootstrap bound over held-out populations is `< 0`, using exactly `10,000` resamples and seed `20260813`.

If condition 2 fails, the result is `indeterminate_strong_reference_failure`, not rescued by dropping current flow. If conditions 3–4 fail, the exact independent result is retained as null/adverse.

## Genetic-response firewall

The primary response source, after Stage-2 predictor fingerprints are frozen, will be the Wiley Supporting Information **Table S1** for DOI `10.1111/mec.12634`, which contains exact pairwise FST values.

`Microsatellite data.xls` from Zenodo/Dryad is reserved for optional raw-genotype replication and is not needed to choose or tune the primary graph.

The exact Table S1 file, its values and the raw microsatellite file remain prohibited inputs until the Stage-2 predictor bundle has been archived and fingerprinted.
