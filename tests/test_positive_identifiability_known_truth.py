from benchmarks.positive_identifiability_known_truth import run_benchmark


def test_positive_information_ceiling_and_asymmetric_identification():
    result = run_benchmark()
    rows = {(r["case"], r["generating_truth"]): r for r in result["results"]}
    assert len(rows) == 10
    assert result["subsets_checked"] == 20
    for truth in ("left", "right"):
        row = rows["disjoint", truth]
        assert row["survivors_at_positive_ceiling"] == [truth]
        assert row["minimum_positive_count_for_truth_identification"] == 1
    assert rows["nested", "narrow"]["survivors_at_positive_ceiling"] == [
        "broad",
        "narrow",
    ]
    assert (
        rows["nested", "narrow"]["minimum_positive_count_for_truth_identification"]
        is None
    )
    assert rows["nested", "broad"]["survivors_at_positive_ceiling"] == ["broad"]
    assert (
        rows["nested", "broad"]["minimum_positive_count_for_truth_identification"] == 1
    )
    for truth in ("fast", "slow"):
        row = rows["same_support", truth]
        assert row["survivors_at_positive_ceiling"] == ["fast", "slow"]
        assert row["status"] == "not_identifiable_at_positive_ceiling"
    for truth in ("left", "right"):
        row = rows["restricted_survey", truth]
        assert row["observable_positives"] == []
        assert row["survivors_at_positive_ceiling"] == ["left", "right"]
    assert rows["omitted_truth", "outside"]["status"] == "declared_universe_falsified"
    assert rows["omitted_truth", "outside"]["survivors_at_positive_ceiling"] == []
    hidden = rows["omitted_truth_hidden", "outside"]
    assert hidden["status"] == "unique_compatible_world_with_omitted_truth"
    assert hidden["survivors_at_positive_ceiling"] == ["left"]
    assert hidden["minimum_positive_count_for_truth_identification"] is None


def test_known_truth_benchmark_is_repeatable():
    assert run_benchmark() == run_benchmark()
