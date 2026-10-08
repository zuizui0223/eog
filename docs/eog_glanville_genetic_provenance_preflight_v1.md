# Glanville genetics × occupancy: source-origin observation qualification v1

**Decision: HOLD_SOURCE_DIRECTION_NOT_IDENTIFIED_AND_NOT_FRESH.**

This is a **metadata-only** comparison of two public scientific archives from the *same* Glanville fritillary (*Melitaea cinxia*) metapopulation in Åland, Finland. The second archive is a separate *data product* but **not an independent ecological system, a new EOG-WF heldout trial, or first-arrival source ground truth**.

No genotype rows, family reconstructions, new biological responses or original occupancy outcomes were read, re-fit or scored in this preflight. The frozen Glanville EOG-WF prediction result remains untouched.

Machine catalog: `validation/eog_virtual_world_ecology_synthesis_v1/glanville_genetic_origin_preflight_v1.json`.

## 1. A useful externally published data layer has been located

**Previous EOG Glanville occupancy archive**

- Dryad [10.5061/dryad.ksn02v707](https://doi.org/10.5061/dryad.ksn02v707), transported from Zenodo record 4987060.
- Its archive was already checksum verified, and the EOG registry separated the spatial/patch files from `survey_data.tsv`. It contains a 4,656-patch frozen network and annual survey-recorded colonization outcomes.
- **Frozen original split:** transitions **1999–2000** through **2011–2012** were calibration; **2012–2013** through **2017–2018** were heldout. The existing Glanville predictive response was consumed and the result is frozen. See `validation/glanville_eogwf/README.md`, its Gate 2 temporal contract and its authoritative outcome provenance.

**An independent archive about genetic kinship, but within the same butterfly population**

- Fountain et al., *Evolutionary Applications*, DOI [10.1111/eva.12552](https://doi.org/10.1111/eva.12552), archived at [Dryad 10.5061/dryad.d461s](https://doi.org/10.5061/dryad.d461s) and [Zenodo record 5010194](https://zenodo.org/records/5010194).
- Published sampling covers **2007–2012**, **3,732 larval family groups**, with genotyping using **272 SNPs**. The analysis reconstructed full-sib families found across local populations to estimate **effective female breeding dispersal** (mean scale around **1 km**), comparing against previous dispersal measurements.
- Public source inventory advertises a separate README and a compressed `supplementary-data-COLONY2.tar.gz` package (inner names described as `master-input.csv`, `master-output.csv`, `colony-input-master`, `colony-output-master-trimmed`). The actual genetic file headers and patch identifiers **have not been inspected** here; no cross-archive patch-ID concordance is established.

The original **1999–2012 calibration period** is separate from the **2013–2018 heldout target years**. **This is NOT a new independent external validation.**

The genetic source's sampling window ends in **2012**, before the EOG-WF heldout target years **2013–2018**. Even perfect patch-ID concordance could **not retrospectively turn it into independently observed first-source identities for the EOG heldout years**.

## 2. Formal distinction: sibling movement does not orient source history

For a reconstructed maternal family found in patches A and B during one larval season, the publicly reported source of evidence is the **unordered cross-patch sibship relation**:

```text
Observation: {A, B} belongs to one inferred maternal full-sib family

Possible history H1: female laid eggs at A → then B
Possible history H2: female laid eggs at B → then A

Same observation in H1 and H2.
Different ordered movement and "first source" targets.
```

The paper's inference of **breeding dispersal between occupied patches** remains meaningful. But without independently dated oviposition order, longitudinal parent tracking or equivalent validated provenance markers, the direction of movement **A → B versus B → A** and the *first-arrival source for a recipient patch* are **not identified** by the undirected full-sib link alone. An observed sib pair also does not establish that either patch had just been colonized rather than previously occupied.

EOG v23's idealized `P_node` action returns a **directed earliest-arrival source tag** under each constructed history. A genetic full-sib link across patches is a **different observation class**, not a direct empirical realization of `P_node`.

A unit test explicitly demonstrates that swapping the direction leaves the unordered sibship observation invariant while changing the directed first-origin target.

## 3. Prior art prevents a simple 'we discovered that colonists come from multiple sources' claim

- [Austin et al. (2011)](https://doi.org/10.1111/j.1600-0706.2010.18992.x) already examined the size and genetic composition of colonizing propagules in this butterfly metapopulation, comparing with a dispersal-model baseline.
- [Hanski et al. (2017)](https://doi.org/10.1038/ncomms14504) studied spatial configuration, long-term colonization/extinction and dispersal-associated genotypes.
- [Fountain et al. (2017/2018)](https://doi.org/10.1111/eva.12552) already used reconstructed full-sib kinship to estimate between-patch effective female dispersal.

Neither **patch connectivity**, **kinship-based female movement**, **multiple colonist sources**, nor their association with population turnover is a new EOG discovery.

## 4. Explicit pre-response qualification

| Evidence or validity gate | Assessment |
|---|---|
| Temporal occupancy + independent genetics on one biological system | **Metadata supports two source products** |
| Exact file identity of older occupancy archive | **Previously frozen and checked** |
| Exact file identity / digest verified for genetics ZIP | **Not checked** (only source-advertised MD5 available) |
| Physical genetic columns and patch IDs matched to EOG registry | **Unverified** |
| Same-year maternal sibling pair determines movement direction | **No** |
| Exact earliest founding source of a newly established patch | **Not provided by public study description** |
| Genetic-origin observations in original 2013–2018 heldout outcomes | **No** |
| New external ecological replication independent of consumed Glanville | **No** |

**Current decision:** `HOLD_SOURCE_DIRECTION_NOT_IDENTIFIED_AND_NOT_FRESH`. This is **not** a negative genetic, ecological or EOG predictive result and **does not enter** the frozen 3 scored / 31 scientific STOP / 3 administrative exclusion EOG-WF denominator.

### What this archived genetic dataset could still contribute

A separately approved **retrospective, calibration-era** analysis could potentially use cross-patch maternal sib links to check the *undirected spatial reachability or dispersal-kernel scale* of a frozen network. It must first verify actual physical archive bytes, source-ID concordance, biological sampling windows, sample opportunity and source coverage—without peeking at genotype/kinship outcomes to choose what to model. This is a **weaker validation target** than identifying activation history, and would need a prior-art comparator and its own transparent retrospective label.

It **cannot** be promoted to a fresh confirmation of the previously closed Glanville EOG prediction, nor turned into empirical validation of the v23 ideal source-provenance observation without additional independent direction and source-timing information.

## 5. What would qualify a true dual-channel ecological test?

Require a **single externally identified patch system** with (a) a time-stamped patch and survey-opportunity register, (b) detection-aware colonization / source-loss outcomes, and (c) source-directed tracking or genetic parentage with time and identification uncertainty adequate to distinguish the first source of recipients.

Freeze the time split, baseline (metapopulation occupancy plus graph/IFM connectivity), source assignment probability/error model and STOP conditions before the relevant biological outcomes are read. If only same-cohort sibling dyads exist, test undirected effective movement, **not** historical provenance.

**Paper decision remains HOLD**: no new third EOG ecological manuscript, no new candidate search to rescue the latest synthetic result, no resumed fitting on the closed Glanville system.

The programmatic source/target distinction is protected in `tests/test_eog_glanville_genetic_provenance_preflight_v1.py`.
