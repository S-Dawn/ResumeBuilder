# ResumeBuilder

A Python/WeasyPrint resume generator with a reusable career evidence profile and GitHub Copilot skill for creating role-specific resume drafts.

## Features

- Keep complete career evidence in `profile/` Markdown records with YAML frontmatter and stable claim IDs.
- Generate a compact index from profile metadata on demand; the Copilot skill reads only relevant profile details.
- Tailor a draft from a pasted or file-based job description with a source map and fit report, or create a consolidated master resume when no job description is supplied.
- Keep each draft's YAML, source map, HTML, and PDF in an isolated directory under `generated/`; tailored drafts include a fit report and master resumes include a conflict report.
- Check generated YAML, source references, PDF text, conventional section order, and strict one-page fit for tailored drafts. Master resumes retain all profile evidence and may span multiple pages.
- Preserve the original `resume.yaml` renderer workflow.

## Requirements

- Python `>=3.10`
- [Poetry](https://python-poetry.org/) for dependency management

## Installation

```bash
git clone https://github.com/S-Dawn/ResumeBuilder.git
cd ResumeBuilder
poetry install
```

## Generate from the legacy YAML

```bash
# Reads resume.yaml and writes HTML/PDF to generated/
poetry run python ResumeBuilder.py

# Use a custom YAML configuration and output directory
poetry run python ResumeBuilder.py --config path/to/myresume.yaml --output-dir output/

# Enforce a one-page PDF and extracted-text checks
poetry run python ResumeBuilder.py --strict-one-page
```

## Analyze profile fit with GitHub Copilot

Use the **Analyze Profile Fit** skill with a pasted job description or a path to a job-description file to assess a role before deciding whether to apply. It compares relevant job qualifications with evidence in the canonical profile and reports supported, partially supported, and undocumented requirements with profile evidence IDs.

The report includes a qualitative assessment and a transparent weighted evidence-coverage score: supported qualifications receive full credit, partial matches half credit, unsupported qualifications no credit, and explicitly required qualifications count twice as much as preferred or other requirements. The score describes only what the profile documents; it is not a hiring or ATS prediction. The analysis distinguishes information to verify in the profile, positioning ideas based on existing evidence, and conditional skill-development areas.

This diagnostic does not create a resume, application draft, profile update, or retained report. For file-based job descriptions, the skill discloses that relevant job-description and profile contents are sent as context to the configured Copilot model and asks for confirmation before reading the file. The full job description is not retained. Profile silence is not treated as proof that the user lacks a qualification.

## Tailor a resume with GitHub Copilot

Use the **Tailor Resume** skill in GitHub Copilot in VS Code and provide either a pasted job description or a path to a job-description file to create a tailored draft. If you provide no job description, the skill creates a consolidated master resume from all profile records and evidence.

For a master resume, the skill:

1. Reads every indexed profile record and includes all distinct supported details.
2. Produces `resume.yaml` and a `source-map.json` that trace every content field and cover every non-conflicting profile evidence ID.
3. Creates `master-report.md` to disclose conflicting claims excluded for clarification.
4. Creates an isolated `master-resume` draft, renders it, and validates its extracted text and single-column structure without a page or word-count limit.

For a job-tailored draft, the skill:

1. Rebuilds and reads `profile/index.yaml`, then fetches relevant profile records as needed.
2. Produces a tailored `resume.yaml`, `source-map.json`, and `fit-report.md`.
3. Creates an isolated application draft under `generated/`, renders it, and checks the actual PDF.
4. Uses the extracted PDF word count to guide content revisions toward a soft 900-word target without screenshots; strict one-page validation and readability remain authoritative.
5. Presents the draft for human review; it does not submit applications.

The skill may substantially rewrite claims, but it must not invent or alter factual claims. It flags conflicting source evidence and, for tailored drafts, identifies unsupported job requirements instead of inventing qualifications. ATS-oriented checks cover text extraction, conventional headings/order, and single-column layout; tailored drafts are also checked for one-page fit. These checks do not guarantee compatibility with every ATS vendor.

Tailored fit reports use `Evidence-backed matches` and `Unsupported or weakly supported requirements` sections. Supported requirements cite profile evidence IDs, and validation rejects unknown IDs or missing sections. Master resumes have no fit report because no target role is assessed.

If an application output already exists, choose a numbered draft, explicitly authorize replacement, or cancel. The default when interaction is unavailable is cancellation. Failed drafts are retained and marked failed for diagnosis.

### Copilot data handling

Selected profile records and the job description are sent as context to the user's configured Copilot model. Do not store secrets in profile records. The full job description is not copied into retained generated artifacts.

## Maintain the profile

See [profile/README.md](profile/README.md) for the Markdown/frontmatter format, stable evidence IDs, validation, and index behavior. Validate and rebuild the compact index with:

```bash
poetry run python resume_tools.py validate-profile
poetry run python resume_tools.py profile-index
```

Use the **Maintain Profile** Copilot skill for full-resume or career-fact consolidation, and **Update Projects** for focused changes to project records. Both preview and validate the complete update before requesting explicit approval; neither treats a tailored application resume as a canonical source. File and selected project-repository content is sent to the configured Copilot model only after disclosure and confirmation.

## Renderer YAML structure

The renderer uses `highlights` for experience and project bullets:

```yaml
profile:
  name: Your Name
  title: Your Job Title
  phone: "+1 234 567 8900"
  email: you@example.com
  location: City, Country
  links:
    - label: LinkedIn
      url: "https://linkedin.com/in/yourprofile"
summary: A concise professional summary.
skills:
  - category: Languages
    items: [Python, Java]
experience:
  - role: Senior Software Engineer
    company: Acme Corp
    location: Remote
    duration: Jan 2022 - Present
    highlights:
      - Built scalable microservices handling 10k requests per second.
projects:
  - name: Example Project
    highlights:
      - Reduced processing time by 30%.
education:
  - degree: B.Tech in Computer Science
    institution: Example University
    date: 2019
    score: "GPA: 3.8"
certifications_and_achievements:
  - "Achievements: Example Award"
  - "Certifications: Example Certificate"
```

Empty optional sections are omitted from the rendered output.
