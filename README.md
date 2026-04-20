# ResumeBuilder

A YAML-driven resume generator that produces an ATS-friendly, single-page PDF resume using Python and WeasyPrint.

## Features

- All resume content is maintained in a single `resume.yaml` file — no HTML or Python edits needed for content changes
- Outputs both HTML and PDF to a configurable output directory (default: `generated/`)
- ATS-friendly single-column layout
- Output filenames are derived automatically from the profile name in the YAML
- CLI interface with overridable paths

## Requirements

- Python `>=3.10`
- [Poetry](https://python-poetry.org/) for dependency management

## Installation

```bash
git clone https://github.com/S-Dawn/ResumeBuilder.git
cd ResumeBuilder
poetry install
```

## Usage

```bash
# Generate with defaults (reads resume.yaml, writes to generated/)
poetry run python ResumeBuilder.py

# Custom config file
poetry run python ResumeBuilder.py --config path/to/myresume.yaml

# Custom output directory
poetry run python ResumeBuilder.py --output-dir output/

# Fully custom output paths
poetry run python ResumeBuilder.py --html-output my_resume.html --pdf-output my_resume.pdf
```

### CLI Options

| Option | Default | Description |
|---|---|---|
| `--config` | `resume.yaml` | Path to the YAML config file |
| `--output-dir` | `generated` | Directory for generated files |
| `--html-output` | `<Name>_Resume.html` | Override the HTML output filename |
| `--pdf-output` | `<Name>_Resume.pdf` | Override the PDF output filename |

## YAML Structure

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
    - label: GitHub
      url: "https://github.com/yourhandle"

experience_years: "5+"        # Shown in the Professional Experience heading

summary: >
  Brief professional summary...

skills:
  - category: Languages
    items: [Python, Java, Go]
  - category: Frameworks
    items: [FastAPI, Spring Boot]

experience:
  - role: Senior Software Engineer
    company: Acme Corp
    location: Remote
    duration: Jan 2022 – Present
    bullets:
      - Built scalable microservices handling 10k RPS.

projects:
  - name: My Project
    tech: Python, FastAPI
    bullets:
      - Reduced latency by 40%.

education:
  - degree: B.Tech in Computer Science
    institution: Some University
    date: 2019
    score: "GPA: 3.8"

certifications_and_achievements:
  - "Achievements: Best Employee Award 2023"
  - "Certifications: AWS Solutions Architect Associate"
```

## Output

Generated files are written to `generated/` (or your chosen `--output-dir`):

```
generated/
  Subham_Dawn_Resume.html
  Subham_Dawn_Resume.pdf
```

## Project Structure

```
ResumeBuilder/
├── ResumeBuilder.py      # Main script
├── resume.yaml           # Resume data
├── pyproject.toml        # Dependencies (Poetry)
├── .gitignore
└── README.md
```
