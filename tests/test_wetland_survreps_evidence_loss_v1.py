"""Mathematical negative controls and row-resolution tests for survreps audit."""
import math
import pytest
from benchmarks import wetland_survreps_evidence_loss_v1 as m


def test_exact_with_replacement_positive_loss():
    assert m.loss_probability(2,1)==2**(-20)
    assert m.loss_probability(20,20)==0
    assert math.isclose(m.loss_probability(15,1),(14/15)**20)


def test_exact_without_replacement_loss():
    assert math.isclose(m.loss_probability(21,1),1/21)
    assert m.loss_probability(21,2)==0
    assert m.loss_probability(21,21)==0


def test_invalid_inputs_fail_closed():
    for n,k in ((0,0),(10,0),(10,11)):
        with pytest.raises(ValueError):
            m.loss_probability(n,k)
    with pytest.raises(TypeError):
        m.loss_probability(3,1.5)


def test_positive_loss_is_monotone_with_k():
    for n in (6,15,20,21,24,50):
        probs=[m.loss_probability(n,k) for k in range(1,n+1)]
        assert all(0<=x<=1 for x in probs)
        assert all(a>=b for a,b in zip(probs,probs[1:]))


def test_description_preserves_raw_positive_evidence():
    rows=[
        {"site":"A","surv":"A:bottletrap:1","Pelobates fuscus":"1"},
        {"site":"A","surv":"A:visual:2","Pelobates fuscus":"0"},
        {"site":"B","surv":"B:visual:3","Pelobates fuscus":"0"},
    ]
    x=m.describe(rows,[{"site":"A"},{"site":"B"}],["Pelobates fuscus"])
    assert x["source_site_count"]==2
    assert x["20_row_normalized_total"]==40
    assert x["observed_positive_site_species_pairs"]==1
    assert math.isclose(x["expected_lost_positive_site_species_pairs"],2**(-20))


def test_duplicate_row_interpretation_is_not_silently_fixed():
    def row(sid,sp):
        return {"surv":sid,"site":sid[:1],"Pelobates fuscus":str(sp)}
    rows=[row("A1",0),row("A1",1),row("B1",0),row("B1",1),row("C1",1)]
    possibilities=list(m.hypothetical_one_row_resolutions(rows,["Pelobates fuscus"]))
    assert len(possibilities)==4
    assert all(len(x)==3 for x in possibilities)
    assert sorted(sum(int(z["Pelobates fuscus"]) for z in x) for x in possibilities)==[1,2,2,3]
