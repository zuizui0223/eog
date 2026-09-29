#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "manuscript/EOG_WF_AUTHOR_ADMIN_CONFIRMATION.json"
DEFAULT_TITLE = ROOT / "manuscript/EOG_WF_TITLE_PAGE.md"
DEFAULT_AI = ROOT / "manuscript/EOG_WF_AI_LLM_DISCLOSURE.md"
DEFAULT_MANUSCRIPT_SOURCE = ROOT / "manuscript/EOG_WF_MANUSCRIPT_V1.md"
DEFAULT_MANUSCRIPT_FINAL = ROOT / "manuscript/EOG_WF_MANUSCRIPT_FINAL.md"
DEFAULT_RECEIPT = ROOT / "manuscript/EOG_WF_AUTHOR_ADMIN_APPROVAL_RECEIPT.json"

EXPECTED_SCHEMA = "eog.eogwf_author_admin_confirmation.v1"
EXPECTED_TITLE = (
    "Environmental Occupancy Geometry: auditable finite-world falsification "
    "with a prospectively stress-tested prediction interface"
)
EXPECTED_JOURNAL = "Methods in Ecology and Evolution"
EXPECTED_ARTICLE_TYPE = "Research Article"
ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-[\dX]{4}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class AuthorAdminError(ValueError):
    pass


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuthorAdminError(f"{label} must be a JSON object")
    return value


def _list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise AuthorAdminError(f"{label} must be a JSON array")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthorAdminError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label)


def _true(value: object, label: str) -> None:
    if value is not True:
        raise AuthorAdminError(f"{label} must be true after author approval")


