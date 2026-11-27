# 2026-11-27 independent hydrography and ordinal fallback

## Actual independent source request

The original publisher fish/geometry CSVs remain unavailable. The previous PR head 81838be90eaa7cf07c553713aa892434d40a773d passed all three workflows. The downloaded original ScienceBase and SDC metadata artifact ZIPs were rechecked in the current runtime; SHA-256 matches their recorded receipts. The current container cannot resolve the official data hosts (DNS failure), and no original CSV was attached.

USGS [NHDPlus HR public service](https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer/3) documents NHDPlusID, FromNode, ToNode, LengthKm, HydroSeq, DnHydroSeq. Its [2025 user guide](https://pubs.usgs.gov/publication/sir20255031/full) defines flow direction and pseudo-node semantics. One exact public, non-biological named-river query was frozen at a1d9318c6b4b63e5104eb510dd44c5154398a59d. Run 45940060646 passed offline graph fixtures, then returned TimeoutError. Downloaded artifact 15172068979 (575 bytes) was verified against ZIP SHA-256 9c9b246320201a91d070aaa6419c5bdec66f3b9f8a0296efa52ffa209028615a. See nhdplus_ci_receipt.json. No graph was obtained from this service; do not claim an empirical topology or retry indefinitely. Even a successful named-flowline graph would not be the original survey registry or historical hydrography.

## Actual conditional ordinal analysis, not a new empirical test

[Duda et al. 2021](https://doi.org/10.3389/fevo.2021.765488), Common Reaches section and Table 2: survey reaches numbered upstream to downstream; post-removal counts upper 13, middle 6, lower 3. Lower dam rkm 7.9, upper dam rkm 21.4. The paper reports a 2018 adult Chinook release at reach 14 below the former upper dam. Outcomes in the published article are already exposed. The pinned original XML independently describes the reach ordering and distinct survey-length/river-boundary meanings. Infer section labels from ordering and post-removal section counts, not actual coordinates or individual row values. Freeze ordinal scaffold protocol at 7196f7974f385595fe0d707a0ec22ab992b828cf before enumeration.

Assume 22 ordinal labels and 21 upstream-only adjacent-rank edges, with lower gate 20->19 and upper gate 14->13. This idealized adjacency is a modeling decision, not authenticated network evidence. Reach 22 is a downstream-entry proxy, not an observed source. Alternative source policy adds reach 14 as a conditional sensitivity to management release; it is not a historical pre-removal source. All four passability combinations are counterfactual configurations, not actual dates or estimated fish passability. No geomorphology, other barriers, real distances, timing or downstream movement is represented.

Executed local Python and compared graph propagation to independent interval oracle, 176/176 target decisions matched, all 22 per-target minimal opening families cross-checked against rank formula. Independent JavaScript computation of archived result is byte-identical to the local Python result (Git blobs ed45bdd25f2a32090b020560614a2a5f3034244c and e838214f0c0ceb5a6ca5b73e16f7b0cb088b4911; result SHA256 970178972c350b7ab9d6eb862f1f81b67c672bd51c0fb9852d808966afdef80c). The receipt's scenario counts are exact conditional arithmetic:

| Open gates | Downstream entry only | Entry plus reach14 | Robust | Unresolved | Excluded |
|---|---:|---:|---:|---:|---:|
| None | 3 | 4 | 3 | 1 | 18 |
| Upper only | 3 | 17 | 3 | 14 | 5 |
| Lower only | 9 | 9 | 9 | 0 | 13 |
| Both | 22 | 22 | 22 | 0 | 0 |

For upper-section ordinal targets (1..13), the minimum opening under downstream-only entry is both gates, while with the additional reach14 source it is the upper gate only. An upper observation cannot by itself establish lower-gate passage if a separate source below the upper gate is admissible. This is a source-policy witness, not empirical evidence that a particular fish was relocated, or that its offspring colonized upper reaches. No biology scored.

## Next geographic source and boundary

A more temporally relevant independent physical-data family is [USGS DOI 10.5066/P13RXGHA](https://www.usgs.gov/data/river-margin-and-braid-shapefiles-digitized-aerial-images-elwha-river-washington-2006-2022) (30 image dates 2006–2022, five before the removals). It includes mapped active channel margins and braids in three selected study reaches, not the whole 65 km survey extent; a publicly described metadata record, not downloaded geometry or a complete route graph. The original study used different channel maps for 2007/08 and 2018/19 (redigitized from 2017 imagery). Therefore an independent current NHDPlus network cannot be used as a verified historical network, and geometry must be crosswalked to the original reach boundaries, not simply snapped to nearest nodes without ambiguity checks. Keep measured snorkeled length separate from movement distance. The original geometry CSV is still required for a verified 22-reach correspondence. No biological files accessed, original 3/31/3 unchanged, no main merge.
