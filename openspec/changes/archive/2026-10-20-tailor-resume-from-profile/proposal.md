## Why

The current workflow treats `resume.yaml` as both the maintained source of career evidence and the final resume, so applying to roles with different priorities requires manually removing and restoring content. A reusable evidence profile and job-specific tailoring workflow will preserve the complete career history while producing focused, reviewable application drafts.

## What Changes

- Migrate all current `resume.yaml` evidence into Markdown profile records with YAML frontmatter, stable record IDs, claim-level evidence IDs, and an index rebuilt from frontmatter for each run.
- Add a GitHub Copilot in VS Code skill that accepts pasted or file-based job descriptions, retrieves profile evidence on demand, and generates renderer-compatible resume YAML, a source map, and a fit report.
- Use deterministic Python tooling for profile index generation, YAML/schema and source-ID validation, collision-safe outputs, rendering, and PDF text/page checks.
- Keep each application's YAML, source map, fit report, HTML, and PDF in an isolated generated draft directory; never overwrite source profile records or root `resume.yaml`.
- Produce an ATS-oriented single-column, text-based resume and verify the actual PDF is exactly one page. Allow up to three content-trimming retries after the initial render, then report failure without treating the draft as successful.
- Preserve failed draft artifacts for diagnosis, require human review, and document that profile records and the supplied job description are sent as context to the user's configured Copilot model; do not retain the full job description in generated artifacts.

## Capabilities

### New Capabilities
- `profile-based-resume-tailoring`: Maintain indexed, traceable career evidence and generate safe, job-specific, ATS-oriented one-page resume drafts.

### Modified Capabilities

## Impact

- `ResumeBuilder.py`, renderer CLI behavior, PDF validation, and tests, while preserving existing YAML rendering by default.
- New profile records/index guidance, a repository-local Copilot skill, deterministic helper tooling, and generated per-application artifacts.
- README documentation for profile maintenance, privacy, generation, validation, and review.
