from eog.v2.source_discovery_firewall import SourceDescriptor
from eog.v2.source_discovery_gate import (
    DiscoveryRoleRequirement,
    DiscoverySource,
    evaluate_discovery_gate,
)


def test_safe_registry_and_effort_roles_allow_content_open():
    result = evaluate_discovery_gate(
        (
            DiscoverySource(
                SourceDescriptor(
                    "registry",
                    "deployments.csv",
                    (
                        "deploymentID",
                        "locationID",
                        "latitude",
                        "longitude",
                        "deploymentStart",
                        "deploymentEnd",
                    ),
                ),
                "registry_effort",
            ),
        ),
        (DiscoveryRoleRequirement("registry_effort"),),
    )
    assert result.status == "ready_for_declared_safe_content_open"
    assert result.ready_for_safe_content_open is True
    assert result.safe_source_ids == ("registry",)


def test_response_bearing_file_cannot_satisfy_safe_role():
    result = evaluate_discovery_gate(
        (
            DiscoverySource(
                SourceDescriptor(
                    "captures",
                    "captures.csv",
                ),
                "registry_effort",
            ),
        ),
        (DiscoveryRoleRequirement("registry_effort"),),
    )
    assert result.status == "stop_required_safe_source_roles_unresolved"
    assert result.ready_for_safe_content_open is False
    assert result.missing_roles == ("registry_effort",)
    assert result.blocked_source_ids == ("captures",)


def test_ambiguous_file_does_not_satisfy_required_role():
    result = evaluate_discovery_gate(
        (DiscoverySource(SourceDescriptor("mystery", "data.csv"), "registry"),),
        (DiscoveryRoleRequirement("registry"),),
    )
    assert result.ready_for_safe_content_open is False
    assert result.missing_roles == ("registry",)


def test_safe_covariates_do_not_substitute_for_missing_coordinate_registry():
    result = evaluate_discovery_gate(
        (
            DiscoverySource(
                SourceDescriptor(
                    "landcover",
                    "site_covariates.csv",
                    ("siteID", "forest", "urban"),
                ),
                "covariates",
            ),
        ),
        (
            DiscoveryRoleRequirement("registry"),
            DiscoveryRoleRequirement("covariates"),
        ),
    )
    assert result.ready_for_safe_content_open is False
    assert result.missing_roles == ("registry",)


def test_response_source_can_be_listed_but_remains_blocked_while_safe_roles_pass():
    result = evaluate_discovery_gate(
        (
            DiscoverySource(
                SourceDescriptor(
                    "deployments",
                    "deployments.csv",
                    ("deploymentID", "latitude", "longitude"),
                ),
                "registry",
            ),
            DiscoverySource(
                SourceDescriptor(
                    "observations",
                    "observations.csv",
                    ("deploymentID", "scientificName"),
                ),
                "future_response",
            ),
        ),
        (DiscoveryRoleRequirement("registry"),),
    )
    assert result.ready_for_safe_content_open is True
    assert result.safe_source_ids == ("deployments",)
    assert result.blocked_source_ids == ("observations",)


def test_gate_result_is_order_invariant():
    sources = (
        DiscoverySource(SourceDescriptor("b", "deployments.csv"), "registry"),
        DiscoverySource(SourceDescriptor("a", "observations.csv"), "future_response"),
    )
    requirements = (DiscoveryRoleRequirement("registry"),)
    left = evaluate_discovery_gate(sources, requirements)
    right = evaluate_discovery_gate(sources[::-1], requirements)
    assert left.fingerprint == right.fingerprint
