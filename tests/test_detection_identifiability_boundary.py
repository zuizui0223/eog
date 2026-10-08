from benchmarks.detection_identifiability_boundary import run_benchmark


def test_nondetection_requires_an_explicit_observation_contract():
    report = run_benchmark()
    assert report["histories_checked"] == 42
    for row in report["results"]:
        zeros = row["histories"][0]
        if row["case"] == "perfect_detection":
            assert zeros["compatible_world_ids"] == ["absent"]
            assert row["histories"][-1]["compatible_world_ids"] == ["occupied"]
            for history in row["histories"][1:-1]:
                assert history["status"] == "contract_falsified"
        else:
            assert zeros["compatible_world_ids"] == ["absent", "occupied"]
        if row["case"] == "imperfect_detection":
            assert zeros["likelihoods"]["occupied"] == f"1/{2 ** row['visits']}"
            for history in row["histories"][1:]:
                assert history["compatible_world_ids"] == ["occupied"]
        if row["case"] == "uninformative_detection":
            assert all(
                h["status"] == "contract_falsified" for h in row["histories"][1:]
            )


def test_detection_boundary_is_repeatable():
    assert run_benchmark() == run_benchmark()
