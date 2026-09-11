#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "manuscript/EOG_WF_MANUSCRIPT_V1.md"

INTRO_OLD = """Ecological prediction and ecological explanation are often asked to operate on the same spatial observations, but success at one task does not guarantee success at the other. A model may predict heldout observations well while leaving the underlying distribution-forming process weakly identified; conversely, new evidence may eliminate structural or mechanistic hypotheses without yielding a better forecasting representation. [REF] This distinction becomes especially important when distributions are represented by several plausible reachability or accessibility rules rather than by one fitted mechanism."""
INTRO_NEW = """Ecological prediction and ecological explanation are often asked to operate on the same spatial observations, but success at one task does not guarantee success at the other. A model may predict heldout observations well while leaving the underlying distribution-forming process weakly identified; conversely, new evidence may eliminate structural or mechanistic hypotheses without yielding a better forecasting representation (Shmueli, 2010; Houlahan et al., 2017). This distinction becomes especially important when distributions are represented by several plausible reachability or accessibility rules rather than by one fitted mechanism."""

REL_OLD = """EOG-WF is not presented as a replacement for species distribution models, dynamic occupancy models, mechanistic range models, landscape connectivity methods or generic ensemble learning. [REF] Those methods can estimate local occurrence support, occupancy dynamics, dispersal processes, connectivity or predictive combinations directly. EOG instead asks whether a declared finite set of structural worlds remains compatible with accumulating distribution evidence and preserves exact provenance when worlds are eliminated.

Nor does the novelty claim rest on generic threshold graphs, percolation, minimum-cost paths, permutation-invariant summaries, stacking, model averaging or schema validation. [REF] The contribution lies in the domain-specific combination of exact finite-world ecological falsification, strict separation of structural state from its prediction-facing compression, and a response-blind validation protocol that retains failed candidates in the denominator rather than repairing them away."""
REL_NEW = """EOG-WF is not presented as a replacement for species distribution models, dynamic occupancy models, mechanistic range models, landscape connectivity methods or generic ensemble learning. Accessibility constraints, occupied-source proximity, habitat-network occurrence models and suitability-derived connectivity are already established components of ecological prediction (Prugh, 2009; Barve et al., 2011; Schooley & Branch, 2011; Ortiz-Rodríguez et al., 2019; Nelli et al., 2022). Those methods can estimate local occurrence support, occupancy dynamics, dispersal processes, connectivity or predictive combinations directly. EOG instead asks whether a declared finite set of structural worlds remains compatible with accumulating distribution evidence and preserves exact provenance when worlds are eliminated.

Nor does the novelty claim rest on any individual ingredient such as thresholded connectivity, path or network representations, permutation-invariant summaries, model combination or schema validation. Sensitivity of habitat-network predictions to dispersal thresholds is itself an established concern (Ortiz-Rodríguez et al., 2023). The contribution lies in the domain-specific combination of exact finite-world ecological falsification, strict separation of structural state from its prediction-facing compression, and a response-blind validation protocol that retains failed candidates in the denominator rather than repairing them away."""

ABSTRACT_TAIL_OLD = """**Keywords:** ecological forecasting; falsification; reachability; prospective validation; model uncertainty; reproducibility; species distributions

**Data and code for peer review:** all manuscript results are linked to immutable repository contracts, certificates, fingerprints and generated paper-ready assets. A review-ready release/archive should be fixed before submission. [FINAL ARCHIVE/DOI TO ADD]"""
ABSTRACT_TAIL_NEW = """**Data and code for peer review:** all manuscript results are linked to immutable repository contracts, certificates, fingerprints and generated paper-ready assets. A review-ready release/archive should be fixed before submission. [FINAL ARCHIVE/DOI TO ADD]

**Keywords:** ecological forecasting; falsification; model uncertainty; prospective validation; reachability; reproducibility; species distributions"""

REFERENCES = """## References

Barve, N., Barve, V., Jiménez-Valverde, A., Lira-Noriega, A., Maher, S.P., Peterson, A.T., Soberón, J. & Villalobos, F. (2011). The crucial role of the accessible area in ecological niche modeling and species distribution modeling. *Ecological Modelling*, 222, 1810–1819. https://doi.org/10.1016/j.ecolmodel.2011.02.011

Houlahan, J.E., McKinney, S.T., Anderson, T.M. & McGill, B.J. (2017). The priority of prediction in ecological understanding. *Oikos*, 126, 1–7. https://doi.org/10.1111/oik.03726

Nelli, L., Schehl, B., Stewart, R.A., Scott, C., Ferguson, S., MacMillan, S. & McCafferty, D.J. (2022). Predicting habitat suitability and connectivity for management and conservation of urban wildlife: A real-time web application for grassland water voles. *Journal of Applied Ecology*, 59, 1072–1085. https://doi.org/10.1111/1365-2664.14118

Ortiz-Rodríguez, D.O., Guisan, A., Holderegger, R. & van Strien, M.J. (2019). Predicting species occurrences with habitat network models. *Ecology and Evolution*, 9, 10457–10471. https://doi.org/10.1002/ece3.5567

Ortiz-Rodríguez, D.O., Guisan, A. & van Strien, M.J. (2023). Sensitivity of habitat network models to changes in maximum dispersal distance. *PLoS ONE*, 18, e0293966. https://doi.org/10.1371/journal.pone.0293966

Prugh, L.R. (2009). An evaluation of patch connectivity measures. *Ecological Applications*, 19, 1300–1310. https://doi.org/10.1890/08-1524.1

Schooley, R.L. & Branch, L.C. (2011). Habitat quality of source patches and connectivity in fragmented landscapes. *Biodiversity and Conservation*, 20, 1611–1623. https://doi.org/10.1007/s10531-011-0049-5

Shmueli, G. (2010). To explain or to predict? *Statistical Science*, 25, 289–310. https://doi.org/10.1214/10-STS330

"""

CHECK_OLD = "- [ ] references are added for literature-positioning statements marked `[REF]`;"
CHECK_NEW = "- [x] literature-positioning statements are supported by verified references and no citation placeholders remain;"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one frozen match, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    if "## References" in text:
        raise RuntimeError("References section already exists; refuse second patch")
    if text.count("[REF]") != 4:
        raise RuntimeError(f"expected exactly four [REF] strings including the checklist marker, got {text.count('[REF]')}")

    text = replace_once(text, INTRO_OLD, INTRO_NEW, "introduction reference patch")
    text = replace_once(text, REL_OLD, REL_NEW, "relationship reference patch")
    text = replace_once(text, ABSTRACT_TAIL_OLD, ABSTRACT_TAIL_NEW, "MEE abstract-tail order patch")
    text = replace_once(text, "## Methods", "## Materials and Methods", "MEE methods-heading patch")
    text = replace_once(text, CHECK_OLD, CHECK_NEW, "checklist reference patch")
    text = replace_once(text, "## Submission-boundary checklist", REFERENCES + "## Submission-boundary checklist", "references insertion")

    if "[REF]" in text:
        raise RuntimeError("reference marker survived deterministic patch")
    PATH.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
