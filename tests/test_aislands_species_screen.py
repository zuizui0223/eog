from eog.aislands_species_screen import summarize_species


def test_screen_uses_unique_islands_not_repeated_lists():
    island_rows = [
        {"list_ID": "L1", "island_ID": "I1"},
        {"list_ID": "L2", "island_ID": "I1"},
        {"list_ID": "L3", "island_ID": "I2"},
        {"list_ID": "L4", "island_ID": "I3"},
        {"list_ID": "L5", "island_ID": "I4"},
    ]
    species_rows = [
        {"List_ID": "L1", "Species_update": "Alpha beta", "Native": "1", "Naturalised": "0"},
        {"List_ID": "L2", "Species_update": "Alpha beta", "Native": "1", "Naturalised": "0"},
        {"List_ID": "L3", "Species_update": "Alpha beta", "Native": "1", "Naturalised": "0"},
        {"List_ID": "L4", "Species_update": "Gamma delta", "Native": "1", "Naturalised": "0"},
    ]
    rows = summarize_species(
        island_rows,
        species_rows,
        min_present_islands=2,
        min_absent_islands=2,
        min_prevalence=0.25,
        max_prevalence=0.75,
    )
    by_species = {row["species"]: row for row in rows}
    assert by_species["Alpha beta"]["n_surveyed_islands"] == 4
    assert by_species["Alpha beta"]["n_present_islands"] == 2
    assert by_species["Alpha beta"]["n_absent_islands"] == 2
    assert by_species["Alpha beta"]["distribution_eligible"] == 1
    assert by_species["Gamma delta"]["distribution_eligible"] == 0


def test_screen_reports_status_without_using_it_for_distribution_eligibility():
    island_rows = [
        {"list_ID": "L1", "island_ID": "I1"},
        {"list_ID": "L2", "island_ID": "I2"},
        {"list_ID": "L3", "island_ID": "I3"},
        {"list_ID": "L4", "island_ID": "I4"},
    ]
    species_rows = [
        {"List_ID": "L1", "Species_update": "Alpha beta", "Native": "", "Naturalised": "1", "Status_APC": "native", "Family": "Alphaaceae"},
        {"List_ID": "L2", "Species_update": "Alpha beta", "Native": "1", "Naturalised": "", "Status_APC": "native", "Family": "Alphaaceae"},
    ]
    row = summarize_species(
        island_rows,
        species_rows,
        min_present_islands=2,
        min_absent_islands=2,
        min_prevalence=0.25,
        max_prevalence=0.75,
    )[0]
    assert row["distribution_eligible"] == 1
    assert row["status_apc_values"] == "native"
    assert row["family_values"] == "Alphaaceae"
    assert row["native_status_values"] == "1"
    assert row["naturalised_status_values"] == "1"


def test_primary_defaults_keep_small_range_taxa():
    island_rows = [
        {"list_ID": f"L{i}", "island_ID": f"I{i}"}
        for i in range(1, 101)
    ]
    species_rows = [
        {"List_ID": f"L{i}", "Species_update": "Small range species"}
        for i in range(1, 11)
    ]
    row = summarize_species(island_rows, species_rows)[0]
    assert row["prevalence"] == 0.1
    assert row["n_present_islands"] == 10
    assert row["n_absent_islands"] == 90
    assert row["distribution_eligible"] == 1


def test_screen_preserves_conflicting_apc_status_for_manual_resolution():
    island_rows = [
        {"List_ID": "L1", "Island_ID": "I1"},
        {"List_ID": "L2", "Island_ID": "I2"},
        {"List_ID": "L3", "Island_ID": "I3"},
        {"List_ID": "L4", "Island_ID": "I4"},
    ]
    species_rows = [
        {"List_ID": "L1", "Species_update": "Alpha beta", "Status_APC": "native"},
        {"List_ID": "L2", "Species_update": "Alpha beta", "Status_APC": "uncertain"},
    ]
    row = summarize_species(
        island_rows,
        species_rows,
        min_present_islands=2,
        min_absent_islands=2,
    )[0]
    assert row["status_apc_values"] == "native|uncertain"
