from __future__ import annotations

import argparse
import html
from pathlib import Path

import yaml
from pypdf import PdfReader
from weasyprint import HTML

CSS_STYLES = """
    @page {
        size: A4;
        margin: 7mm 8mm 6mm;
        background-color: #ffffff;
    }
    body {
        font-family: "Helvetica", "Arial", sans-serif;
        color: #111;
        line-height: 1.10;
        margin: 0;
        padding: 0;
        font-size: 7.6pt;
    }
    .header {
        text-align: center;
        border-bottom: 1px solid #222;
        padding-bottom: 5px;
        margin-bottom: 6px;
    }
    h1 {
        font-size: 17pt;
        margin: 0;
        color: #111;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .job-title {
        font-size: 10pt;
        font-weight: bold;
        color: #222;
        margin: 2px 0;
    }
    .contact-info {
        font-size: 8.2pt;
        color: #333;
    }
    .contact-info a {
        color: #111;
        text-decoration: none;
    }
    h2 {
        font-size: 9pt;
        color: #111;
        border-bottom: 1px solid #222;
        padding-bottom: 1px;
        margin: 6px 0 3px 0;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    p {
        margin: 0 0 4px 0;
    }
    .experience-item, .project-item {
        margin-bottom: 3px;
    }
    .item-header {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        font-weight: bold;
        margin-bottom: 1px;
    }
    .item-sub {
        color: #333;
        font-size: 8.2pt;
        margin-bottom: 1px;
    }
    ul {
        margin: 1px 0 3px 12px;
        padding: 0;
    }
    li {
        margin-bottom: 0;
    }
    .skills-line {
        margin-bottom: 3px;
    }
    .skills-label,
    .bold {
        font-weight: bold;
    }
    .section-tight {
        margin-bottom: 2px;
    }
    .project-points {
        margin: 1px 0 2px 12px;
    }
    .subline {
        display: flex;
        justify-content: space-between;
        gap: 12px;
    }
    .muted {
        color: #333;
    }
"""


def esc(value: str | None) -> str:
    return html.escape(value or "")


def build_contact_line(profile: dict) -> str:
    parts: list[str] = []

    if profile.get("phone"):
        parts.append(esc(profile["phone"]))

    if profile.get("email"):
        email = esc(profile["email"])
        parts.append(f'<a href="mailto:{email}">{email}</a>')

    for link in profile.get("links", []):
        label = esc(link.get("label", ""))
        url = esc(link.get("url", "#"))
        parts.append(f'<a href="{url}">{label}</a>')

    if profile.get("location"):
        parts.append(esc(profile["location"]))

    return " | ".join(parts)


def render_skills(skills: list[dict]) -> str:
    rows: list[str] = []
    for skill in skills:
        category = esc(skill.get("category", ""))
        items = skill.get("items", [])
        if isinstance(items, list):
            item_text = ", ".join(esc(str(item)) for item in items)
        else:
            item_text = esc(str(items))
        rows.append(
            f"""
        <div class=\"skills-line\"><span class=\"skills-label\">{category}:</span> {item_text}</div>
        """
        )

    return "\n".join(rows)


def render_experience(experience: list[dict]) -> str:
    blocks: list[str] = []
    for item in experience:
        role = esc(item.get("role", ""))
        company = esc(item.get("company", ""))
        location = esc(item.get("location", ""))
        duration = esc(item.get("duration", ""))

        company_line = " | ".join(part for part in [company, location] if part)

        highlights = "\n".join(
            f"<li>{esc(str(highlight))}</li>" for highlight in item.get("highlights", [])
        )
        highlight_list = f"<ul>{highlights}</ul>" if highlights else ""

        blocks.append(
            f"""
    <div class=\"experience-item\">
        <div class=\"item-header\"><span>{role}</span><span>{duration}</span></div>
        <div class=\"item-sub\">{company_line}</div>
        {highlight_list}
    </div>
        """
        )

    return "\n".join(blocks)


