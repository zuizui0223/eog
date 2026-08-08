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
        {"List_ID": "L5", "Species_update": "Gamma delta", "Native": "1", "Naturalised": "0"},
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
    assert by_species["Gamma delta"]["distribution_eligible"] == 1


def test_metadata_only_island_does_not_create_universal_absence():
    island_rows = [
        {"list_ID": "L1", "island_ID": "I1"},
        {"list_ID": "L2", "island_ID": "I2"},
        {"list_ID": "L3", "island_ID": "I3"},
    ]
    species_rows = [
        {"List_ID": "L1", "Species_update": "Alpha beta"},
        {"List_ID": "L2", "Species_update": "Gamma delta"},
    ]
    rows = summarize_species(
        island_rows,
        species_rows,
        min_present_islands=1,
        min_absent_islands=1,
    )
    by_species = {row["species"]: row for row in rows}
    assert by_species["Alpha beta"]["n_surveyed_islands"] == 2
    assert by_species["Alpha beta"]["n_present_islands"] == 1
    assert by_species["Alpha beta"]["n_absent_islands"] == 1
    assert by_species["Gamma delta"]["n_surveyed_islands"] == 2
    assert by_species["Gamma delta"]["n_absent_islands"] == 1


def test_screen_reports_status_without_using_it_for_distribution_eligibility():
    island_rows = [
        {"list_ID": "L1", "island_ID": "I1"},
        {"list_ID": "L2", "island_ID": "I2"},
        {"list_ID": "L3", "island_ID": "I3"},
        {"list_ID": "L4", "island_ID": "I4"},
    ]
    species_rows = [
        {"List_ID": "L1", "Species_update": "Alpha beta", "Native": "", "Naturalised": "1"},
        {"List_ID": "L2", "Species_update": "Alpha beta", "Native": "1", "Naturalised": ""},
        {"List_ID": "L3", "Species_update": "Gamma delta", "Native": "1", "Naturalised": ""},
        {"List_ID": "L4", "Species_update": "Gamma delta", "Native": "1", "Naturalised": ""},
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
    ] + [
        {"List_ID": f"L{i}", "Species_update": "Background surveyed species"}
        for i in range(11, 101)
    ]
    rows = summarize_species(island_rows, species_rows)
    by_species = {row["species"]: row for row in rows}
    row = by_species["Small range species"]
    assert row["prevalence"] == 0.1
    assert row["n_present_islands"] == 10
    assert row["n_absent_islands"] == 90
    assert row["distribution_eligible"] == 1
