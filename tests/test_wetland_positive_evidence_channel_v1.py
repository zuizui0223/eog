"""Source-positive-only compatibility and 256-seed reconciliation controls."""
import pytest
from benchmarks import wetland_positive_evidence_channel_v1 as m


def test_eog_positive_only_world_contract_direction():
    source={"a","b"}
    sampled={"a"}
    universe=[{"a"},{"a","b"},{"a","b","c"},{"b"},set()]
    w_raw={i for i,w in enumerate(universe)
           if m.world_is_positive_compatible(w,source)}
    w_sample={i for i,w in enumerate(universe)
              if m.world_is_positive_compatible(w,sampled)}
    assert w_raw == {1,2}
    assert w_sample == {0,1,2}
    assert w_raw <= w_sample
    assert w_raw == {i for i,w in enumerate(universe)
                     if m.world_is_positive_compatible(w,
                         sampled | (source-sampled))}


def test_missing_positive_is_not_observed_true_absence():
    source={"site1/rare","site2/common"}
    sampled={"site2/common"}
    assert source-sampled=={"site1/rare"}
    assert m.world_is_positive_compatible(source,sampled)
    # A source-consistent world must not be excluded just because
    # the processed table omitted the rare positive.
    assert m.world_is_positive_compatible(source,source)


def make_synthetic_input(all_missing=False):
    sources={
        "published_q1":{("A","frog"),("B","frog")},
        "published_q2":{("A","frog")}
    }
    pairs=[]
    summaries=[]
    for seed in m.SEEDS:
        missing=all_missing or seed%2==1
        pairs.extend([
            {"cohort":"published_q1","seed":str(seed),
             "site":"A","species":"frog","retained_after_sampling":"1"},
            {"cohort":"published_q1","seed":str(seed),
             "site":"B","species":"frog",
             "retained_after_sampling":"0" if missing else "1"},
            {"cohort":"published_q2","seed":str(seed),
             "site":"A","species":"frog","retained_after_sampling":"1"}
        ])
        summaries.append({
            "seed":str(seed),
            "q1_lost_positive_site_species":str(int(missing)),
            "q2_lost_positive_site_species":"0"
        })
    return sources,pairs,summaries


def test_all_seed_source_reconciliation_and_ever_missing_partition():
    sources,pairs,summaries=make_synthetic_input()
    r=m.reconcile(sources,pairs,summaries)
    q1=r["cohorts"]["published_q1"]
    assert q1["source_positive_site_species_pairs"]==2
    assert q1["retained_at_every_one_of_256_seeds"]==1
    assert q1["variable_between_256_seed_inputs"]==1
    assert q1["omitted_at_all_256_seeds"]==0
    assert q1["seeds_with_any_native_positive_omission"]==128
    assert all(v["source_recovered_positive_count"]==2
               for v in q1["per_seed"])
    assert r["cohorts"]["published_q2"]["retained_at_every_one_of_256_seeds"]==1


def test_never_retained_does_not_become_source_absence():
    sources,pairs,summaries=make_synthetic_input(all_missing=True)
    r=m.reconcile(sources,pairs,summaries)
    q1=r["cohorts"]["published_q1"]
    assert q1["retained_at_every_one_of_256_seeds"]==1
    assert q1["variable_between_256_seed_inputs"]==0
    assert q1["omitted_at_all_256_seeds"]==1
    assert all(v["source_recovered_positive_count"]==2 for v in q1["per_seed"])


def test_seed_coverage_or_extra_positive_fails_closed():
    sources,pairs,summaries=make_synthetic_input()
    bad=[dict(p) for p in pairs[:-1]]
    with pytest.raises(ValueError,match="incomplete"):
        m.reconcile(sources,bad,summaries)
    bad=[dict(p) for p in pairs]
    bad[0]["site"]="OTHER"
    with pytest.raises(ValueError,match="non-source-positive"):
        m.reconcile(sources,bad,summaries)


def test_summary_count_disagreement_fails_closed():
    sources,pairs,summaries=make_synthetic_input()
    bad=[dict(z) for z in summaries]
    bad[0]["q1_lost_positive_site_species"]="99"
    with pytest.raises(ValueError,match="disagrees"):
        m.reconcile(sources,pairs,bad)