def render_projects(projects: list[dict]) -> str:
    blocks: list[str] = []
    for project in projects:
        name = esc(project.get("name", ""))
        description = esc(project.get("description", ""))
        highlights = project.get("highlights", [])

        project_points = ""
        if isinstance(highlights, list) and highlights:
            bullets = "\n".join(
                f"<li>{esc(str(highlight))}</li>" for highlight in highlights
            )
            project_points = f'<ul class="project-points">{bullets}</ul>'

        blocks.append(
            f"""
    <div class=\"project-item\">
        <div class=\"item-header\">{name}</div>
        {f'<div class="item-sub">{description}</div>' if description else ''}
        {project_points}
    </div>
        """
        )

    return "\n".join(blocks)


def render_education(education: list[dict]) -> str:
    items: list[str] = []
    for item in education:
        degree = esc(item.get("degree", ""))
        institution = esc(item.get("institution", ""))
        score = esc(item.get("score", ""))
        date = esc(item.get("date", ""))

        all_parts = [part for part in [degree, institution, date, score] if part]
        line = " | ".join(f"<span class=\"bold\">{all_parts[0]}</span>" if i == 0 else esc(p)
                          for i, p in enumerate(all_parts))
        items.append(f'<div class="section-tight">{line}</div>')

    return "\n".join(items)


def render_bullets(items: list[str]) -> str:
    return "\n".join(f"<li>{esc(str(item))}</li>" for item in items)


def extract_section_items(items: list[str], prefix: str) -> list[str]:
    prefix_with_colon = f"{prefix}:"
    extracted: list[str] = []
    for item in items:
        text = str(item)
        if text.startswith(prefix_with_colon):
            extracted.append(text[len(prefix_with_colon):].strip())
    return extracted


def get_experience_years_label(years: str) -> str:
    if not years:
        return ""
    return f" ({years} Years)"


def build_html(resume: dict) -> str:
    profile = resume.get("profile", {})
    experience = resume.get("experience", [])
    summary = resume.get("summary", "")
    experience_years = resume.get("experience_years", "")
    cert_and_achievement_items = resume.get("certifications_and_achievements", [])
    certifications = extract_section_items(cert_and_achievement_items, "Certifications")
    achievements = extract_section_items(cert_and_achievement_items, "Achievements")
    combined_certifications_and_achievements = []

    if achievements:
        combined_certifications_and_achievements.append(
            f'Achievements: {"; ".join(achievements)}'
        )
    if certifications:
        combined_certifications_and_achievements.append(
            f'Certifications: {"; ".join(certifications)}'
        )

    sections: list[str] = []
    if isinstance(summary, str) and summary.strip():
        sections.append(f'<h2>Professional Summary</h2>\n    <p>{esc(summary)}</p>')

    skills = resume.get("skills", [])
    if skills:
        sections.append(f"<h2>Technical Skills</h2>\n    {render_skills(skills)}")

    if experience:
        sections.append(
            f"<h2>Professional Experience{get_experience_years_label(experience_years)}</h2>\n"
            f"    {render_experience(experience)}"
        )

    projects = resume.get("projects", [])
    if projects:
        sections.append(f"<h2>Projects</h2>\n    {render_projects(projects)}")

    education = resume.get("education", [])
    if education:
        sections.append(f"<h2>Education</h2>\n    {render_education(education)}")

    if combined_certifications_and_achievements:
        sections.append(
            "<h2>Certifications &amp; Achievements</h2>\n"
            f"    <ul>{render_bullets(combined_certifications_and_achievements)}</ul>"
        )

    sections_html = "\n\n    ".join(sections)

    return f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <style>
{CSS_STYLES}
    </style>
</head>
<body>

    <div class=\"header\">
        <h1>{esc(profile.get("name", ""))}</h1>
        <div class=\"job-title\">{esc(profile.get("title", ""))}</div>
        <div class=\"contact-info\">{build_contact_line(profile)}</div>
    </div>

    {sections_html}

