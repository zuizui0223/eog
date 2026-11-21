"""Strict source-stage parity and duplicate-weight concentration tests."""
import pytest
from benchmarks import wetland_nmixmatrix_stage_v1 as m


def fixture():
    native=[
        {"site":"A","surv":"A:visual:1","date":"2024-01-01",
         "method":"visual","Pelobates fuscus":"2"},
        {"site":"A","surv":"A:visual:2","date":"2024-01-02",
         "method":"visual","Pelobates fuscus":"0"},
    ]
    mapping=[]
    cells=[]
    for i in range(1,21):
        source=native[0]
        mapping.append({"site":"A","surv":source["surv"],"date":source["date"],
                        "method":"visual","eog_native_row_index":"1",
                        "eog_replay_repeat_index":str(i)})
        cells.append({"cohort":"published_q1","site":"A","repeat_index":str(i),
                      "species":"Pelobates fuscus","source_row_id":"1",
                      "surv":source["surv"],"date":source["date"],
                      "method":"visual","native_count":"2","nmix_count":"2",
                      "nmix_detected":"1"})
    return native,mapping,cells


def test_duplicate_weight_concentration_is_not_nominal_row_count():
    assert m.kish_weight_concentration([1]*20)==1
    assert m.kish_weight_concentration(list(range(20)))==20
    assert m.kish_weight_concentration([1]*10+[2]*10)==2
    with pytest.raises(ValueError,match="empty"):
        m.kish_weight_concentration([])


def test_original_count_two_retained_in_R_nmixmatrix(monkeypatch):
    monkeypatch.setitem(m.EXPECTED,"published_q1",(1,20,1,0))
    native,mapping,cells=fixture()
    out=m.inspect_one(native,["Pelobates fuscus"],mapping,cells,"published_q1")
    assert out["R_nmixmatrix_cells"]==20
    assert out["positive_R_cells_gt_zero"]==20
    assert out["R_cells_with_native_count_gt_one"]==20
    assert out["sum_R_matrix_native_counts"]==40
    assert out["repeated_source_row_positions"]==19
    w=out["Kish_duplicate_weight_concentration_not_inferential_ESS"]
    assert w["mean_per_site"]==1
    assert w["fraction_of_nominal_pseudo_rows"]==0.05


def test_modified_R_cell_count_fails_closed(monkeypatch):
    monkeypatch.setitem(m.EXPECTED,"published_q1",(1,20,1,0))
    native,mapping,cells=fixture()
    cells[10]["nmix_count"]="1"
    with pytest.raises(ValueError,match="retain native count"):
        m.inspect_one(native,["Pelobates fuscus"],mapping,cells,"published_q1")


def test_fabricated_positivity_fails_closed(monkeypatch):
    monkeypatch.setitem(m.EXPECTED,"published_q1",(1,20,1,0))
    native,mapping,cells=fixture()
    cells[2]["nmix_detected"]="0"
    with pytest.raises(ValueError,match="derived binary"):
        m.inspect_one(native,["Pelobates fuscus"],mapping,cells,"published_q1")


def test_source_row_spoofing_fails_closed(monkeypatch):
    monkeypatch.setitem(m.EXPECTED,"published_q1",(1,20,1,0))
    native,mapping,cells=fixture()
    cells[3]["source_row_id"]="2"
    with pytest.raises(ValueError,match="source identity"):
        m.inspect_one(native,["Pelobates fuscus"],mapping,cells,"published_q1")
