import importlib
import tomllib
from pathlib import Path

import eog.v2.cli as cli


EXPECTED_V2_SCRIPTS = {
    "eog-v2-genetic-validate": "eog.v2.cli:genetic_validate_main",
    "eog-v2-occurrence-freeze": "eog.v2.cli:occurrence_freeze_main",
    "eog-v2-occurrence-validate": "eog.v2.cli:occurrence_validate_main",
}


def test_all_v2_console_scripts_route_through_one_v2_facade():
    project = tomllib.loads(Path("pyproject.toml").read_text())
    scripts = project["project"]["scripts"]
    observed = {name: value for name, value in scripts.items() if name.startswith("eog-v2-")}
    assert observed == EXPECTED_V2_SCRIPTS


def test_v2_console_entry_points_resolve_to_callables():
    for spec in EXPECTED_V2_SCRIPTS.values():
        module_name, attribute = spec.split(":", 1)
        module = importlib.import_module(module_name)
        assert callable(getattr(module, attribute))


def test_cli_facade_keeps_commands_explicit_and_small():
    assert cli.__all__ == [
        "genetic_validate_main",
        "occurrence_freeze_main",
        "occurrence_validate_main",
    ]
