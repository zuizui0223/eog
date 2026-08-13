# EOG v2 Zhoushan frog response-free metadata audit result

## Status

**Stage 1 response-free metadata audit — PASS as an access firewall, geography admission not yet passed.**

No microsatellite/genetic file was downloaded, opened or hashed.

Source workbook: Zenodo record `5012316`, `Raw transects .xlsx` only.

- released MD5: `3fcd9bc56c414d6ca6518303d87c4736`;
- observed SHA-256: `70988c9acb69463bd32c2aed5b25a00ec5ebc762bde63ec4aec8b7f777dd4443`;
- workflow run: `31654548790`;
- artifact ID: `9163845608`;
- artifact digest: `sha256:9ff9d73f3ff5a2267a6e87196f4050bc884a02e16beddfd788ac39a5b43416e0`;
- response-free metadata fingerprint: `95f629c363639f569ab61af983426507dfe421a280831fcfe79c9825a482da6c`.

## Workbook audit

The workbook contains one sheet with 418 non-empty rows. Its declared columns are line-transect summaries (`Island`, line transects, frog counts and transect area); there is no longitude, latitude, GPS, easting, northing or other coordinate column.

All 24 declared island nodes were found directly in the response-free workbook:

Meishan, Fodu, Liuheng, Huni, Xiashi, Mayi, Taohua, Dengbu, Zhujiajian, Putuoshan, Zhoushan, Damao, Cezi, Jintang, Dapengshan, Changbai, Xiushan, Dayushan, Daishan, Dongji, Qushan, Sijiao, Shengshan and Huaniao.

The three declared mainland sampling sites — Guoju, Xiepu and Yuanhua — are absent from this transect workbook.

## Decision

`geography_admitted = false` at this stage.

This is not a dataset rejection and not a genetic result. It means only that the released non-genetic transect workbook cannot by itself define all 27 node coordinates.

The next gate is therefore an independent response-free gazetteer/geographic-source audit. Coordinates will be frozen before `Microsatellite data.xls` is accessed. The author-uploaded Figure 1 from Wang et al. (2014) remains a qualitative study-map cross-check, but automated retrieval of the ResearchGate image asset returned HTTP 403 and is not used as the sole reproducible coordinate source.

No location will be inferred from FST, allele frequencies, clustering, migration estimates or any other genetic response.
