---
name: tailor-resume
description: Create a job-tailored resume from a job description or a complete master resume when no job description is supplied, preserving source traceability and requiring human review.
disable-model-invocation: true
compatibility: Requires Python and uv/uvx to invoke the resumebuilder-tools engine package from PyPI.
---

# Tailor a resume

Create either a focused application draft, a consolidated master resume, or a market-oriented resume from the canonical profile in `profile/`.
Never modify the profile or repository-root `resume.yaml`.

## Modes

The skill supports three draft modes:

| Mode | When to use | Output |
|------|-------------|--------|
| **Tailored** | A job description is supplied | One-page, ~900-word, job-specific draft with fit report |
| **Master** | No job description; complete career archive | Multi-page, all evidence, no word/page limit |
| **Market** | No job description; market-oriented curation | One-page, ~900-word, trend-curated draft with market report |

Choose the mode that matches your goal:

- **Tailored**: See [tailored-mode.md](tailored-mode.md)
- **Master**: See [master-mode.md](master-mode.md)
- **Market**: See [market-mode.md](market-mode.md)

## Build context on demand (all modes)

1. Run `uvx resumebuilder-tools@1.0.0 profile-index` and read only `profile/index.yaml`.
2. Use record summaries, metadata, tags, aliases, and the job description (if any) to identify candidate records.
3. Read only the candidate Markdown records. Expand the set when needed to establish accurate dates, responsibilities, or evidence; do not impose an arbitrary record-count cap.
4. Use stable evidence IDs from the record bullets in every source mapping. If relevant source claims conflict, omit the disputed claim and report the conflicting IDs for user clarification.

## Trust boundaries (all modes)

See [trust-boundaries.md](trust-boundaries.md).

## Source map and rendering (all modes)

See [rendering.md](rendering.md).

## Human review (all modes)

Present the mode-appropriate report (fit report for tailored, market report for market, master report for master), source map, HTML, and PDF for human review.

- In master mode, summarize the profile coverage and flag any conflicting claims.
- In market mode, summarize the confirmed role, trend sources, omitted-evidence rationale, and conflicting claims.
- Explain unsupported job requirements and material trade-offs for tailored drafts.

A validated draft is not approved for submission; never submit it externally.
