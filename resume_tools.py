from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pypdf.errors import PdfReadError
from weasyprint import HTML

from ResumeBuilder import build_html, load_resume_data, validate_pdf_output

RECORD_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EVIDENCE_LINE = re.compile(
    r"^\s*-\s+\[([a-z0-9]+(?:-[a-z0-9]+)*)\]\s+(.+?)\s*$",
    re.MULTILINE,
)
MARKDOWN_BULLET = re.compile(r"^\s*-\s+")
FIT_REPORT_HEADINGS = (
    "## Evidence-backed matches",
    "## Unsupported or weakly supported requirements",
)
FIT_EVIDENCE = re.compile(
    r"^\s*-\s+.+?\s+—\s+evidence:\s+((?:`[a-z0-9]+(?:-[a-z0-9]+)*`(?:,\s*)?)+)\s*$"
)
FIT_GAP = re.compile(
    r"^\s*-\s+.+?\s+—\s+(?:unsupported|weakly supported)"
    r"(?:;\s+evidence:\s+(?:`[a-z0-9]+(?:-[a-z0-9]+)*`(?:,\s*)?)+)?\s*$",
    re.IGNORECASE,
)
FIT_EVIDENCE_ID = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)*)`")
REQUIRED_METADATA = ("id", "type", "title", "summary")
OPTIONAL_METADATA = (
    "employer",
    "role",
    "location",
    "dates",
    "skills",
    "domains",
    "tags",
    "aliases",
)
ROOT_FIELDS = {
    "profile",
    "experience_years",
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications_and_achievements",
}
PROFILE_FIELDS = {"name", "title", "phone", "email", "location", "links"}
ITEM_FIELDS = {
    "skills": {"category", "items"},
    "experience": {"role", "company", "location", "duration", "highlights"},
    "projects": {"name", "description", "highlights"},
    "education": {"degree", "institution", "score", "date"},
}
class WorkflowError(ValueError):
    pass


class PageFitError(WorkflowError):
    def __init__(self, page_count: int):
        self.page_count = page_count
        super().__init__(
            f"Strict one-page validation failed: generated PDF has {page_count} pages."
        )


def parse_profile_record(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise WorkflowError(f"{path}: missing YAML frontmatter opening delimiter.")
    try:
        closing_index = lines.index("---", 1)
    except ValueError as exc:
        raise WorkflowError(f"{path}: missing YAML frontmatter closing delimiter.") from exc
    try:
        metadata = yaml.safe_load("\n".join(lines[1:closing_index]))
    except yaml.YAMLError as exc:
        raise WorkflowError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise WorkflowError(f"{path}: YAML frontmatter must be a mapping.")
    return metadata, "\n".join(lines[closing_index + 1 :])


def profile_records(profile_dir: Path) -> list[tuple[Path, dict[str, Any], str]]:
    root = profile_dir.resolve()
    if not profile_dir.is_dir():
        raise WorkflowError(f"Profile directory not found: {profile_dir}")

    records: list[tuple[Path, dict[str, Any], str]] = []
    for path in sorted(profile_dir.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        if not path.resolve().is_relative_to(root):
            raise WorkflowError(f"Profile record resolves outside profile directory: {path}")
        metadata, body = parse_profile_record(path)
        records.append((path, metadata, body))
    if not records:
        raise WorkflowError(f"No Markdown profile records found in {profile_dir}")
    return records


def validate_profile(profile_dir: Path) -> tuple[list[dict[str, Any]], set[str]]:
    records = profile_records(profile_dir)
    seen_record_ids: dict[str, Path] = {}
    seen_evidence_ids: dict[str, Path] = {}
    index_records: list[dict[str, Any]] = []

    for path, metadata, body in records:
        for field in REQUIRED_METADATA:
            if not isinstance(metadata.get(field), str) or not metadata[field].strip():
                raise WorkflowError(f"{path}: frontmatter field '{field}' must be a non-empty string.")

        unknown_fields = set(metadata) - set(REQUIRED_METADATA) - set(OPTIONAL_METADATA)
        if unknown_fields:
            names = ", ".join(sorted(unknown_fields))
            raise WorkflowError(f"{path}: unsupported frontmatter field(s): {names}")

        record_id = metadata["id"]
        if not RECORD_ID.fullmatch(record_id):
            raise WorkflowError(f"{path}: record id '{record_id}' must be lowercase kebab-case.")
        if record_id in seen_record_ids:
            raise WorkflowError(
                f"{path}: duplicate record id '{record_id}' also found in {seen_record_ids[record_id]}."
            )
        seen_record_ids[record_id] = path

        for field in ("employer", "role", "location", "dates"):
            if field in metadata and not isinstance(metadata[field], str):
                raise WorkflowError(f"{path}: frontmatter field '{field}' must be a string.")
        for field in ("skills", "domains", "tags", "aliases"):
            values = metadata.get(field, [])
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise WorkflowError(f"{path}: frontmatter field '{field}' must be a list of strings.")

        for line_number, line in enumerate(body.splitlines(), start=1):
            if MARKDOWN_BULLET.match(line) and not EVIDENCE_LINE.match(line):
                raise WorkflowError(
                    f"{path}: body line {line_number}: profile bullets must start with a stable [evidence-id]."
                )
        for evidence_match in EVIDENCE_LINE.finditer(body):
            evidence_id = evidence_match.group(1)
            if evidence_id in seen_evidence_ids:
                raise WorkflowError(
                    f"{path}: duplicate evidence id '{evidence_id}' also found in "
                    f"{seen_evidence_ids[evidence_id]}."
                )
            seen_evidence_ids[evidence_id] = path

        index_record: dict[str, Any] = {
            field: metadata[field] for field in REQUIRED_METADATA
        }
        for field in OPTIONAL_METADATA:
            if field in metadata:
                index_record[field] = metadata[field]
        index_records.append(index_record)

    shared_ids = set(seen_record_ids) & set(seen_evidence_ids)
    if shared_ids:
        shared_id = sorted(shared_ids)[0]
        raise WorkflowError(
            f"ID '{shared_id}' is used as both a record id and evidence id."
        )
    all_ids = set(seen_record_ids) | set(seen_evidence_ids)
    return index_records, all_ids


def write_index(profile_dir: Path, output_path: Path | None) -> Path:
    records, _ = validate_profile(profile_dir)
    destination = output_path or profile_dir / "index.yaml"
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.safe_dump(
        {"version": 1, "records": records},
        sort_keys=False,
        allow_unicode=True,
    )
    destination.write_text(content, encoding="utf-8")
    return destination


def collect_string_paths(value: Any, prefix: str = "") -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            paths.update(collect_string_paths(child, child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_prefix = f"{prefix}.{index}" if prefix else str(index)
            paths.update(collect_string_paths(child, child_prefix))
    elif isinstance(value, str) and value.strip():
        paths.add(prefix)
    return paths


def validate_resume_data(resume: Any) -> dict[str, Any]:
    if not isinstance(resume, dict):
        raise WorkflowError("Resume YAML root must be a mapping.")
    extra_root = set(resume) - ROOT_FIELDS
    if extra_root:
        raise WorkflowError(f"Unsupported resume field(s): {', '.join(sorted(extra_root))}.")

    profile = resume.get("profile")
    if not isinstance(profile, dict):
        raise WorkflowError("Resume field 'profile' must be a mapping.")
    if set(profile) - PROFILE_FIELDS:
        raise WorkflowError(
            f"Unsupported profile field(s): {', '.join(sorted(set(profile) - PROFILE_FIELDS))}."
        )
    if not isinstance(profile.get("name"), str) or not profile["name"].strip():
        raise WorkflowError("Resume field 'profile.name' must be a non-empty string.")
    for key, value in profile.items():
        if key == "links":
            if not isinstance(value, list):
                raise WorkflowError("Resume field 'profile.links' must be a list.")
            for index, link in enumerate(value):
                if not isinstance(link, dict) or set(link) - {"label", "url"}:
                    raise WorkflowError(f"profile.links.{index} must contain only label and url.")
                if not all(isinstance(link.get(field), str) for field in ("label", "url")):
                    raise WorkflowError(f"profile.links.{index} label and url must be strings.")
        elif not isinstance(value, str):
            raise WorkflowError(f"Resume field 'profile.{key}' must be a string.")

    for key in ("experience_years", "summary"):
        if key in resume and not isinstance(resume[key], str):
            raise WorkflowError(f"Resume field '{key}' must be a string.")

    list_fields = ("skills", "experience", "projects", "education", "certifications_and_achievements")
    for section in list_fields:
        if section not in resume:
            continue
        value = resume[section]
        if not isinstance(value, list):
            raise WorkflowError(f"Resume field '{section}' must be a list.")
        if section == "certifications_and_achievements":
            if not all(isinstance(item, str) for item in value):
                raise WorkflowError(f"Resume field '{section}' must contain strings.")
            if any(
                not item.startswith(("Achievements:", "Certifications:"))
                for item in value
            ):
                raise WorkflowError(
                    "certifications_and_achievements entries must start with "
                    "'Achievements:' or 'Certifications:'."
                )
            if any(not item.partition(":")[2].strip() for item in value):
                raise WorkflowError(
                    "certifications_and_achievements entries must include content after the prefix."
                )
            continue
        for index, item in enumerate(value):
            location = f"{section}.{index}"
            if not isinstance(item, dict):
                raise WorkflowError(f"{location} must be a mapping.")
            allowed = ITEM_FIELDS[section]
            if set(item) - allowed:
                extra = ", ".join(sorted(set(item) - allowed))
                raise WorkflowError(f"{location} has unsupported field(s): {extra}.")
            required_fields = {
                "skills": ("category", "items"),
                "experience": ("role", "company", "duration", "highlights"),
                "projects": ("name", "highlights"),
                "education": ("degree", "institution"),
            }[section]
            for field in required_fields:
                if field not in item:
                    raise WorkflowError(f"{location}.{field} is required.")
            nonempty_fields = {
                "skills": ("category",),
                "experience": ("role", "company", "duration"),
                "projects": ("name",),
                "education": ("degree", "institution"),
            }[section]
            for field, field_value in item.items():
                if field == "highlights" or field == "items":
                    if not isinstance(field_value, list) or not all(
                        isinstance(entry, str) for entry in field_value
                    ):
                        raise WorkflowError(f"{location}.{field} must be a list of strings.")
                    if field == "items" and not field_value:
                        raise WorkflowError(f"{location}.{field} must not be empty.")
                elif not isinstance(field_value, str):
                    raise WorkflowError(f"{location}.{field} must be a string.")
                elif field in nonempty_fields and not field_value.strip():
                    raise WorkflowError(f"{location}.{field} must not be empty.")

    return resume


def validate_source_map(resume: dict[str, Any], source_map_path: Path, profile_dir: Path) -> None:
    try:
        source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"{source_map_path}: invalid JSON: {exc}") from exc
    if not isinstance(source_map, dict) or not isinstance(source_map.get("items"), list):
        raise WorkflowError(f"{source_map_path}: expected an object with an 'items' list.")

    _, known_ids = validate_profile(profile_dir)
    mapped_paths: set[str] = set()
    for index, item in enumerate(source_map["items"]):
        if not isinstance(item, dict) or set(item) != {"path", "source_evidence_ids"}:
            raise WorkflowError(
                f"{source_map_path}: items.{index} must contain path and source_evidence_ids."
            )
        path = item["path"]
        evidence_ids = item["source_evidence_ids"]
        if not isinstance(path, str) or not path:
            raise WorkflowError(f"{source_map_path}: items.{index}.path must be a non-empty string.")
        if path in mapped_paths:
            raise WorkflowError(f"{source_map_path}: duplicate mapped path '{path}'.")
        mapped_paths.add(path)
        if not isinstance(evidence_ids, list) or not evidence_ids or not all(
            isinstance(evidence_id, str) for evidence_id in evidence_ids
        ):
            raise WorkflowError(
                f"{source_map_path}: items.{index}.source_evidence_ids must be a non-empty string list."
            )
        unknown = set(evidence_ids) - known_ids
        if unknown:
            raise WorkflowError(
                f"{source_map_path}: path '{path}' references unknown evidence id(s): "
                f"{', '.join(sorted(unknown))}."
            )

    content_paths = collect_string_paths(resume)
    if content_paths != mapped_paths:
        missing = sorted(content_paths - mapped_paths)
        stale = sorted(mapped_paths - content_paths)
        details = []
        if missing:
            details.append(f"unmapped content: {', '.join(missing)}")
        if stale:
            details.append(f"paths not present in resume: {', '.join(stale)}")
        raise WorkflowError(f"{source_map_path}: " + "; ".join(details) + ".")


def validate_fit_report(fit_report_path: Path, profile_dir: Path) -> None:
    try:
        report = fit_report_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkflowError(f"Cannot read fit report {fit_report_path}: {exc}") from exc

    heading_positions = [report.find(heading) for heading in FIT_REPORT_HEADINGS]
    if any(position < 0 for position in heading_positions):
        raise WorkflowError(
            f"{fit_report_path}: expected headings 'Evidence-backed matches' and "
            "'Unsupported or weakly supported requirements'."
        )
    if heading_positions != sorted(heading_positions):
        raise WorkflowError(f"{fit_report_path}: fit report sections are out of order.")

    matched_section = report[
        heading_positions[0] + len(FIT_REPORT_HEADINGS[0]) : heading_positions[1]
    ]
    gaps_section = report[heading_positions[1] + len(FIT_REPORT_HEADINGS[1]) :]
    matched_entries = [
        line for line in matched_section.splitlines() if line.lstrip().startswith("- ")
    ]
    gap_entries = [line for line in gaps_section.splitlines() if line.lstrip().startswith("- ")]
    if not matched_entries:
        raise WorkflowError(f"{fit_report_path}: list matched requirements or 'None identified'.")
    if not gap_entries:
        raise WorkflowError(f"{fit_report_path}: list unsupported requirements or 'None identified'.")

    _, known_ids = validate_profile(profile_dir)
    for line in matched_entries:
        if line.strip().casefold() == "- none identified":
            continue
        match = FIT_EVIDENCE.fullmatch(line)
        if not match:
            raise WorkflowError(
                f"{fit_report_path}: matched requirement must include evidence IDs, "
                "for example '- Backend APIs — evidence: `project-api`'."
            )
        unknown_ids = set(FIT_EVIDENCE_ID.findall(match.group(1))) - known_ids
        if unknown_ids:
            raise WorkflowError(
                f"{fit_report_path}: unknown evidence ID(s): {', '.join(sorted(unknown_ids))}."
            )

    for line in gap_entries:
        if line.strip().casefold() == "- none identified":
            continue
        if not FIT_GAP.fullmatch(line):
            raise WorkflowError(
                f"{fit_report_path}: gap entry must end in '— unsupported' or "
                "'— weakly supported' with evidence IDs when applicable."
            )
        unknown_ids = set(FIT_EVIDENCE_ID.findall(line)) - known_ids
        if unknown_ids:
            raise WorkflowError(
                f"{fit_report_path}: unknown evidence ID(s): {', '.join(sorted(unknown_ids))}."
            )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not slug or not RECORD_ID.fullmatch(slug):
        raise WorkflowError("Application name must produce a lowercase alphanumeric slug.")
    return slug


def prompt_collision() -> str:
    if not sys.stdin.isatty():
        return "cancel"
    print("Application draft already exists. Choose: [n]ew numbered draft, [r]eplace, [c]ancel")
    choice = input("Choice [c]: ").strip().casefold()
    return {"n": "new", "r": "replace", "c": "cancel", "": "cancel"}.get(choice, "cancel")


def create_draft(application: str, output_root: Path, collision: str) -> Path:
    root = output_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    slug = slugify(application)
    candidate = root / slug

    if candidate.exists() or candidate.is_symlink():
        choice = prompt_collision() if collision == "ask" else collision
        if choice == "cancel":
            raise WorkflowError(f"Cancelled: output already exists at {candidate}.")
        if choice == "new":
            draft_number = 2
            while True:
                numbered = root / f"{slug}-draft-{draft_number}"
                if not numbered.exists() and not numbered.is_symlink():
                    candidate = numbered
                    break
                draft_number += 1
        elif choice == "replace":
            if candidate.is_symlink() or not candidate.resolve().is_relative_to(root):
                raise WorkflowError(f"Refusing to replace unsafe output path: {candidate}")
            if candidate.is_dir():
                shutil.rmtree(candidate)
            else:
                candidate.unlink()
        else:
            raise WorkflowError(f"Unsupported collision choice: {choice}")

    if not candidate.parent.resolve().is_relative_to(root):
        raise WorkflowError(f"Refusing to create output outside generated directory: {candidate}")
    candidate.mkdir(parents=False, exist_ok=False)
    write_status(
        candidate,
        {
            "state": "draft",
            "application": application,
            "render_attempts": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return candidate


def read_status(draft_dir: Path) -> dict[str, Any]:
    path = draft_dir / "status.json"
    if not path.exists():
        return {"state": "draft", "render_attempts": 0}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowError(f"{path}: expected a JSON object.")
    return value


def write_status(draft_dir: Path, status: dict[str, Any]) -> None:
    status_path = draft_dir / "status.json"
    temporary_path = status_path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(status_path)


def render_draft(
    draft_dir: Path,
    profile_dir: Path,
    attempt: int,
    generated_root: Path = Path("generated"),
) -> int:
    root = generated_root.resolve()
    if not draft_dir.is_dir() or draft_dir.is_symlink():
        raise WorkflowError(f"Draft directory not found or is unsafe: {draft_dir}")
    resolved_draft = draft_dir.resolve()
    if resolved_draft.parent != root:
        raise WorkflowError(
            f"Draft directory must be a direct child of generated root '{root}': {draft_dir}"
        )
    status = read_status(draft_dir)
    previous_attempt = status.get("render_attempts", 0)
    if not isinstance(previous_attempt, int) or attempt != previous_attempt + 1 or attempt > 4:
        raise WorkflowError(
            f"Render attempt must be sequential and between 1 and 4; previous attempt was {previous_attempt}."
        )

    status.update({"state": "failed", "render_attempts": attempt})
    status.pop("error", None)
    status.pop("page_count", None)
    write_status(draft_dir, status)

    try:
        resume_path = draft_dir / "resume.yaml"
        source_map_path = draft_dir / "source-map.json"
        fit_report_path = draft_dir / "fit-report.md"
        for required_file in (resume_path, source_map_path, fit_report_path):
            if not required_file.is_file() or required_file.is_symlink():
                raise WorkflowError(f"Required application artifact not found or unsafe: {required_file}")
        resume = validate_resume_data(load_resume_data(resume_path))
        validate_source_map(resume, source_map_path, profile_dir)
        validate_fit_report(fit_report_path, profile_dir)

        html_content = build_html(resume)
        html_path = draft_dir / "resume.html"
        pdf_path = draft_dir / "resume.pdf"
        html_path.write_text(html_content, encoding="utf-8")
        HTML(str(html_path)).write_pdf(str(pdf_path))

        page_count = validate_pdf_output(pdf_path, resume, html_content)
        if page_count != 1:
            raise PageFitError(page_count)
        status.update({"state": "validated", "page_count": page_count})
        write_status(draft_dir, status)
        return page_count
    except (WorkflowError, OSError, yaml.YAMLError, PdfReadError) as exc:
        status.update({"state": "failed", "error": str(exc)})
        if isinstance(exc, PageFitError):
            status["page_count"] = exc.page_count
        write_status(draft_dir, status)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Profile indexing and safe resume draft tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("profile-index", help="Rebuild the profile metadata index.")
    index_parser.add_argument("--profile-dir", type=Path, default=Path("profile"))
    index_parser.add_argument("--output", type=Path, default=None)

    validate_parser = subparsers.add_parser("validate-profile", help="Validate profile records and IDs.")
    validate_parser.add_argument("--profile-dir", type=Path, default=Path("profile"))

    draft_parser = subparsers.add_parser("create-draft", help="Create an isolated application draft directory.")
    draft_parser.add_argument("--application", required=True, help="Application slug or descriptive label.")
    draft_parser.add_argument("--output-root", type=Path, default=Path("generated"))
    draft_parser.add_argument(
        "--collision",
        choices=("ask", "new", "replace", "cancel"),
        default="ask",
    )

    render_parser = subparsers.add_parser("render", help="Validate and render an application draft.")
    render_parser.add_argument("--draft-dir", required=True, type=Path)
    render_parser.add_argument("--profile-dir", type=Path, default=Path("profile"))
    render_parser.add_argument("--generated-root", type=Path, default=Path("generated"))
    render_parser.add_argument("--attempt", required=True, type=int)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.command == "profile-index":
            destination = write_index(args.profile_dir, args.output)
            print(destination)
        elif args.command == "validate-profile":
            records, evidence_ids = validate_profile(args.profile_dir)
            print(f"Validated {len(records)} records and {len(evidence_ids)} record/evidence IDs.")
        elif args.command == "create-draft":
            destination = create_draft(args.application, args.output_root, args.collision)
            print(destination)
        elif args.command == "render":
            page_count = render_draft(
                args.draft_dir,
                args.profile_dir,
                args.attempt,
                args.generated_root,
            )
            print(f"Validated one-page draft: {args.draft_dir} ({page_count} page)")
    except (WorkflowError, OSError, yaml.YAMLError, PdfReadError) as exc:
        print(f"resume-tools: error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
