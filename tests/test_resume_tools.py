from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from pypdf import PdfWriter

import resume_tools
from ResumeBuilder import build_html, validate_pdf_output
from weasyprint import HTML


def write_profile(profile_dir: Path) -> None:
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "record.md").write_text(
        """---
id: test-record
type: project
title: Test Project
summary: A project used in tests.
skills:
  - Python
tags:
  - backend
---

## Evidence

- [test-evidence] Built a tested Python service.
""",
        encoding="utf-8",
    )


def sample_resume() -> dict:
    return {
        "profile": {
            "name": "Test User",
            "title": "Software Engineer",
            "email": "test@example.com",
            "links": [{"label": "GitHub", "url": "https://example.com"}],
        },
        "summary": "Builds reliable backend services.",
        "skills": [],
        "experience": [
            {
                "role": "Software Engineer",
                "company": "Example Co",
                "duration": "2022 - Present",
                "highlights": ["Built a tested Python service."],
            }
        ],
        "projects": [],
        "education": [],
        "certifications_and_achievements": [],
    }


def write_draft_files(draft_dir: Path, profile_dir: Path, resume: dict | None = None) -> None:
    content = resume or sample_resume()
    (draft_dir / "resume.yaml").write_text(
        yaml.safe_dump(content, sort_keys=False),
        encoding="utf-8",
    )
    mapped_paths = sorted(resume_tools.collect_string_paths(content))
    (draft_dir / "source-map.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "path": path,
                        "source_evidence_ids": ["test-evidence"],
                    }
                    for path in mapped_paths
                ]
            }
        ),
        encoding="utf-8",
    )
    (draft_dir / "fit-report.md").write_text(
        "# Fit report\n\n## Evidence-backed matches\n"
        "- Backend API — evidence: `test-evidence`\n\n"
        "## Unsupported or weakly supported requirements\n"
        "- None identified\n",
        encoding="utf-8",
    )


class ProfileTests(unittest.TestCase):
    def test_profile_index_is_rebuilt_from_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            profile_dir = Path(temporary_directory) / "profile"
            write_profile(profile_dir)
            index_path = resume_tools.write_index(profile_dir, None)
            index_text = index_path.read_text(encoding="utf-8")
            index = yaml.safe_load(index_text)

        self.assertEqual(index["version"], 1)
        self.assertEqual(index["records"][0]["id"], "test-record")
        self.assertEqual(index["records"][0]["tags"], ["backend"])
        self.assertNotIn("Built a tested Python service.", index_text)

    def test_profile_validation_rejects_duplicate_evidence_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            profile_dir = Path(temporary_directory) / "profile"
            write_profile(profile_dir)
            (profile_dir / "duplicate.md").write_text(
                """---
id: second-record
type: project
title: Second Project
summary: Another project.
---
- [test-evidence] Duplicate evidence.
""",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(resume_tools.WorkflowError, "duplicate evidence id"):
                resume_tools.validate_profile(profile_dir)

    def test_profile_validation_requires_ids_on_markdown_bullets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            profile_dir = Path(temporary_directory) / "profile"
            write_profile(profile_dir)
            path = profile_dir / "record.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n- Missing evidence id.\n", encoding="utf-8")
            with self.assertRaisesRegex(resume_tools.WorkflowError, "stable \\[evidence-id\\]"):
                resume_tools.validate_profile(profile_dir)

    def test_profile_validation_accepts_keyed_source_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            profile_dir = Path(temporary_directory) / "profile"
            write_profile(profile_dir)
            path = profile_dir / "record.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\n## Source notes\n"
                "`test-evidence`: User-provided in conversation; imported 2026-10-20; "
                "locator: project details\n",
                encoding="utf-8",
            )

            records, evidence_ids = resume_tools.validate_profile(profile_dir)

        self.assertEqual(len(records), 1)
        self.assertIn("test-evidence", evidence_ids)

    def test_profile_validation_rejects_malformed_duplicate_and_orphan_source_notes(self) -> None:
        invalid_notes = (
            "`test-evidence`: User-provided in conversation; imported 2026-14-20",
            "`unknown-evidence`: User-provided in conversation; imported 2026-10-20",
            "`test-evidence`: User-provided in conversation; imported 2026-10-20\n"
            "`test-evidence`: Another source; imported 2026-10-20",
        )
        for source_notes in invalid_notes:
            with self.subTest(source_notes=source_notes), tempfile.TemporaryDirectory() as temporary_directory:
                profile_dir = Path(temporary_directory) / "profile"
                write_profile(profile_dir)
                path = profile_dir / "record.md"
                path.write_text(
                    path.read_text(encoding="utf-8")
                    + "\n## Source notes\n"
                    + source_notes
                    + "\n",
                    encoding="utf-8",
                )
                with self.assertRaises(resume_tools.WorkflowError):
                    resume_tools.validate_profile(profile_dir)


