"""Check exact, non-preregistered descriptive arithmetic for source-geometry readout value."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
MARGINAL = DIRECTORY / "readout_marginal_value_v1.json"
DOC = ROOT / "docs/eog_history_readout_crossover_v23.md"


def test_marginal_values_are_derived_only_from_existing_frozen_receipt():
    item=json.loads(MARGINAL.read_text(encoding="utf-8"))
    path=ROOT / item["source"]
    raw=path.read_bytes()
    git_blob=hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    assert git_blob==item["source_git_blob_sha"]
    source=json.loads(raw.decode("utf-8"))
    assert source["status"]=="POST_RESULT_EXPLORATORY_NOT_PREREGISTERED"
    assert item["status"]=="POST_RESULT_DESCRIPTIVE_ARITHMETIC_NOT_PREREGISTERED"
    assert item["parent_pr"]==614
    for layout in ("clustered","dispersed"):
        vals=item["computed"][layout]
        src=source["identification_by_readout"]
        n=vals["n"]
        assert n==source["matched_landscapes"]==384
        occ=src["occupancy_only"][layout]
        prov=src["provenance_only"][layout]
        both=src["combined"][layout]
        assert both>=max(occ,prov)
        assert vals["occupancy_identified"]==occ
        assert vals["provenance_identified"]==prov
        assert vals["combined_identified"]==both
        assert vals["occupancy_unresolved"]==n-occ
        assert vals["provenance_unresolved"]==n-prov
        assert vals["additional_by_provenance_after_occupancy"]==both-occ
        assert vals["additional_by_occupancy_after_provenance"]==both-prov
        assert vals["remaining_unresolved_combined"]==n-both
        assert math.isclose(
            vals["fraction_unresolved_occupancy_rescued_by_provenance"],
            (both-occ)/(n-occ), rel_tol=1e-14
        )
        assert math.isclose(
            vals["fraction_unresolved_provenance_rescued_by_occupancy"],
            (both-prov)/(n-prov), rel_tol=1e-14
        )


def test_no_premature_empirical_or_sampling_claims():
    item=json.loads(MARGINAL.read_text(encoding="utf-8"))
    x=item["computed"]
    assert x["clustered"]["additional_by_provenance_after_occupancy"]==107
    assert x["dispersed"]["additional_by_provenance_after_occupancy"]==1
    assert x["clustered"]["occupancy_unresolved"]==153
    assert x["dispersed"]["occupancy_unresolved"]==36
    assert len(item["boundaries"])>=5
    assert any("not an ecological sample" in s for s in item["boundaries"])
    s=DOC.read_text(encoding="utf-8")
    assert "107/153 = 69.9%" in s
    assert "1/36 = 2.8%" in s
    assert "ceiling" in s.lower()
    assert "equally priced field assay" in s
