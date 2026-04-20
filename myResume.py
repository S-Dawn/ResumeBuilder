from __future__ import annotations

import argparse
import html
from pathlib import Path

import yaml
from weasyprint import HTML

CSS_STYLES = """
    @page {
        size: A4;
        margin: 15mm 12mm;
        background-color: #ffffff;
    }
    body {
        font-family: "Helvetica", "Arial", sans-serif;
        color: #333;
        line-height: 1.4;
        margin: 0;
        padding: 0;
        font-size: 10pt;
    }
    .header {
        text-align: center;
        border-bottom: 2px solid #2c3e50;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }
    h1 {
        font-size: 20pt;
        margin: 0;
        color: #2c3e50;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .job-title {
        font-size: 13pt;
        font-weight: bold;
        color: #555;
        margin: 5px 0;
    }
    .contact-info {
        font-size: 9pt;
        color: #666;
    }
    .contact-info a {
        color: #2980b9;
        text-decoration: none;
    }
    h2 {
        font-size: 13pt;
        color: #2c3e50;
        border-left: 4px solid #2c3e50;
        padding-left: 8px;
        margin: 18px 0 8px 0;
        text-transform: uppercase;
        background-color: #f8f9fa;
    }
    h3 {
        font-size: 11pt;
        margin: 12px 0 4px 0;
        color: #333;
    }
    .experience-item, .project-item {
        margin-bottom: 12px;
    }
    .item-header {
        display: block;
        font-weight: bold;
        margin-bottom: 2px;
    }
    .item-sub {
        font-style: italic;
        color: #666;
        font-size: 9.5pt;
        margin-bottom: 4px;
    }
    ul {
        margin: 4px 0 8px 18px;
        padding: 0;
    }
    li {
        margin-bottom: 4px;
    }
    .skills-grid {
        width: 100%;
    }
    .skills-grid td {
        vertical-align: top;
        padding-bottom: 4px;
    }
    .skill-cat {
        font-weight: bold;
        width: 130px;
    }
    .bold { font-weight: bold; }
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
        <tr>
            <td class=\"skill-cat\">{category}:</td>
            <td>{item_text}</td>
        </tr>
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

        header_parts = [part for part in [role, company, location] if part]
        header_text = " | ".join(header_parts)

        highlights = "\n".join(
            f"<li>{esc(str(highlight))}</li>" for highlight in item.get("highlights", [])
        )

        blocks.append(
            f"""
    <div class=\"experience-item\">
        <div class=\"item-header\">{header_text}</div>
        <div class=\"item-sub\">{duration}</div>
        <ul>
            {highlights}
        </ul>
    </div>
        """
        )

    return "\n".join(blocks)


def render_projects(projects: list[dict]) -> str:
    blocks: list[str] = []
    for project in projects:
        name = esc(project.get("name", ""))
        description = esc(project.get("description", ""))
        blocks.append(
            f"""
    <div class=\"project-item\">
        <div class=\"item-header\">{name}</div>
        <p style=\"margin: 2px 0 8px 0;\">{description}</p>
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

        details = " | ".join(part for part in [institution, score, date] if part)
        items.append(
            f"""
    <div style=\"margin-bottom: 5px;\">
        <span class=\"bold\">{degree}</span>{" | " + details if details else ""}
    </div>
        """
        )

    return "\n".join(items)


def render_bullets(items: list[str]) -> str:
    return "\n".join(f"<li>{esc(str(item))}</li>" for item in items)


def build_html(resume: dict) -> str:
    profile = resume.get("profile", {})

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

    <h2>Professional Summary</h2>
    <p>{esc(resume.get("summary", ""))}</p>

    <h2>Technical Skills</h2>
    <table class=\"skills-grid\">
        {render_skills(resume.get("skills", []))}
    </table>

    <h2>Professional Experience</h2>
    {render_experience(resume.get("experience", []))}

    <h2>Core Projects</h2>
    {render_projects(resume.get("projects", []))}

    <h2>Education</h2>
    {render_education(resume.get("education", []))}

    <h2>Certifications & Achievements</h2>
    <ul>
        {render_bullets(resume.get("certifications_and_achievements", []))}
    </ul>

</body>
</html>
"""


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
        default="Subham_Dawn_Resume_Updated.html",
        help="HTML output path.",
    )
    parser.add_argument(
        "--pdf-output",
        default="Subham_Dawn_Resume_Updated.pdf",
        help="PDF output path.",
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

    html_path = Path(args.html_output)
    pdf_path = Path(args.pdf_output)

    if not html_path.is_absolute():
        html_path = output_dir / html_path
    if not pdf_path.is_absolute():
        pdf_path = output_dir / pdf_path

    html_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    html_path.write_text(html_content, encoding="utf-8")
    HTML(str(html_path)).write_pdf(str(pdf_path))


if __name__ == "__main__":
    main()
