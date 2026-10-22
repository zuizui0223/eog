from benchmarks.directional_identifiability_boundary import run_benchmark


def test_directional_evidence_and_universe_expansion_boundaries():
    report = run_benchmark()
    rows = {(r["case"], tuple(r["declared_order"])): r for r in report["results"]}
    assert len(rows) == 10
    for order, survivor in ((("C", "X"), "forward"), (("X", "C"), "reverse")):
        assert rows["opposed", order]["not_contradicted"] == [survivor]
        assert rows["ambiguous_extension", order]["supported"] == [survivor]
        assert set(rows["ambiguous_extension", order]["not_contradicted"]) == {
            survivor,
            "symmetric",
        }
        assert set(rows["unresolved_extension", order]["not_contradicted"]) == {
            survivor,
            "no_direction",
        }
        for case in (
            "weight_twin",
            "ambiguous_extension",
            "unresolved_extension",
            "all",
        ):
            assert survivor in rows[case, order]["not_contradicted"]
    assert rows["weight_twin", ("C", "X")]["supported"] == ["forward", "forward_weak"]
    assert rows["weight_twin", ("X", "C")]["not_contradicted"] == ["reverse"]


def test_directional_boundary_report_is_repeatable():
    assert run_benchmark() == run_benchmark()
