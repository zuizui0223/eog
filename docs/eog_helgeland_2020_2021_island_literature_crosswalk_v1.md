# Helgeland: 2020 eight named populations versus 2021 eleven named populations

**Qualified:** peer-reviewed *names and research sampling-window definitions* only. **Not qualified:** equivalence of numeric codes in either Dryad CSV, field effort for non-detections, actual raw population trajectories or an EOG forecast.

## Primary study methods

[Niskanen et al. (2020), PNAS](https://pmc.ncbi.nlm.nih.gov/articles/PMC7322018/) (doi:10.1073/pnas.1909599117), *Samples and Genotyping*, includes **five farm islands** (Aldra, Gjerøy, Hestmannøy, Indre Kvarøy, Nesøy) and **three nonfarm islands** (Myken, Selvær, Træna). Genotyped adult samples covered **1998–2013** in the five farm populations, **2003–2013** in Selvær and Træna, and **2004–2013** in Myken. **These are study-specific adult genotype sampling windows**, not evidence that field surveys outside those periods were absent or that observed population size was zero.

[Ranke et al. (2021), Journal of Animal Ecology](https://doi.org/10.1111/1365-2656.13580), section *2.1 Study populations*, lists **eleven** populations in the 1993–2014 study: the same eight plus farm-island Lurøy-Onøy and nonfarm islands Lovund and Sleneset. It reports annual population and dispersal histories, but its definitions note only some habitat/year/site combinations had full recruit-production coverage. In particular, it reports **no complete breeding-season nest searches at Lurøy-Onøy** and none on nonfarm islands before 1999, with 1994 survey starts for three islands.

### The paper-to-paper name mapping

The nominal shared set has exactly **eight** island names. The additional three in the 11-island paper are **Lovund, Lurøy-Onøy, Sleneset**. Neither *Ytre Kvarøy* nor *Sundøy* can be substituted for *Indre Kvarøy*. The 2020 archived source was publicly available by 2020 (Dryad [v8 / 78498](https://doi.org/10.5061/dryad.m0cfxpp10)), while 2021 paper and its reported effects must **not** be treated as a pre-publication-2020 input.

Ranke et al. (2021) already reports **2,192 recorded recruits, 376 inter-island dispersers (17.2%)** for its past observation window. That is an existing published result, **not a new EOG effect**. EOG's incremental value must be demonstrated as independently testable **out-of-time reachable-set or observational-process prediction**, beyond established dispersal studies, and not by rediscovering these counts.

## Immutable machine-readable receipt

`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2020_2021_island_literature_crosswalk_v1.json` freezes the 11 named populations, eight-island subset, farm/nonfarm categories, and paper-specific adult-genotype sample years, plus explicit scientific HOLD flags. A synthetic/documentation-only pytest validates exact set identity and forbids silently filling unsampled years with ecological zero.

No bird observation row, file body or genotype record was accessed by this audit. The 2020 Dryad v8 actual bytes remain unavailable due to **HTTP 401** on unauthenticated REST downloads. Offline verifier merged in [PR #636](https://github.com/zuizui0223/eog/pull/636) is ready for legitimately acquired original v8 files. Peer-reviewed names cannot substitute for an **actual numeric island-code crosswalk** in the frozen files.

## Stop conditions before biological EOG validation

1. Independently hash actual 2020 v8 original files (IDs 358961, 358957 and 358962); do not use 2023 v10 files.
2. Confirm actual CSV schema, island/site naming and calendar years, whether population sizes represent raw observations, estimates or a model summary.
3. Independently map 2020 file island codes/names to the 2026 11-island code dictionary. The 2021 eleven-island paper is *not* itself a guarantee that both archives use the same numeric codes.
4. Qualify surveyed-negative opportunity/effort and freeze model, comparator and outcome access before any true held-out ecological score.

All 2020 genotype sampling-year windows are **sampling design, not occupancy**. The current research remains HOLD for ecological predictions. See [Issue #626](https://github.com/zuizui0223/eog/issues/626).
