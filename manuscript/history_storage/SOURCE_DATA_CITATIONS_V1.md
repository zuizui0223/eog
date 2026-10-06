# History-storage manuscript — source data and provenance v1

## Plant microbiome source

Primary study:

Leopold DR & Busby PE (2020), *Current Biology* 30: 3260–3266.e5.  
Article DOI: `10.1016/j.cub.2020.06.011`.

Analysis source used by EOG:

- GitHub repository: `dleopold/Populus_priorityEffects`;
- pinned commit: `d8082daabfccccf3bcbdd631b4438f44c04014c1`;
- archived release: Zenodo v1.2;
- Zenodo DOI: `10.5281/zenodo.3872145`;
- raw sequencing BioProject: `PRJNA605581`.

Scored file identities:

- `data/Sample_data.csv`:
  `dcdc54ff26013714ab29ddce77211ac3b0043938`;
- `output/compiled/OTU.table.csv`:
  `8784a02f7617a7cc207e3da8c7798753d082a4b6`;
- `output/tabs/bias.csv`:
  `45167a953653e7706e8a515516309bc6afec4cf5`;
- `data/rust_measurements.csv`:
  `a98138a2355f72b6946ba34138696d971c2cab37`.

### Metadata correction

The frozen v28 protocol contains `source.dryad_doi = 10.5061/dryad.7p2cv`.

That field is a source-metadata error. It belongs to a different wood-decomposer dataset
screened later in the EOG programme and was never used by the v28 scorer.

The v28 protocol is kept immutable after scoring. The correction is recorded in:

`validation/eog_original_idea_leopold_history_retention_v28/source_metadata_correction_v1.json`.

The error has **no scoring impact** because the v28 pipeline materialized the pinned
GitHub files above and verified their blob identities.

## Grassland source

Primary study:

Alonso-Crespo IM, Weidlich EWA, Temperton VM & Delory BM (2023),
*Oikos* 2023(1): e08886.  
Article DOI: `10.1111/oik.08886`.

Data source used by EOG:

- GitHub repository: `BenjaminDelory/PE_Rhizobox_2017_data`;
- pinned commit: `438f028fb2e1713a9e253be9e07df0833b491f47`;
- source article data archive: Zenodo;
- data DOI: `10.5281/zenodo.5713397`.

Scored file identities:

- `Data/Data_shoot_biomass_RZ_PE_2017.txt`:
  `4fb311a7bbe9bb14cdac77bbc889e2dcbb9cfedc`;
- `Data/Data_root_biomass_RZ_PE_2017.txt`:
  `d7822cefa35f41b144a87c0184f6029e9726bca9`;
- `Data/README.txt`:
  `31d7398c8f5259ad48095324ab575575a6b39312`.

## Submission rule

The manuscript and cover letter should cite the original articles for biological
provenance and cite the public data/code archives in Data Availability.

Do not cite `10.5061/dryad.7p2cv` as the source of the 2020 Populus microbiome
reanalysis.