class ProfileUpdateTests(unittest.TestCase):
    def write_operations(self, root: Path, contents: str) -> Path:
        operations_path = root / "operations.json"
        operations_path.write_text(
            json.dumps(
                {
                    "writes": {"record.md": contents},
                    "deletes": [],
                }
            ),
            encoding="utf-8",
        )
        return operations_path

    def updated_record(self, profile_dir: Path) -> str:
        return (
            (profile_dir / "record.md")
            .read_text(encoding="utf-8")
            .replace("A project used in tests.", "An updated project used in tests.")
            + (
            "\n- [test-impact] Improved service reliability.\n"
            "\n## Source notes\n"
            "`test-impact`: User-provided in conversation; imported 2026-10-20; "
            "locator: project details\n"
            )
        )

    def test_stage_validates_candidate_and_does_not_modify_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            original = (profile_dir / "record.md").read_bytes()
            operations = self.write_operations(root, self.updated_record(profile_dir))

            stage_dir, changed, diff = resume_tools.stage_profile_update(profile_dir, operations)
            try:
                self.assertIn("record.md", changed)
                self.assertIn("index.yaml", changed)
                self.assertIn("+- [test-impact]", diff)
                self.assertEqual((profile_dir / "record.md").read_bytes(), original)
                self.assertTrue((stage_dir / "profile" / "index.yaml").exists())
            finally:
                resume_tools.discard_profile_update(stage_dir, profile_dir)

    def test_stage_rejects_invalid_candidate_without_mutating_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            record_path = profile_dir / "record.md"
            original = record_path.read_bytes()
            operations = self.write_operations(
                root,
                record_path.read_text(encoding="utf-8") + "\n- [test-evidence] Duplicate claim.\n",
            )

            with self.assertRaisesRegex(resume_tools.WorkflowError, "duplicate evidence id"):
                resume_tools.stage_profile_update(profile_dir, operations)
            self.assertEqual(record_path.read_bytes(), original)

    def test_stage_rejects_paths_outside_profile_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            operations = root / "operations.json"
            operations.write_text(
                json.dumps({"writes": {"../resume.yaml": "unsafe"}, "deletes": []}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(resume_tools.WorkflowError, "Unsafe profile record path"):
                resume_tools.stage_profile_update(profile_dir, operations)

    def test_promotion_allows_unrelated_profile_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            unrelated_record = profile_dir / "other.md"
            unrelated_record.write_text(
                """---
id: other-record
type: project
title: Other Project
summary: Another project.
---

## Evidence

- [other-evidence] Original unrelated claim.
""",
                encoding="utf-8",
            )
            operations = self.write_operations(root, self.updated_record(profile_dir))
            stage_dir, _, _ = resume_tools.stage_profile_update(profile_dir, operations)
            unrelated_record.write_text(
                unrelated_record.read_text(encoding="utf-8").replace(
                    "Original unrelated claim.",
                    "Updated unrelated wording without changing IDs or metadata.",
                ),
                encoding="utf-8",
            )
            marker = profile_dir / "local-note.txt"
            marker.write_text("unrelated file", encoding="utf-8")
            try:
                changed = resume_tools.promote_profile_update(stage_dir, profile_dir)
                self.assertIn("record.md", changed)
                self.assertTrue(marker.exists())
                self.assertIn(
                    "Updated unrelated wording",
                    unrelated_record.read_text(encoding="utf-8"),
                )
                self.assertIn("test-impact", (profile_dir / "record.md").read_text(encoding="utf-8"))
            finally:
                if stage_dir.exists():
                    resume_tools.discard_profile_update(stage_dir, profile_dir)

    def test_promotion_rejects_relevant_profile_change_without_overwriting_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            operations = self.write_operations(root, self.updated_record(profile_dir))
            stage_dir, _, _ = resume_tools.stage_profile_update(profile_dir, operations)
            record_path = profile_dir / "record.md"
            record_path.write_text(
                record_path.read_text(encoding="utf-8").replace(
                    "Built a tested Python service.",
                    "Built a revised Python service.",
                ),
                encoding="utf-8",
            )
            try:
                with self.assertRaisesRegex(resume_tools.WorkflowError, "changed after the preview"):
                    resume_tools.promote_profile_update(stage_dir, profile_dir)
                self.assertIn(
                    "revised Python service",
                    record_path.read_text(encoding="utf-8"),
                )
                self.assertNotIn("test-impact", record_path.read_text(encoding="utf-8"))
            finally:
                resume_tools.discard_profile_update(stage_dir, profile_dir)

    def test_promotion_rejects_global_evidence_id_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            operations = self.write_operations(root, self.updated_record(profile_dir))
            stage_dir, _, _ = resume_tools.stage_profile_update(profile_dir, operations)
            unrelated_record = profile_dir / "other.md"
            unrelated_record.write_text(
                """---
id: other-record
type: project
title: Other Project
summary: Another project.
---

- [new-global-evidence] A new claim changes global evidence IDs.
""",
                encoding="utf-8",
            )
            try:
                with self.assertRaisesRegex(resume_tools.WorkflowError, "changed after the preview"):
                    resume_tools.promote_profile_update(stage_dir, profile_dir)
                self.assertTrue(unrelated_record.exists())
                self.assertNotIn("test-impact", (profile_dir / "record.md").read_text(encoding="utf-8"))
            finally:
                resume_tools.discard_profile_update(stage_dir, profile_dir)

    def test_promotion_rolls_back_record_when_index_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            record_path = profile_dir / "record.md"
            original_record = record_path.read_bytes()
            operations = self.write_operations(root, self.updated_record(profile_dir))
            stage_dir, _, _ = resume_tools.stage_profile_update(profile_dir, operations)
            real_replace = os.replace
            replace_calls = 0

            def fail_index_replace(source: object, destination: object) -> None:
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls == 2:
                    raise OSError("simulated index promotion failure")
                real_replace(source, destination)

            try:
                with patch.object(resume_tools.os, "replace", side_effect=fail_index_replace):
                    with self.assertRaisesRegex(resume_tools.WorkflowError, "Changes were rolled back"):
                        resume_tools.promote_profile_update(stage_dir, profile_dir)
                self.assertEqual(record_path.read_bytes(), original_record)
                self.assertFalse((profile_dir / "index.yaml").exists())
            finally:
                resume_tools.discard_profile_update(stage_dir, profile_dir)

    def test_promotion_retains_recovery_backup_when_rollback_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            record_path = profile_dir / "record.md"
            original_record = record_path.read_bytes()
            operations = self.write_operations(root, self.updated_record(profile_dir))
            stage_dir, _, _ = resume_tools.stage_profile_update(profile_dir, operations)
            real_replace = os.replace
            replace_calls = 0
            backup_dir: Path | None = None
            error_text = ""

            def fail_index_and_rollback(source: object, destination: object) -> None:
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls in {2, 3}:
                    raise OSError("simulated promotion/rollback failure")
                real_replace(source, destination)

            try:
                with patch.object(resume_tools.os, "replace", side_effect=fail_index_and_rollback):
                    with self.assertRaisesRegex(
                        resume_tools.WorkflowError,
                        "Recovery backups retained at",
                    ) as error:
                        resume_tools.promote_profile_update(stage_dir, profile_dir)
                error_text = str(error.exception)
                backup_dir = Path(error_text.split("Recovery backups retained at ", 1)[1].rstrip("."))
                self.assertTrue((backup_dir / "record.md").is_file())
                self.assertEqual((backup_dir / "record.md").read_bytes(), original_record)
                self.assertIn("test-impact", record_path.read_text(encoding="utf-8"))
            finally:
                if backup_dir is not None:
                    shutil.rmtree(backup_dir, ignore_errors=True)
                resume_tools.discard_profile_update(stage_dir, profile_dir)

    def test_successful_promotion_updates_records_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            operations = self.write_operations(root, self.updated_record(profile_dir))
            stage_dir, _, _ = resume_tools.stage_profile_update(profile_dir, operations)

            changed = resume_tools.promote_profile_update(stage_dir, profile_dir)
            records, evidence_ids = resume_tools.validate_profile(profile_dir)
            index = yaml.safe_load((profile_dir / "index.yaml").read_text(encoding="utf-8"))

        self.assertIn("record.md", changed)
        self.assertIn("index.yaml", changed)
        self.assertIn("test-impact", evidence_ids)
        self.assertEqual(index["records"], records)


class ResumeValidationTests(unittest.TestCase):
    def test_rejects_unsupported_yaml_fields(self) -> None:
        resume = sample_resume()
        resume["unexpected"] = "not supported"
        with self.assertRaisesRegex(resume_tools.WorkflowError, "Unsupported resume field"):
            resume_tools.validate_resume_data(resume)

    def test_source_map_requires_every_string_and_known_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            resume = sample_resume()
            source_map_path = root / "source-map.json"
            source_map_path.write_text('{"items": []}', encoding="utf-8")
            with self.assertRaisesRegex(resume_tools.WorkflowError, "unmapped content"):
                resume_tools.validate_source_map(resume, source_map_path, profile_dir)

            (root / "draft").mkdir()
            draft_map = root / "draft" / "source-map.json"
            draft_map.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "path": path,
                                "source_evidence_ids": ["unknown-evidence"],
                            }
                            for path in sorted(resume_tools.collect_string_paths(resume))
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(resume_tools.WorkflowError, "unknown evidence id"):
                resume_tools.validate_source_map(resume, draft_map, profile_dir)

    def test_fit_report_requires_requirement_mapping_and_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            fit_report_path = root / "fit-report.md"
            fit_report_path.write_text(
                "# Fit report\n\n"
                "## Evidence-backed matches\n"
                "- Backend API — evidence: `test-evidence`\n\n"
                "## Unsupported or weakly supported requirements\n"
                "- Production Kubernetes — weakly supported; evidence: `test-evidence`\n",
                encoding="utf-8",
            )
            resume_tools.validate_fit_report(fit_report_path, profile_dir)

            fit_report_path.write_text(
                "# Fit report\n\n"
                "## Evidence-backed matches\n"
                "- Backend API — evidence: `missing-evidence`\n\n"
                "## Unsupported or weakly supported requirements\n"
                "- None identified\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(resume_tools.WorkflowError, "unknown evidence ID"):
                resume_tools.validate_fit_report(fit_report_path, profile_dir)

            fit_report_path.write_text(
                "# Fit report\n\n"
                "## Evidence-backed matches\n"
                "- Backend API\n\n"
                "## Unsupported or weakly supported requirements\n"
                "- None identified\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(resume_tools.WorkflowError, "must include evidence IDs"):
                resume_tools.validate_fit_report(fit_report_path, profile_dir)


class DraftTests(unittest.TestCase):
    def test_collision_creates_numbered_draft_or_requires_explicit_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory) / "generated"
            first = resume_tools.create_draft("Example Role", output_root, "cancel")
            second = resume_tools.create_draft("Example Role", output_root, "new")
            self.assertEqual(second.name, "example-role-draft-2")
            (first / "keep.txt").write_text("preserve", encoding="utf-8")

            replacement = resume_tools.create_draft("Example Role", output_root, "replace")
            self.assertFalse((replacement / "keep.txt").exists())
            self.assertTrue(second.exists())

    def test_noninteractive_collision_cancels_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory) / "generated"
            first = resume_tools.create_draft("Example Role", output_root, "cancel")
            marker = first / "keep.txt"
            marker.write_text("preserve", encoding="utf-8")
            non_tty = io.StringIO()
            with patch.object(non_tty, "isatty", return_value=False), patch.object(
                resume_tools.sys, "stdin", non_tty
            ):
                with self.assertRaisesRegex(resume_tools.WorkflowError, "Cancelled"):
                    resume_tools.create_draft("Example Role", output_root, "ask")
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")

    def test_render_rejects_draft_outside_generated_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            outside_draft = root / "outside"
            outside_draft.mkdir()
            with self.assertRaisesRegex(resume_tools.WorkflowError, "direct child"):
                resume_tools.render_draft(
                    outside_draft,
                    profile_dir,
                    1,
                    generated_root=root / "generated",
                )

    def test_one_page_render_is_validated_and_empty_sections_are_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            draft_dir = resume_tools.create_draft(
                "Example Role", root / "generated", "cancel"
            )
            write_draft_files(draft_dir, profile_dir)

            pages = resume_tools.render_draft(
                draft_dir,
                profile_dir,
                1,
                generated_root=root / "generated",
            )
            html_content = (draft_dir / "resume.html").read_text(encoding="utf-8")
            status = json.loads((draft_dir / "status.json").read_text(encoding="utf-8"))
            extracted_word_count = resume_tools.count_pdf_words(draft_dir / "resume.pdf")

        self.assertEqual(pages, 1)
        self.assertEqual(status["state"], "validated")
        self.assertEqual(status["word_count"], extracted_word_count)
        self.assertGreater(status["word_count"], 0)
        self.assertNotIn("<h2>Technical Skills</h2>", html_content)
        self.assertNotIn("<h2>Projects</h2>", html_content)
        self.assertNotIn("<ul>\n            \n        </ul>", html_content)

    def test_eight_failed_page_attempts_are_retained_and_ninth_is_rejected(self) -> None:
        class TwoPageHtml:
            def __init__(self, *_args: object, **_kwargs: object) -> None:
                pass

            def write_pdf(self, path: str) -> None:
                writer = PdfWriter()
                writer.add_blank_page(width=595, height=842)
                writer.add_blank_page(width=595, height=842)
                with open(path, "wb") as output_file:
                    writer.write(output_file)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            draft_dir = resume_tools.create_draft(
                "Long Role", root / "generated", "cancel"
            )
            write_draft_files(draft_dir, profile_dir)

            with patch.object(resume_tools, "HTML", TwoPageHtml):
                for attempt in range(1, resume_tools.MAX_RENDER_ATTEMPTS + 1):
                    with self.assertRaises(resume_tools.PageFitError):
                        resume_tools.render_draft(
                            draft_dir,
                            profile_dir,
                            attempt,
                            generated_root=root / "generated",
                        )
                rejected_attempt = resume_tools.MAX_RENDER_ATTEMPTS + 1
                with self.assertRaisesRegex(
                    resume_tools.WorkflowError,
                    f"between 1 and {resume_tools.MAX_RENDER_ATTEMPTS}",
                ):
                    resume_tools.render_draft(
                        draft_dir,
                        profile_dir,
                        rejected_attempt,
                        generated_root=root / "generated",
                    )

            status = json.loads((draft_dir / "status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["state"], "failed")
            self.assertEqual(status["render_attempts"], resume_tools.MAX_RENDER_ATTEMPTS)
            self.assertEqual(status["page_count"], 2)
            self.assertEqual(status["word_count"], 0)
            self.assertTrue((draft_dir / "resume.yaml").exists())
            self.assertTrue((draft_dir / "resume.pdf").exists())

    def test_second_application_preserves_first_draft_and_canonical_resume(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        root_resume = repository_root / "resume.yaml"
        original_resume = root_resume.read_bytes()
        profile_sources = {
            path: path.read_bytes()
            for path in (repository_root / "profile").rglob("*.md")
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profile_dir = root / "profile"
            write_profile(profile_dir)
            generated_root = root / "generated"
            first = resume_tools.create_draft("backend-role", generated_root, "cancel")
            write_draft_files(first, profile_dir)
            resume_tools.render_draft(
                first,
                profile_dir,
                1,
                generated_root=generated_root,
            )
            first_pdf = (first / "resume.pdf").read_bytes()

            second_resume = sample_resume()
            second_resume["summary"] = "Delivers agentic AI systems for field deployment."
            second = resume_tools.create_draft("forward-deployed-engineer", generated_root, "cancel")
            write_draft_files(second, profile_dir, second_resume)
            resume_tools.render_draft(
                second,
                profile_dir,
                1,
                generated_root=generated_root,
            )

            self.assertNotEqual(first, second)
            self.assertEqual((first / "resume.pdf").read_bytes(), first_pdf)
            self.assertNotIn("Full job description:", (second / "fit-report.md").read_text(encoding="utf-8"))
            self.assertEqual(
                json.loads((first / "status.json").read_text(encoding="utf-8"))["state"],
                "validated",
            )
            self.assertEqual(
                json.loads((second / "status.json").read_text(encoding="utf-8"))["state"],
                "validated",
            )

        self.assertEqual(root_resume.read_bytes(), original_resume)
        self.assertTrue(all(path.read_bytes() == content for path, content in profile_sources.items()))


class RendererTests(unittest.TestCase):
    def test_empty_sections_are_omitted_and_nonempty_sections_keep_order(self) -> None:
        html_content = build_html(sample_resume())
        self.assertIn("<h2>Professional Summary</h2>", html_content)
        self.assertIn("<h2>Professional Experience</h2>", html_content)
        self.assertNotIn("<h2>Technical Skills</h2>", html_content)
        self.assertLess(
            html_content.index("<h2>Professional Summary</h2>"),
            html_content.index("<h2>Professional Experience"),
        )
        self.assertNotIn("<table", html_content.lower())

    def test_pdf_position_check_rejects_two_column_body(self) -> None:
        resume = {
            "profile": {"name": "Test User"},
            "summary": "Two-column content",
        }
        two_column_html = """
        <html><body>
          <h2>Professional Summary</h2>
          <div style="position:absolute;left:30px;top:100px;width:250px">
            <p>Left column line one</p><p>Left column line two</p>
            <p>Left column line three</p><p>Left column line four</p>
          </div>
          <div style="position:absolute;left:330px;top:100px;width:250px">
            <p>Right column line one</p><p>Right column line two</p>
            <p>Right column line three</p><p>Right column line four</p>
          </div>
        </body></html>
        """
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "two-columns.pdf"
            HTML(string=two_column_html).write_pdf(str(pdf_path))
            with self.assertRaisesRegex(ValueError, "multi-column body"):
                validate_pdf_output(pdf_path, resume, "<h2>Professional Summary</h2>")


if __name__ == "__main__":
    unittest.main()