</body>
</html>
"""


def validate_pdf_output(
    pdf_path: Path,
    resume: dict,
    html_content: str,
    allow_multiple_pages: bool = False,
) -> int:
    lowered_html = html_content.lower()
    if (
        "<table" in lowered_html
        or "column-count" in lowered_html
        or "grid-template-columns" in lowered_html
    ):
        raise ValueError("Generated HTML is not a supported single-column layout.")

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    if page_count != 1 and not allow_multiple_pages:
        return page_count

    text_fragments: list[tuple[int, str, float, float]] = []

    def collect_text_position(page_number: int):
        def collect(
            text: str,
            _current_matrix: list[float],
            text_matrix: list[float],
            _font_dictionary: dict | None,
            _font_size: float,
        ) -> None:
            if text.strip():
                text_fragments.append(
                    (page_number, text, float(text_matrix[4]), float(text_matrix[5]))
                )

        return collect

    extracted_text = "\n".join(
        page.extract_text(visitor_text=collect_text_position(page_number)) or ""
        for page_number, page in enumerate(reader.pages)
    )
    if not extracted_text.strip():
        raise ValueError("Generated PDF contains no extractable text.")

    expected_headings: list[str] = []
    if isinstance(resume.get("summary"), str) and resume["summary"].strip():
        expected_headings.append("Professional Summary")
    if resume.get("skills"):
        expected_headings.append("Technical Skills")
    if resume.get("experience"):
        expected_headings.append("Professional Experience")
    if resume.get("projects"):
        expected_headings.append("Projects")
    if resume.get("education"):
        expected_headings.append("Education")
    if resume.get("certifications_and_achievements"):
        expected_headings.append("Certifications & Achievements")

    normalized_text = " ".join(extracted_text.split()).casefold()
    previous_index = -1
    for heading in expected_headings:
        current_index = normalized_text.find(heading.casefold(), previous_index + 1)
        if current_index < 0:
            raise ValueError(f"Generated PDF is missing expected heading: {heading}")
        previous_index = current_index

    if expected_headings:
        first_heading = expected_headings[0].casefold()
        body_start = next(
            (
                y
                for page_number, text, _x, y in text_fragments
                if page_number == 0 and first_heading in text.casefold()
            ),
            None,
        )
        if body_start is None:
            raise ValueError("Could not locate the first section heading in the PDF text layout.")

        page_widths = [float(page.mediabox.width) for page in reader.pages]
        rows: dict[tuple[int, int], set[str]] = {}
        for page_number, _text, x, y in text_fragments:
            if page_number == 0 and y < body_start:
                continue
            page_width = page_widths[page_number]
            row_key = (page_number, round(y / 2))
            columns = rows.setdefault(row_key, set())
            if x < page_width * 0.45:
                columns.add("left")
            elif x > page_width * 0.55:
                columns.add("right")
        split_rows = sum(1 for columns in rows.values() if {"left", "right"} <= columns)
        if split_rows >= 4:
            raise ValueError(
                "Generated PDF text placement indicates a multi-column body layout."
            )

    return page_count


def load_resume_data(yaml_path: Path) -> dict:
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("The YAML root must be a mapping/object.")

    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate resume HTML and PDF from a YAML configuration file."
    )
    parser.add_argument(
        "--config",
        default="resume.yaml",
        help="Path to resume YAML file (default: resume.yaml).",
    )
    parser.add_argument(
        "--output-dir",
        default="generated",
        help="Directory where generated files are written (default: generated).",
    )
    parser.add_argument(
        "--html-output",
        default=None,
        help="HTML output filename (default: derived from profile name in YAML).",
    )
    parser.add_argument(
        "--pdf-output",
        default=None,
        help="PDF output filename (default: derived from profile name in YAML).",
    )
    parser.add_argument(
        "--strict-one-page",
        action="store_true",
        help="Fail unless the generated PDF is one page with extractable text and expected headings.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"YAML config not found: {config_path}")

    resume = load_resume_data(config_path)
    html_content = build_html(resume)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    profile_name = resume.get("profile", {}).get("name", "Resume")
    stem = profile_name.strip().replace(" ", "_")

    html_path = Path(args.html_output) if args.html_output else Path(f"{stem}_Resume.html")
    pdf_path = Path(args.pdf_output) if args.pdf_output else Path(f"{stem}_Resume.pdf")

    if not html_path.is_absolute():
        html_path = output_dir / html_path
    if not pdf_path.is_absolute():
        pdf_path = output_dir / pdf_path

    html_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    html_path.write_text(html_content, encoding="utf-8")
    HTML(str(html_path)).write_pdf(str(pdf_path))
    if args.strict_one_page:
        page_count = validate_pdf_output(pdf_path, resume, html_content)
        if page_count != 1:
            raise ValueError(
                f"Strict one-page validation failed: generated PDF has {page_count} pages."
            )


if __name__ == "__main__":
    main()
