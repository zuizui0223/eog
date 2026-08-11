# Verified reference ledger for the structural-reachability manuscript

Verification date: **2026-08-12**

This ledger records only references used in the current Introduction and Methods framing. Bibliographic fields were checked against the publisher article page or the original data repository. Inclusion here verifies citation metadata; it does not imply that a cited method is equivalent to EOG.

| Key | Verified citation | DOI / source | Manuscript role |
|---|---|---|---|
| Valavi2019 | Valavi, R., Elith, J., Lahoz-Monfort, J.J. & Guillera-Arroita, G. (2019). blockCV: An R package for generating spatially or environmentally separated folds for k-fold cross-validation of species distribution models. *Methods in Ecology and Evolution* 10: 225–232. | 10.1111/2041-210X.13107 | Spatial block cross-validation changes evaluation design rather than representing a dispersal process. |
| Mila2022 | Milà, C., Mateu, J., Pebesma, E. & Meyer, H. (2022). Nearest neighbour distance matching Leave-One-Out Cross-Validation for map validation. *Methods in Ecology and Evolution* 13: 1304–1316. | 10.1111/2041-210X.13851 | Distance-aware validation aligns train–test separation with prediction geometry; it remains an evaluation strategy. |
| Bakka2019 | Bakka, H., Vanhatalo, J., Illian, J.B., Simpson, D. & Rue, H. (2019). Non-stationary Gaussian models with physical barriers. *Spatial Statistics* 29: 268–288. | 10.1016/j.spasta.2019.01.002 | Barrier SPDE modifies spatial dependence to respect physical barriers; it is not a source-conditioned propagation estimator. |
| Broms2016 | Broms, K.M., Hooten, M.B., Johnson, D.S., Altwegg, R. & Conquest, L.L. (2016). Dynamic occupancy models for explicit colonization processes. *Ecology* 97: 194–204. | 10.1890/15-0416.1 | Dynamic occupancy can explicitly model colonisation, neighbouring occupancy and long-distance dispersal, so EOG must not claim that occupancy models ignore those processes. |
| Merow2011 | Merow, C., LaFleur, N., Silander, J.A. Jr., Wilson, A.M. & Rubega, M. (2011). Developing dynamic mechanistic species distribution models: Predicting bird-mediated spread of invasive plants across northeastern North America. *The American Naturalist* 178: 30–43. | 10.1086/660295 | Mechanistic SDMs can include population growth and local/long-distance dispersal through heterogeneous landscapes. |
| Adriaensen2003 | Adriaensen, F., Chardon, J.P., De Blust, G., Swinnen, E., Villalba, S., Gulinck, H. & Matthysen, E. (2003). The application of ‘least-cost’ modelling as a functional landscape model. *Landscape and Urban Planning* 64: 233–247. | 10.1016/S0169-2046(02)00242-6 | Least-cost models estimate effective distance through resistance surfaces. |
| McRae2008 | McRae, B.H., Dickson, B.G., Keitt, T.H. & Shah, V.B. (2008). Using circuit theory to model connectivity in ecology, evolution, and conservation. *Ecology* 89: 2712–2724. | 10.1890/07-1861.1 | Circuit theory represents multiple pathways through resistance landscapes and is a strong landscape-specific connectivity comparator. |
| OrtizRodriguez2019 | Ortiz-Rodríguez, D.O., Guisan, A., Holderegger, R. & van Strien, M.J. (2019). Predicting species occurrences with habitat network models. *Ecology and Evolution* 9: 10457–10471. | 10.1002/ece3.5567 | Habitat-network models combine patch suitability, resistance-based edges and network quantities; graph use itself is not novel. |
| Schrader2025 | Schrader, J. et al. (2025). A-Islands: A Vascular Plant Dataset for Biodiversity Research and Species Monitoring on Australian Continental Islands. *Journal of Vegetation Science* 36: e70019. | 10.1111/jvs.70019; data: 10.5281/zenodo.10775809 | Primary description and archive for A-Islands v1.0. |
| Karger2017 | Karger, D.N. et al. (2017). Climatologies at high resolution for the earth’s land surface areas. *Scientific Data* 4: 170122. | 10.1038/sdata.2017.122 | CHELSA climatic-data reference. |
| BrodieNewmark2019 | Brodie, J.F. & Newmark, W.D. (2019). Heterogeneous matrix habitat drives species occurrences in complex, fragmented landscapes. *The American Naturalist* 193: 748–754. | 10.1086/702589; data: 10.5061/dryad.p042h0c | Primary article and archived source package for the Tanzania forest-fragment benchmark. |

## Citation boundary

The manuscript may use these references to delimit method roles, but should not infer the following from citation alone:

- that pointwise SDMs universally ignore space or dispersal;
- that barrier SPDE, dynamic occupancy, least-cost paths, circuit theory, habitat networks and EOG estimate the same quantity;
- that connected frequency is a colonisation or dispersal probability;
- that a positive A-Islands result establishes realised movement;
- that the adverse Tanzania result establishes universal superiority of current flow.
