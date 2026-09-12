# Fresh endpoint source identity ledger

Status: 2026-09-08. This ledger records only source identities already frozen in the prospective EOG endpoint issues/contracts. It is not a substitute for the final formatted bibliography.

## 1. Azores yellow eel acoustic telemetry

**EOG endpoint:** receiver-week recorded detection; Issue #289; once-only run `32807155541`.

Frozen public identities before response access:

- biological dataset DOI: **10.5281/zenodo.18154777**;
- source analysis release DOI: **10.5281/zenodo.18154674**;
- associated paper DOI: **10.1111/jfb.70355**;
- system: European yellow eel, *Anguilla anguilla*, Cruz stream, Flores, Azores;
- physically separated response: `raw_detection_data.csv`;
- response-independent receiver registry/effort: `deployments.csv`;
- response-independent tag/release metadata: `flores_eels_meta_data.csv`.

The final manuscript bibliography should resolve the full author/title/year metadata for DOI `10.1111/jfb.70355` from an authoritative bibliographic source. Do not infer those fields from the EOG repository if the source itself is unavailable.

## 2. Southwest Louisiana King Rail passive acoustic monitoring

**EOG endpoint:** site-occasion recorded detection; Issue #292; once-only run `32812052801`.

Frozen official source:

- USGS data-release DOI: **10.5066/P9RRIIR2**;
- ScienceBase item: **5ecf119d82ce30fd980854bd**;
- public design: 33 randomly selected sites, 20 sampling occasions during February–June 2012, 11 secretive marsh-bird species;
- response-independent site table: `Sites.csv`;
- response-independent sampling table: `Samples.csv`;
- focal response table: species-specific `KIRA` detection-history CSV after response-independent focal selection.

The final bibliography should cite the authoritative USGS release and any primary study publication required by the source metadata. The EOG paper should not invent a journal article citation if the release is the only frozen authoritative identity available.

## 3. Tampa Bay seagrass transect monitoring

**EOG endpoint:** eligible parent Transect visit × recorded *Thalassia testudinum* detection among linked child Point events; Issue #388; once-only run `34028447227`.

Frozen public source repository:

- repository: **`tbep-tech/obis-example`**;
- pinned source commit: **`6c567beff95ea04f0e397101befb49d5233ace8f`**;
- response-independent Event core: `dwc/event.csv`, Git blob `583b4d4e328290ab065346579eb4f29f03ea0f99`, 24,654,717 bytes;
- biological response: `dwc/occurrence.csv`, Git blob `d34aeb5aedb72459d1e04059629cb09450df929e`, 12,508,487 bytes;
- occurrence-linked measurement table excluded from the predictive endpoint: `dwc/emof.csv`, Git blob `e463046726080334637824555309fd89c7c447da`, 16,449,353 bytes;
- source documentation states that fixed seagrass transects across Tampa Bay have been surveyed annually since 1998.

The final bibliography should add the authoritative Tampa Bay monitoring/data publication if the source repository or programme supplies one. Until that is verified, cite the immutable source repository/commit in Data and Code Availability rather than inventing bibliographic metadata.

## Citation-completion rule

Before submission:

1. resolve each DOI/repository identity against an authoritative publisher or repository record;
2. preserve the exact frozen source identifiers above;
3. add full bibliographic entries only when supported by the authoritative record;
4. do not change endpoint definitions, preprocessing or result directions while completing citations;
5. record any bibliographic correction as exposition-only and post-outcome.
