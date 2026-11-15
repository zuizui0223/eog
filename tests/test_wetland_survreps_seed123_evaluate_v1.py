"""Offline fail-closed tests for authentic R sampling map evaluation."""
import pytest
from benchmarks import wetland_survreps_seed123_evaluate_v1 as m


def _synthetic_original():
    return [
        {"site":"A", "surv":"A:1", "date":"2024-01-01", "method":"visual",
         "Pelobates fuscus":"1"},
        {"site":"A", "surv":"A:2", "date":"2024-01-02", "method":"visual",
         "Pelobates fuscus":"0"},
        {"site":"B", "surv":"B:3", "date":"2024-01-03", "method":"visual",
         "Pelobates fuscus":"1"},
    ]


def _synthetic_mapping(rows):
    mapping = []
    for site, src_idx in (("A", 2), ("B", 3)):
        row = rows[src_idx-1]
        for p in range(1, 21):
            mapping.append({
                "site":site, "surv":row["surv"], "date":row["date"],
                "method":row["method"],"eog_native_row_index":str(src_idx),
                "eog_replay_repeat_index":str(p),
            })
    return mapping


def test_replay_detects_lost_native_positive_and_duplicates(monkeypatch):
    rows = _synthetic_original()
    monkeypatch.setitem(m.EXPECTED, "published_q1", (2, 3, 2))
    out = m.evaluate_one(rows, [{"site":"A"}, {"site":"B"}],
                         ["Pelobates fuscus"], _synthetic_mapping(rows),
                         "published_q1")
    assert out["native_positive_species_site_pairs"] == 2
    assert out["seed123_positive_species_site_pairs"] == 1
    assert out["lost_species_site_pairs"] == [
        {"site":"A", "species":"Pelobates fuscus"}
    ]
    assert out["repeated_source_row_positions"] == 38
    assert out["distinct_native_source_rows_selected"] == 2


def test_cross_site_or_wrong_source_index_fails_closed(monkeypatch):
    rows = _synthetic_original()
    monkeypatch.setitem(m.EXPECTED, "published_q1", (2, 3, 2))
    map_rows = _synthetic_mapping(rows)
    map_rows[0]["eog_native_row_index"] = "3"
    with pytest.raises(ValueError, match="identity drift"):
        m.evaluate_one(rows,[{"site":"A"},{"site":"B"}],
                       ["Pelobates fuscus"], map_rows,"published_q1")


def test_duplicate_virtual_repeat_index_fails_closed(monkeypatch):
    rows = _synthetic_original()
    monkeypatch.setitem(m.EXPECTED, "published_q1", (2, 3, 2))
    map_rows = _synthetic_mapping(rows)
    map_rows[1]["eog_replay_repeat_index"] = "1"
    with pytest.raises(ValueError, match="reused"):
        m.evaluate_one(rows,[{"site":"A"},{"site":"B"}],
                       ["Pelobates fuscus"], map_rows,"published_q1")


def test_runtime_seed_kind_requires_verifiable_r(tmp_path):
    p=tmp_path/"runtime.txt"
    p.write_text("seed=123\nreps=20\nR_version=R version 4.4.3\nRNGkind=Mersenne-Twister;Inversion;Rejection\n")
    assert m.read_runtime(p)["seed"] == "123"
    p.write_text("seed=321\nreps=20\nR_version=R version 4.4.3\nRNGkind=Mersenne-Twister;Inversion;Rejection\n")
    with pytest.raises(ValueError, match="seed123"):
        m.read_runtime(p)
