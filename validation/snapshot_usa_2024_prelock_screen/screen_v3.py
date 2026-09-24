from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import urllib.request

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)
from eog.v2.dryad_public_file import (
    resolve_dryad_published_file,
    verify_dryad_file_bytes,
)
from eog.v2.source_transport_preflight import (
    TransportRouteEvidence,
    evaluate_source_transport_qualification,
)
from validation.snapshot_usa_2024_prelock_screen.screen import (
    PrelockScreenStop,
    _audit_deployments,
    _fetch,
    _fetch_json,
    _https_url,
    _one_file,
    canonical_sha256,
)


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_screen_contract_v3.json"
DEFAULT_OUTPUT = HERE / "prelock_screen_v3_result.json"


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    opener=None,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    source = contract["source_identity"]
    bounds = contract["metadata_bounds"]
    safe_cfg = contract["safe_file"]
    response_cfg = contract["response_file"]
    minima = contract["response_independent_architecture_minima"]

    opener = opener or urllib.request.build_opener()
    ledger: list[dict[str, object]] = []
    base = {
        "schema": "eog.snapshot_usa_2024_prelock_screen_result.v3",
        "screen_id": contract["screen_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "candidate_locked": False,
        "focal_species_selected": False,
        "response_file_requests": 0,
        "response_file_payload_bytes_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }

    try:
        dataset, item = _fetch_json(
            source["api_dataset_url"],
            maximum_bytes=int(bounds["maximum_json_bytes"]),
            opener=opener,
            role="dryad_dataset_metadata",
        )
        ledger.append(item)
        identifier = str(dataset.get("identifier") or "").strip().casefold()
        if identifier not in {
            f"doi:{source['doi']}".casefold(),
            str(source["doi"]).casefold(),
        }:
            raise PrelockScreenStop(
                f"Dryad dataset identifier drift: {identifier!r}"
            )
        if str(dataset.get("title") or "").strip() != source["title"]:
            raise PrelockScreenStop("Dryad dataset title drift")

        links = dataset.get("_links")
        if not isinstance(links, dict):
            raise PrelockScreenStop("Dryad dataset metadata lacks links")
        version_link = links.get("stash:version")
        if not isinstance(version_link, dict):
            raise PrelockScreenStop("Dryad dataset metadata lacks latest version link")
        version_href = str(version_link.get("href") or "").strip()
        if not version_href:
            raise PrelockScreenStop("Dryad latest version href is empty")

        version_url = _https_url("https://datadryad.org", version_href)
        version, item = _fetch_json(
            version_url,
            maximum_bytes=int(bounds["maximum_json_bytes"]),
            opener=opener,
            role="dryad_latest_version_metadata",
        )
        ledger.append(item)
        version_links = version.get("_links")
        if not isinstance(version_links, dict):
            raise PrelockScreenStop("Dryad version metadata lacks links")
        files_link = version_links.get("stash:files")
        if isinstance(files_link, dict) and str(files_link.get("href") or "").strip():
            files_href = str(files_link["href"])
        else:
            files_href = version_href.rstrip("/") + "/files"

        files_url = _https_url("https://datadryad.org", files_href)
        separator = "&" if "?" in files_url else "?"
        files_url = (
            f"{files_url}{separator}per_page="
            f"{int(bounds['maximum_files_per_version'])}"
        )
        files_doc, item = _fetch_json(
            files_url,
            maximum_bytes=int(bounds["maximum_json_bytes"]),
            opener=opener,
            role="dryad_latest_version_files",
        )
        ledger.append(item)

        route_template = str(safe_cfg["public_route_template"])
        route_suffix = "/{file_id}"
        if not route_template.endswith(route_suffix):
            raise PrelockScreenStop(
                "safe-file public route template must end with /{file_id}"
            )
        public_base_url = route_template[: -len(route_suffix)]
        safe_identity = resolve_dryad_published_file(
            _one_file(files_doc, str(safe_cfg["path"])),
            public_base_url=public_base_url,
        )
        response_identity = resolve_dryad_published_file(
            _one_file(files_doc, str(response_cfg["path"])),
            public_base_url=public_base_url,
        )
        if safe_identity.size > int(safe_cfg["maximum_bytes"]):
            raise PrelockScreenStop("safe deployments file exceeds frozen byte bound")

        expected_public = str(safe_cfg["public_route_template"]).format(
            file_id=safe_identity.file_id
        )
        if safe_identity.public_download_url != expected_public:
            raise PrelockScreenStop("derived Dryad public safe-file route drift")

        safe_bytes, item = _fetch(
            safe_identity.public_download_url,
            maximum_bytes=int(safe_cfg["maximum_bytes"]),
            accept="text/csv,*/*",
            opener=opener,
            role="dryad_public_safe_deployments_file",
        )
        ledger.append(item)
        safe_sha = verify_dryad_file_bytes(safe_identity, safe_bytes)

        audit = _audit_deployments(safe_bytes)
        transport = evaluate_source_transport_qualification(
            (
                TransportRouteEvidence(
                    route_id="dryad_current_public_separate_deployments_file",
                    route_type="separate_safe_assets",
                    qualified=True,
                    safe_payload_bytes_opened=len(safe_bytes),
                    response_payload_bytes_opened=0,
                    reason=(
                        "Dryad API metadata froze separate safe/response file identities; "
                        "current anonymous public file_stream retrieved only deployments and "
                        "repository SHA-256 verification passed"
                    ),
                    transport_detail=(
                        f"file_id={safe_identity.file_id}; version={version_href}"
                    ),
                ),
            )
        )

        closed_registry = (
            audit["nodes_with_multiple_exact_coordinates_count"] == 0
        )
        declaration = CandidatePreflightDeclaration(
            attempt_id="snapshot_usa_2024_source_architecture_prelock_v3",
            minimum_nodes=int(minima["minimum_unique_nodes"]),
            minimum_outer_units=int(minima["minimum_outer_units"]),
            minimum_repeated_nodes=int(minima["minimum_repeated_nodes"]),
            require_separate_geometry_and_response=True,
            require_coordinate_geometry=True,
            require_closed_analysis_registry=True,
            require_response_blind_transport_qualification=True,
        )
        evidence = CandidatePreflightEvidence(
            source_identity=f"Dryad:{source['doi']}",
            geometry_source_identity=(
                f"{safe_identity.path}@sha256:{safe_identity.sha256}"
            ),
            response_source_identity=(
                f"{response_identity.path}@sha256:{response_identity.sha256}"
            ),
            geometry_response_separable=True,
            coordinate_geometry_present=True,
            node_count=int(audit["unique_stable_node_count"]),
            outer_unit_count=int(audit["unique_outer_state_count"]),
            repeated_node_count=int(audit["repeated_stable_node_count"]),
            layout_design="natural_irregular",
            analysis_registry_closed=closed_registry,
            response_blind_transport_qualified=transport.ready,
            transport_qualification_fingerprint=transport.fingerprint,
            response_rows_opened=False,
            response_bytes_opened=False,
            note=(
                "source architecture only; current public Dryad deployments route; "
                "sequence payload unopened and no focal taxon selected"
            ),
        )
        preflight = evaluate_candidate_preflight(declaration, evidence)

        arrays_pass = audit["unique_array_count"] >= int(
            minima["minimum_arrays"]
        )
        survey_pass = audit["survey_nights_min"] > 0
        registry_pass = (
            closed_registry
            if bool(minima["require_all_nodes_single_coordinate_pair"])
            else True
        )
        architecture_ready = (
            preflight.ready
            and arrays_pass
            and survey_pass
            and registry_pass
        )

        result = {
            **base,
            "status": (
                "source_ready_for_focal_selection_prelock"
                if architecture_ready
                else "source_architecture_unqualified_prelock"
            ),
            "dataset_identity": {
                "identifier": dataset.get("identifier"),
                "title": dataset.get("title"),
                "version_number": dataset.get("versionNumber"),
                "version_href": version_href,
            },
            "safe_file": {
                **asdict(safe_identity),
                "actual_sha256": safe_sha,
                "payload_bytes_opened": len(safe_bytes),
            },
            "response_file": {
                **asdict(response_identity),
                "payload_requests": 0,
                "payload_bytes_opened": 0,
            },
            "deployment_audit": audit,
            "transport_qualification": asdict(transport),
            "candidate_preflight": asdict(preflight),
            "additional_architecture_checks": {
                "minimum_arrays": int(minima["minimum_arrays"]),
                "arrays_pass": arrays_pass,
                "require_positive_survey_nights": bool(
                    minima["require_positive_survey_nights"]
                ),
                "survey_nights_pass": survey_pass,
                "require_all_nodes_single_coordinate_pair": bool(
                    minima["require_all_nodes_single_coordinate_pair"]
                ),
                "single_coordinate_per_node_pass": registry_pass,
            },
        }
    except (
        PrelockScreenStop,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        result = {
            **base,
            "status": "source_screen_stop_prelock",
            "reason": str(exc),
        }

    result["request_ledger"] = ledger
    result["metadata_and_safe_bytes_opened"] = sum(
        int(item["bytes_opened"]) for item in ledger
    )
    result["fingerprint"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "fingerprint"}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    result = run()
    print(
        json.dumps(
            {
                "status": result["status"],
                "fingerprint": result["fingerprint"],
                "response_file_payload_bytes_opened": (
                    result["response_file_payload_bytes_opened"]
                ),
            },
            sort_keys=True,
        )
    )