def _validate_authors(data: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    authors_raw = _list(data.get("authors"), "authors")
    if not authors_raw:
        raise AuthorAdminError("authors must contain at least one confirmed author")

    authors: list[dict[str, Any]] = []
    author_ids: set[str] = set()
    for index, raw in enumerate(authors_raw, start=1):
        row = _mapping(raw, f"authors[{index}]")
        author_id = _text(row.get("id"), f"authors[{index}].id")
        if author_id in author_ids:
            raise AuthorAdminError(f"duplicate author id: {author_id}")
        author_ids.add(author_id)
        full_name = _text(row.get("full_name"), f"authors[{index}].full_name")
        orcid = _text(row.get("orcid"), f"authors[{index}].orcid")
        if orcid.casefold() != "none" and ORCID_RE.fullmatch(orcid) is None:
            raise AuthorAdminError(
                f"authors[{index}].orcid must be 'none' or canonical ORCID"
            )
        affiliation_ids = [
            _text(value, f"authors[{index}].affiliation_ids")
            for value in _list(
                row.get("affiliation_ids"),
                f"authors[{index}].affiliation_ids",
            )
        ]
        if not affiliation_ids:
            raise AuthorAdminError(
                f"authors[{index}].affiliation_ids must be non-empty"
            )
        credit_roles = [
            _text(value, f"authors[{index}].credit_roles")
            for value in _list(
                row.get("credit_roles"),
                f"authors[{index}].credit_roles",
            )
        ]
        if not credit_roles:
            raise AuthorAdminError(
                f"authors[{index}].credit_roles must be non-empty"
            )
        authors.append(
            {
                "id": author_id,
                "full_name": full_name,
                "orcid": orcid,
                "affiliation_ids": affiliation_ids,
                "credit_roles": credit_roles,
            }
        )

    affiliations_raw = _list(data.get("affiliations"), "affiliations")
    if not affiliations_raw:
        raise AuthorAdminError("affiliations must contain at least one entry")
    affiliations: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(affiliations_raw, start=1):
        row = _mapping(raw, f"affiliations[{index}]")
        affiliation_id = _text(row.get("id"), f"affiliations[{index}].id")
        if affiliation_id in affiliations:
            raise AuthorAdminError(f"duplicate affiliation id: {affiliation_id}")
        affiliations[affiliation_id] = {
            "id": affiliation_id,
            "institution": _text(
                row.get("institution"),
                f"affiliations[{index}].institution",
            ),
            "department": _optional_text(
                row.get("department"),
                f"affiliations[{index}].department",
            ),
            "city": _text(row.get("city"), f"affiliations[{index}].city"),
            "country": _text(
                row.get("country"),
                f"affiliations[{index}].country",
            ),
            "postal_address": _text(
                row.get("postal_address"),
                f"affiliations[{index}].postal_address",
            ),
        }

    known_affiliations = set(affiliations)
    for author in authors:
        unknown = set(author["affiliation_ids"]) - known_affiliations
        if unknown:
            raise AuthorAdminError(
                f"author {author['id']!r} references unknown affiliations: "
                f"{sorted(unknown)!r}"
            )
    return authors, affiliations


def validate_confirmation(data: Mapping[str, Any]) -> dict[str, Any]:
    if data.get("schema") != EXPECTED_SCHEMA:
        raise AuthorAdminError(f"schema must be {EXPECTED_SCHEMA!r}")

    manuscript = _mapping(data.get("manuscript"), "manuscript")
    if manuscript.get("title") != EXPECTED_TITLE:
        raise AuthorAdminError("manuscript title differs from frozen EOG-WF title")
    if manuscript.get("journal") != EXPECTED_JOURNAL:
        raise AuthorAdminError("journal differs from frozen EOG-WF route")
    if manuscript.get("article_type") != EXPECTED_ARTICLE_TYPE:
        raise AuthorAdminError("article type differs from frozen EOG-WF route")

    authors, affiliations = _validate_authors(data)
    author_ids = {row["id"] for row in authors}

    corresponding = _mapping(
        data.get("corresponding_author"),
        "corresponding_author",
    )
    corresponding_id = _text(
        corresponding.get("author_id"),
        "corresponding_author.author_id",
    )
    if corresponding_id not in author_ids:
        raise AuthorAdminError(
            "corresponding_author.author_id must match a confirmed author id"
        )
    email = _text(corresponding.get("email"), "corresponding_author.email")
    if EMAIL_RE.fullmatch(email) is None:
        raise AuthorAdminError("corresponding_author.email is not valid")
    postal_address = _text(
        corresponding.get("postal_address"),
        "corresponding_author.postal_address",
    )

    running_headline = _text(data.get("running_headline"), "running_headline")
    if len(running_headline) > 45:
        raise AuthorAdminError("running_headline exceeds 45 characters")
    acknowledgements = _text(data.get("acknowledgements"), "acknowledgements")

    funding = _mapping(data.get("funding"), "funding")
    _true(funding.get("confirmed_by_all_authors"), "funding.confirmed_by_all_authors")
    funding_statement = _text(funding.get("statement"), "funding.statement")

    competing = _mapping(data.get("competing_interests"), "competing_interests")
    _true(
        competing.get("confirmed_by_all_authors"),
        "competing_interests.confirmed_by_all_authors",
    )
    competing_statement = _text(
        competing.get("statement"),
        "competing_interests.statement",
    )

    ethics = _mapping(data.get("ethics_and_permits"), "ethics_and_permits")
    _true(
        ethics.get("reviewed_by_all_authors"),
        "ethics_and_permits.reviewed_by_all_authors",
    )
    ethics_statement = _text(
        ethics.get("statement"),
        "ethics_and_permits.statement",
    )

    originality = _mapping(
        data.get("originality_and_submission"),
        "originality_and_submission",
    )
    for key in (
        "approved_by_all_authors",
        "not_published_previously_confirmed",
        "not_under_consideration_elsewhere_confirmed",
    ):
        _true(originality.get(key), f"originality_and_submission.{key}")

    third_party = _mapping(
        data.get("third_party_data_reuse"),
        "third_party_data_reuse",
    )
    _true(
        third_party.get("confirmed_by_all_authors"),
        "third_party_data_reuse.confirmed_by_all_authors",
    )
    _true(
        third_party.get("publicly_available_or_permission_obtained_confirmed"),
        "third_party_data_reuse.publicly_available_or_permission_obtained_confirmed",
    )
    third_party_data_statement = _text(
        third_party.get("statement"),
        "third_party_data_reuse.statement",
    )

    submission_declarations = _mapping(
        data.get("submission_declarations"),
        "submission_declarations",
    )
    for key in (
        "all_authors_and_relevant_institutions_approve_submission",
        "all_entitled_authors_included",
        "all_necessary_acknowledgements_made",
        "legal_and_ethics_requirements_confirmed",
    ):
        _true(
            submission_declarations.get(key),
            f"submission_declarations.{key}",
        )

    inclusion = _mapping(data.get("inclusion_statement"), "inclusion_statement")
    _true(
        inclusion.get("approved_by_all_authors"),
        "inclusion_statement.approved_by_all_authors",
    )
    inclusion_statement = _text(
        inclusion.get("statement"),
        "inclusion_statement.statement",
    )

    ai = _mapping(data.get("ai_llm"), "ai_llm")
    application = _text(ai.get("application"), "ai_llm.application")
    provider = _text(ai.get("provider"), "ai_llm.provider")
    model_or_version = _text(
        ai.get("model_or_version"),
        "ai_llm.model_or_version",
    )
    approximate_period = _text(
        ai.get("approximate_period"),
        "ai_llm.approximate_period",
    )
    categories = [
        _text(value, "ai_llm.assistance_categories")
        for value in _list(
            ai.get("assistance_categories"),
            "ai_llm.assistance_categories",
        )
    ]
    if not categories:
        raise AuthorAdminError("ai_llm.assistance_categories must be non-empty")
    responsible_author_id = _text(
        ai.get("responsible_author_id"),
        "ai_llm.responsible_author_id",
    )
    if responsible_author_id not in author_ids:
        raise AuthorAdminError(
            "ai_llm.responsible_author_id must match a confirmed author id"
        )
    final_methods_disclosure = _text(
        ai.get("final_methods_disclosure"),
        "ai_llm.final_methods_disclosure",
    )
    contribution_statement = _text(
        ai.get("contribution_statement"),
        "ai_llm.contribution_statement",
    )
    for key in (
        "reviewed_by_all_authors",
        "author_accountability_confirmed",
        "live_journal_policy_checked",
    ):
        _true(ai.get(key), f"ai_llm.{key}")

    confirmations = _mapping(data.get("confirmations"), "confirmations")
    for key in (
        "author_order_approved",
        "affiliations_approved",
        "corresponding_author_approved",
        "credit_roles_approved",
        "acknowledgements_approved",
        "running_headline_approved",
        "final_title_page_approved",
        "final_ai_llm_disclosure_approved",
        "third_party_data_reuse_approved",
    ):
        _true(confirmations.get(key), f"confirmations.{key}")

    author_by_id = {row["id"]: row for row in authors}
    return {
        "authors": authors,
        "affiliations": affiliations,
        "author_by_id": author_by_id,
        "corresponding_author_id": corresponding_id,
        "corresponding_email": email,
        "corresponding_postal_address": postal_address,
        "running_headline": running_headline,
        "acknowledgements": acknowledgements,
        "funding_statement": funding_statement,
        "competing_statement": competing_statement,
        "ethics_statement": ethics_statement,
        "inclusion_statement": inclusion_statement,
        "third_party_data_statement": third_party_data_statement,
        "submission_declarations": {
            key: True
            for key in (
                "all_authors_and_relevant_institutions_approve_submission",
                "all_entitled_authors_included",
                "all_necessary_acknowledgements_made",
                "legal_and_ethics_requirements_confirmed",
            )
        },
        "ai": {
            "application": application,
            "provider": provider,
            "model_or_version": model_or_version,
            "approximate_period": approximate_period,
            "assistance_categories": categories,
            "other_assistance": _optional_text(
                ai.get("other_assistance"),
                "ai_llm.other_assistance",
            ),
            "specific_code_or_text_annotations": _optional_text(
                ai.get("specific_code_or_text_annotations"),
                "ai_llm.specific_code_or_text_annotations",
            ),
            "responsible_author_id": responsible_author_id,
            "final_methods_disclosure": final_methods_disclosure,
            "contribution_statement": contribution_statement,
        },
        "manuscript": dict(manuscript),
    }


def render_title_page(validated: Mapping[str, Any]) -> str:
    affiliations: Mapping[str, Mapping[str, Any]] = validated["affiliations"]
    authors: list[Mapping[str, Any]] = validated["authors"]

    lines = [
        "# EOG-WF title page",
        "",
        "## Title",
        "",
        EXPECTED_TITLE,
        "",
        "## Authors and affiliations",
        "",
    ]
    for author in authors:
        affiliation_labels = ", ".join(author["affiliation_ids"])
        orcid_text = "" if author["orcid"].casefold() == "none" else f"; ORCID {author['orcid']}"
        lines.append(
            f"- {author['full_name']} — {affiliation_labels}{orcid_text}"
        )

    lines += ["", "### Affiliations", ""]
    for affiliation_id in sorted(affiliations):
        row = affiliations[affiliation_id]
        parts = [row["institution"]]
        if row["department"]:
            parts.append(row["department"])
        parts.extend([row["city"], row["country"], row["postal_address"]])
        lines.append(f"- {affiliation_id}: " + ", ".join(parts))

    corresponding = validated["author_by_id"][validated["corresponding_author_id"]]
    lines += [
        "",
        "## Corresponding author",
        "",
        f"- Name: {corresponding['full_name']}",
        f"- Email: {validated['corresponding_email']}",
        f"- Postal address: {validated['corresponding_postal_address']}",
        "",
        "## Running headline",
        "",
        validated["running_headline"],
        "",
        "## Acknowledgements",
        "",
        validated["acknowledgements"],
        "",
        "## Author contributions",
        "",
    ]
    for author in authors:
        lines.append(
            f"- {author['full_name']}: " + ", ".join(author["credit_roles"])
        )

    lines += [
        "",
        "## Data availability",
        "",
        (
            "Peer-review code and data snapshot: "
            "https://github.com/zuizui0223/eog/tree/"
            "91125ae68004f298fcd45027566506772a3688d5"
        ),
        "",
        "## Data sources and reuse",
        "",
        validated["third_party_data_statement"],
        "",
        "## Conflict of interest",
        "",
        validated["competing_statement"],
        "",
        "## Funding",
        "",
        validated["funding_statement"],
        "",
        "## Ethics and permits",
        "",
        validated["ethics_statement"],
        "",
        "## Inclusion statement",
        "",
        validated["inclusion_statement"],
        "",
    ]
    return "\n".join(lines)


def render_ai_disclosure(validated: Mapping[str, Any]) -> str:
    ai = validated["ai"]
    responsible = validated["author_by_id"][ai["responsible_author_id"]]
    lines = [
        "# EOG-WF AI / LLM disclosure — author approved",
        "",
        "## Confirmed tool context",
        "",
        f"- Application: {ai['application']}",
        f"- Provider: {ai['provider']}",
        f"- Model/version: {ai['model_or_version']}",
        f"- Approximate period: {ai['approximate_period']}",
        "- Assistance categories: " + "; ".join(ai["assistance_categories"]),
    ]
    if ai["other_assistance"]:
        lines.append(f"- Other assistance: {ai['other_assistance']}")
    if ai["specific_code_or_text_annotations"]:
        lines.append(
            "- Specific annotations required: "
            + ai["specific_code_or_text_annotations"]
        )
    lines += [
        "",
        "## Methods disclosure text",
        "",
        ai["final_methods_disclosure"],
        "",
        "## Author contribution / accountability text",
        "",
        ai["contribution_statement"],
        "",
        "## Responsible author",
        "",
        responsible["full_name"],
        "",
    ]
    return "\n".join(lines)


def render_final_manuscript(
    validated: Mapping[str, Any],
    source_text: str,
) -> str:
    marker = "## Results"
    if marker not in source_text:
        raise AuthorAdminError("source manuscript lacks Results heading")
    if "### AI / LLM use in manuscript preparation" in source_text:
        raise AuthorAdminError("source manuscript already contains the admin AI disclosure section")

    disclosure = validated["ai"]["final_methods_disclosure"]
    block = (
        "### AI / LLM use in manuscript preparation\n\n"
        + disclosure
        + "\n\n"
    )
    return source_text.replace(marker, block + marker, 1)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def validate_admin_receipt(
    receipt_path: Path = DEFAULT_RECEIPT,
    *,
    title_path: Path = DEFAULT_TITLE,
    ai_path: Path = DEFAULT_AI,
    manuscript_path: Path = DEFAULT_MANUSCRIPT_FINAL,
) -> bool:
    if not receipt_path.is_file():
        return False
    if not title_path.is_file() or not ai_path.is_file() or not manuscript_path.is_file():
        return False
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if receipt.get("schema") != "eog.eogwf_author_admin_approval_receipt.v1":
        return False
    if receipt.get("all_author_admin_confirmations_complete") is not True:
        return False
    expected = receipt.get("outputs")
    if not isinstance(expected, Mapping):
        return False
    observed = {
        "title_page_sha256": _sha256_file(title_path),
        "ai_llm_disclosure_sha256": _sha256_file(ai_path),
        "final_manuscript_sha256": _sha256_file(manuscript_path),
    }
    return all(expected.get(key) == value for key, value in observed.items())


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def build(
    input_path: Path = DEFAULT_INPUT,
    title_output: Path = DEFAULT_TITLE,
    ai_output: Path = DEFAULT_AI,
    manuscript_source: Path = DEFAULT_MANUSCRIPT_SOURCE,
    manuscript_output: Path = DEFAULT_MANUSCRIPT_FINAL,
    receipt_output: Path = DEFAULT_RECEIPT,
) -> dict[str, object]:
    raw_confirmation = input_path.read_bytes()
    data = json.loads(raw_confirmation.decode("utf-8"))
    validated = validate_confirmation(_mapping(data, "confirmation"))
    title_text = render_title_page(validated) + "\n"
    ai_text = render_ai_disclosure(validated) + "\n"
    source_text = manuscript_source.read_text(encoding="utf-8")
    final_manuscript = render_final_manuscript(validated, source_text)
    if not final_manuscript.endswith("\n"):
        final_manuscript += "\n"

    title_output.write_text(title_text, encoding="utf-8")
    ai_output.write_text(ai_text, encoding="utf-8")
    manuscript_output.write_text(final_manuscript, encoding="utf-8")

    receipt = {
        "schema": "eog.eogwf_author_admin_approval_receipt.v1",
        "status": "author_admin_confirmed",
        "journal": EXPECTED_JOURNAL,
        "article_type": EXPECTED_ARTICLE_TYPE,
        "manuscript_title": EXPECTED_TITLE,
        "confirmation_sha256": _sha256_bytes(raw_confirmation),
        "author_count": len(validated["authors"]),
        "corresponding_author_id": validated["corresponding_author_id"],
        "all_author_admin_confirmations_complete": True,
        "outputs": {
            "title_page_sha256": _sha256_bytes(title_text.encode("utf-8")),
            "ai_llm_disclosure_sha256": _sha256_bytes(ai_text.encode("utf-8")),
            "final_manuscript_sha256": _sha256_bytes(final_manuscript.encode("utf-8")),
        },
    }
    receipt_output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not validate_admin_receipt(
        receipt_output,
        title_path=title_output,
        ai_path=ai_output,
        manuscript_path=manuscript_output,
    ):
        raise AuthorAdminError("generated author-admin approval receipt failed verification")

    return {
        "status": "author_admin_outputs_generated",
        "title_page": _display_path(title_output),
        "ai_llm_disclosure": _display_path(ai_output),
        "final_manuscript": _display_path(manuscript_output),
        "approval_receipt": _display_path(receipt_output),
        "author_count": len(validated["authors"]),
        "corresponding_author_id": validated["corresponding_author_id"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--title-output", type=Path, default=DEFAULT_TITLE)
    parser.add_argument("--ai-output", type=Path, default=DEFAULT_AI)
    parser.add_argument(
        "--manuscript-source",
        type=Path,
        default=DEFAULT_MANUSCRIPT_SOURCE,
    )
    parser.add_argument(
        "--manuscript-output",
        type=Path,
        default=DEFAULT_MANUSCRIPT_FINAL,
    )
    parser.add_argument(
        "--receipt-output",
        type=Path,
        default=DEFAULT_RECEIPT,
    )
    args = parser.parse_args()
    result = build(
        args.input,
        args.title_output,
        args.ai_output,
        args.manuscript_source,
        args.manuscript_output,
        args.receipt_output,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
