from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath
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
SOURCE_NOTE_LINE = re.compile(
    r"^\s*`([a-z0-9]+(?:-[a-z0-9]+)*)`:\s+([^;\r\n]+);"
    r"\s+imported (\d{4}-\d{2}-\d{2})"
    r"(?:;\s+locator:\s+(.+))?\s*$"
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


def source_note_ids(path: Path, body: str, evidence_ids: set[str]) -> None:
    lines = body.splitlines()
    headings = [
        index
        for index, line in enumerate(lines)
        if line.strip() == "## Source notes"
    ]
    if len(headings) > 1:
        raise WorkflowError(f"{path}: duplicate '## Source notes' sections.")
    if not headings:
        return

    start = headings[0] + 1
    end = next(
        (
            index
            for index in range(start, len(lines))
            if re.match(r"^##\s+", lines[index])
        ),
        len(lines),
    )
    notes = [line for line in lines[start:end] if line.strip()]
    if not notes:
        raise WorkflowError(f"{path}: '## Source notes' section must contain at least one source note.")

    seen: set[str] = set()
    for line_index in range(start, end):
        line = lines[line_index]
        if not line.strip():
            continue
        match = SOURCE_NOTE_LINE.fullmatch(line)
        if not match:
            raise WorkflowError(
                f"{path}: body line {line_index + 1}: malformed source note; expected "
                "`evidence-id`: source label; imported YYYY-MM-DD; optional locator."
            )
        evidence_id, source_label, imported_date, locator = match.groups()
        if evidence_id in seen:
            raise WorkflowError(f"{path}: duplicate source note for evidence id '{evidence_id}'.")
        if evidence_id not in evidence_ids:
            raise WorkflowError(
                f"{path}: source note references unknown evidence id '{evidence_id}'."
            )
        try:
            datetime.strptime(imported_date, "%Y-%m-%d")
        except ValueError as exc:
            raise WorkflowError(
                f"{path}: source note for '{evidence_id}' has invalid import date '{imported_date}'."
            ) from exc
        if not source_label.strip() or (locator is not None and not locator.strip()):
            raise WorkflowError(f"{path}: source note fields must not be empty.")
        seen.add(evidence_id)


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

        local_evidence_ids: set[str] = set()
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
            local_evidence_ids.add(evidence_id)
        source_note_ids(path, body, local_evidence_ids)

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
    destination.write_text(profile_index_content(records), encoding="utf-8")
    return destination


def profile_index_content(records: list[dict[str, Any]]) -> str:
    return yaml.safe_dump(
        {"version": 1, "records": records},
        sort_keys=False,
        allow_unicode=True,
    )


def profile_tree_snapshot(profile_dir: Path) -> dict[str, str]:
    root = profile_dir.resolve()
    if profile_dir.is_symlink() or not root.is_dir():
        raise WorkflowError(f"Profile directory not found or unsafe: {profile_dir}")

    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise WorkflowError(f"Profile tree contains an unsafe symbolic link: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise WorkflowError(f"Profile tree contains a non-regular file: {path}")
        relative = path.relative_to(root).as_posix()
        snapshot[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def profile_dependency_fingerprint(profile_dir: Path) -> str:
    root = profile_dir.resolve()
    records = profile_records(profile_dir)
    metadata_records, evidence_ids = validate_profile(profile_dir)
    record_dependencies = []
    for path, metadata, body in records:
        record_dependencies.append(
            {
                "path": path.resolve().relative_to(root).as_posix(),
                "record_id": metadata["id"],
                "evidence_ids": sorted(
                    match.group(1) for match in EVIDENCE_LINE.finditer(body)
                ),
            }
        )
    payload = {
        "records": metadata_records,
        "record_dependencies": record_dependencies,
        "all_ids": sorted(evidence_ids),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def selected_profile_snapshot(profile_dir: Path, relative_paths: set[str]) -> dict[str, str | None]:
    root = profile_dir.resolve()
    if profile_dir.is_symlink() or not root.is_dir():
        raise WorkflowError(f"Profile directory not found or unsafe: {profile_dir}")

    snapshot: dict[str, str | None] = {}
    for relative_path in sorted(relative_paths):
        if relative_path == "index.yaml":
            path = root / relative_path
            if path.is_symlink():
                raise WorkflowError(f"Profile index is an unsafe symbolic link: {path}")
        else:
            path = checked_profile_record_path(root, relative_path)
        if not path.exists():
            snapshot[relative_path] = None
            continue
        if not path.is_file():
            raise WorkflowError(f"Profile update path is not a regular file: {path}")
        snapshot[relative_path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def checked_profile_record_path(root: Path, relative_path: str) -> Path:
    relative = PurePosixPath(relative_path)
    if (
        not relative_path
        or relative.is_absolute()
        or "\\" in relative_path
        or relative.as_posix() != relative_path
        or any(part in {"", ".", ".."} for part in relative.parts)
        or relative.suffix.lower() != ".md"
        or relative.name.lower() == "readme.md"
    ):
        raise WorkflowError(f"Unsafe profile record path: {relative_path!r}")

    candidate = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise WorkflowError(f"Profile record path contains a symbolic link: {relative_path}")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise WorkflowError(f"Profile record path escapes the profile directory: {relative_path}")
    return candidate


def stage_profile_update(
    profile_dir: Path,
    operations_path: Path,
) -> tuple[Path, list[str], str]:
    if operations_path.is_symlink() or not operations_path.is_file():
        raise WorkflowError(f"Update operations file not found or unsafe: {operations_path}")
    try:
        operations = json.loads(operations_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid profile update operations JSON: {exc}") from exc
    if (
        not isinstance(operations, dict)
        or set(operations) != {"writes", "deletes"}
        or not isinstance(operations["writes"], dict)
        or not isinstance(operations["deletes"], list)
    ):
        raise WorkflowError("Profile update operations must contain string writes and a string deletes list.")
    if not operations["writes"] and not operations["deletes"]:
        raise WorkflowError("Profile update contains no changes.")
    if not all(
        isinstance(path, str) and isinstance(content, str)
        for path, content in operations["writes"].items()
    ) or not all(isinstance(path, str) for path in operations["deletes"]):
        raise WorkflowError("Profile update paths and file contents must be strings.")

    write_paths = set(operations["writes"])
    delete_paths = set(operations["deletes"])
    if len(operations["deletes"]) != len(delete_paths) or write_paths & delete_paths:
        raise WorkflowError("Profile update contains duplicate or conflicting paths.")

    profile_root = profile_dir.resolve()
    promote_paths = write_paths | delete_paths | {"index.yaml"}
    original_paths = selected_profile_snapshot(profile_dir, promote_paths)
    original_dependencies = profile_dependency_fingerprint(profile_dir)
    stage_dir = Path(tempfile.mkdtemp(prefix="resume-profile-update-"))
    candidate_dir = stage_dir / "profile"
    try:
        shutil.copytree(profile_root, candidate_dir)
        for relative_path, content in operations["writes"].items():
            destination = checked_profile_record_path(candidate_dir, relative_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
        for relative_path in operations["deletes"]:
            destination = checked_profile_record_path(candidate_dir, relative_path)
            if not destination.is_file():
                raise WorkflowError(f"Cannot delete missing profile record: {relative_path}")
            destination.unlink()

        records, _ = validate_profile(candidate_dir)
        write_index(candidate_dir, None)
        candidate_snapshot = profile_tree_snapshot(candidate_dir)
        current_paths = selected_profile_snapshot(profile_dir, promote_paths)
        current_dependencies = profile_dependency_fingerprint(profile_dir)
        if current_paths != original_paths or current_dependencies != original_dependencies:
            raise WorkflowError(
                "Profile changed while staging the update. Rebuild the candidate from the current profile."
            )
        candidate_paths = selected_profile_snapshot(candidate_dir, promote_paths)
        changed = sorted(
            path
            for path in promote_paths
            if original_paths.get(path) != candidate_paths.get(path)
        )
        if not changed:
            raise WorkflowError("Profile update contains no changes.")
        manifest = {
            "version": 2,
            "profile_root": str(profile_root),
            "original_paths": original_paths,
            "dependency_fingerprint": original_dependencies,
            "promote_paths": changed,
            "candidate_snapshot": candidate_snapshot,
        }
        (stage_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        diff_parts: list[str] = []
        for relative_path in changed:
            if not relative_path.endswith(".md") and relative_path != "index.yaml":
                continue
            old_path = profile_root / relative_path
            new_path = candidate_dir / relative_path
            old_lines = old_path.read_text(encoding="utf-8").splitlines(keepends=True) if old_path.exists() else []
            new_lines = new_path.read_text(encoding="utf-8").splitlines(keepends=True) if new_path.exists() else []
            diff_parts.extend(
                difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=f"a/profile/{relative_path}",
                    tofile=f"b/profile/{relative_path}",
                )
            )
        return stage_dir, changed, "".join(diff_parts)
    except (OSError, WorkflowError, yaml.YAMLError):
        shutil.rmtree(stage_dir, ignore_errors=True)
        raise


def read_profile_update_stage(stage_dir: Path, profile_dir: Path) -> tuple[Path, dict[str, Any]]:
    resolved_stage = stage_dir.resolve()
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if (
        resolved_stage.parent != temporary_root
        or not resolved_stage.name.startswith("resume-profile-update-")
        or stage_dir.is_symlink()
    ):
        raise WorkflowError(f"Unsafe profile update staging directory: {stage_dir}")
    manifest_path = resolved_stage / "manifest.json"
    candidate_dir = resolved_stage / "profile"
    if manifest_path.is_symlink() or candidate_dir.is_symlink():
        raise WorkflowError(f"Profile update staging directory contains a symbolic link: {resolved_stage}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Invalid profile update staging manifest: {exc}") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("version") != 2
        or manifest.get("profile_root") != str(profile_dir.resolve())
        or not isinstance(manifest.get("original_paths"), dict)
        or not isinstance(manifest.get("dependency_fingerprint"), str)
        or not isinstance(manifest.get("promote_paths"), list)
        or not isinstance(manifest.get("candidate_snapshot"), dict)
        or not candidate_dir.is_dir()
    ):
        raise WorkflowError(f"Profile update staging manifest does not match {profile_dir}.")
    original_paths = manifest["original_paths"]
    promote_paths = manifest["promote_paths"]
    if not all(
        isinstance(path, str)
        and (path == "index.yaml" or checked_profile_record_path(candidate_dir, path))
        and (digest is None or isinstance(digest, str))
        for path, digest in original_paths.items()
    ):
        raise WorkflowError("Profile update staging manifest contains invalid source paths or digests.")
    if (
        not promote_paths
        or not all(isinstance(path, str) for path in promote_paths)
        or len(promote_paths) != len(set(promote_paths))
        or not all(path in original_paths for path in promote_paths)
    ):
        raise WorkflowError("Profile update staging manifest contains invalid promotion paths.")
    expected_promote_paths = {
        path
        for path, original_digest in original_paths.items()
        if original_digest != manifest["candidate_snapshot"].get(path)
    }
    if set(promote_paths) != expected_promote_paths:
        raise WorkflowError("Profile update staging manifest promotion paths do not match the candidate.")
    return candidate_dir, manifest


def promote_profile_update(stage_dir: Path, profile_dir: Path) -> list[str]:
    candidate_dir, manifest = read_profile_update_stage(stage_dir, profile_dir)
    original_paths = manifest["original_paths"]
    promote_paths = set(manifest["promote_paths"])
    current_paths = selected_profile_snapshot(profile_dir, set(original_paths))
    current_dependencies = profile_dependency_fingerprint(profile_dir)
    if (
        current_paths != original_paths
        or current_dependencies != manifest["dependency_fingerprint"]
    ):
        raise WorkflowError(
            "Profile changed after the preview. Rebuild and validate the candidate, then request approval again."
        )
    candidate_snapshot = profile_tree_snapshot(candidate_dir)
    if candidate_snapshot != manifest["candidate_snapshot"]:
        raise WorkflowError("Staged profile candidate changed after validation; rebuild the preview.")
    records, _ = validate_profile(candidate_dir)
    candidate_index = candidate_dir / "index.yaml"
    if (
        candidate_index.is_symlink()
        or not candidate_index.is_file()
        or candidate_index.read_text(encoding="utf-8") != profile_index_content(records)
    ):
        raise WorkflowError("Staged profile candidate index is missing or inconsistent.")

    changed = sorted(promote_paths)
    if not changed:
        raise WorkflowError("Staged profile update has no changes to promote.")
    write_order = [path for path in changed if path != "index.yaml"]
    if "index.yaml" in changed:
        write_order.append("index.yaml")

    backup_dir = Path(tempfile.mkdtemp(prefix="resume-profile-backup-"))
    applied: list[str] = []
    root = profile_dir.resolve()
    preserve_backup = False
    try:
        for relative_path in changed:
            if original_paths[relative_path] is not None:
                backup = backup_dir / relative_path
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root / relative_path, backup)

        if (
            selected_profile_snapshot(profile_dir, set(original_paths)) != original_paths
            or profile_dependency_fingerprint(profile_dir) != manifest["dependency_fingerprint"]
        ):
            raise WorkflowError(
                "Profile changed during promotion preparation. Rebuild the candidate and request approval again."
            )

        def replace_from(source: Path, destination: Path, prefix: str) -> None:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=prefix,
                dir=destination.parent,
            )
            os.close(descriptor)
            temporary_file = Path(temporary_name)
            try:
                shutil.copy2(source, temporary_file)
                os.replace(temporary_file, destination)
            finally:
                if temporary_file.exists():
                    temporary_file.unlink()

        for relative_path in write_order:
            destination = root / relative_path
            staged_source = candidate_dir / relative_path
            if relative_path not in candidate_snapshot:
                destination.unlink()
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                replace_from(
                    staged_source,
                    destination,
                    f".{destination.name}.profile-update-",
                )
            applied.append(relative_path)
    except (OSError, WorkflowError) as exc:
        rollback_errors: list[str] = []
        for relative_path in reversed(applied):
            destination = root / relative_path
            try:
                backup = backup_dir / relative_path
                if original_paths[relative_path] is not None:
                    replace_from(
                        backup,
                        destination,
                        f".{destination.name}.profile-rollback-",
                    )
                elif destination.exists():
                    destination.unlink()
            except OSError as rollback_exc:
                rollback_errors.append(f"{relative_path}: {rollback_exc}")
        details = f"Profile promotion failed: {exc}. "
        if rollback_errors:
            preserve_backup = True
            details += (
                "Rollback failures: "
                + "; ".join(rollback_errors)
                + f". Recovery backups retained at {backup_dir}."
            )
        else:
            details += "Changes were rolled back."
        raise WorkflowError(details) from exc
    finally:
        if not preserve_backup:
            shutil.rmtree(backup_dir, ignore_errors=True)

    try:
        shutil.rmtree(stage_dir)
    except OSError as exc:
        raise WorkflowError(
            f"Profile update was promoted, but staging cleanup failed at {stage_dir}: {exc}"
        ) from exc
    return changed


def discard_profile_update(stage_dir: Path, profile_dir: Path) -> None:
    read_profile_update_stage(stage_dir, profile_dir)
    shutil.rmtree(stage_dir)


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

    stage_parser = subparsers.add_parser(
        "stage-profile-update",
        help="Validate a profile update candidate without modifying the canonical profile.",
    )
    stage_parser.add_argument("--profile-dir", type=Path, default=Path("profile"))
    stage_parser.add_argument("--operations", required=True, type=Path)

    promote_parser = subparsers.add_parser(
        "promote-profile-update",
        help="Promote a validated profile update after explicit user approval.",
    )
    promote_parser.add_argument("--profile-dir", type=Path, default=Path("profile"))
    promote_parser.add_argument("--stage-dir", required=True, type=Path)

    discard_parser = subparsers.add_parser(
        "discard-profile-update",
        help="Discard a staged profile update that the user did not approve.",
    )
    discard_parser.add_argument("--profile-dir", type=Path, default=Path("profile"))
    discard_parser.add_argument("--stage-dir", required=True, type=Path)

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
        elif args.command == "stage-profile-update":
            stage_dir, changed, diff = stage_profile_update(args.profile_dir, args.operations)
            print(
                json.dumps(
                    {
                        "state": "validated",
                        "stage_dir": str(stage_dir),
                        "changed_paths": changed,
                        "diff": diff,
                    },
                    indent=2,
                )
            )
        elif args.command == "promote-profile-update":
            changed = promote_profile_update(args.stage_dir, args.profile_dir)
            print(json.dumps({"state": "promoted", "changed_paths": changed}, indent=2))
        elif args.command == "discard-profile-update":
            discard_profile_update(args.stage_dir, args.profile_dir)
            print(f"Discarded profile update stage: {args.stage_dir}")
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
