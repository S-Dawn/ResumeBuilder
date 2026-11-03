# Rendering and validation (all modes)

Shared steps for generating source maps, rendering, and validating drafts in any mode.

## Generate `source-map.json`

Create `source-map.json` with this exact structure:

```json
{
  "items": [
    {
      "path": "experience.0.highlights.0",
      "source_evidence_ids": ["optum-backend-services"]
    }
  ]
}
```

Include one entry for every non-empty string value in `resume.yaml`; paths use dot-separated mapping keys and zero-based list indexes.

## Create an isolated output directory

For a tailored draft:

```sh
uvx resumebuilder-tools@1.0.1 create-draft --application <company-role-slug>
```

For a master resume:

```sh
uvx resumebuilder-tools@1.0.1 create-draft --application master-resume --type master
```

For a market resume:

```sh
uvx resumebuilder-tools@1.0.1 create-draft --application market-resume --type market
```

If a directory already exists, ask whether to create a numbered draft, explicitly replace it, or cancel. Use `--collision new` only after the user chooses a numbered draft and `--collision replace` only after explicit replacement authorization. If interaction is unavailable, cancel; never silently overwrite.

## Render

Invoke the helper for the initial render:

```sh
uvx resumebuilder-tools@1.0.1 render --draft-dir <draft-directory> --attempt 1
```

The render command accepts only a direct child of the configured `generated_dir` (default: `generated/`); the engine applies this path automatically from `resumebuilder-skills.config.json`.

## Word count

The render helper records the number of words extracted from the actual PDF in `status.json` as `word_count`, including contact details and section headings. Use this measure instead of screenshots or visual page inspection to assess content fullness.

## Mode-specific validation rules

| Rule | Tailored | Master | Market |
|------|----------|--------|--------|
| One-page check | Strict (exactly 1 page) | Not enforced | Strict (exactly 1 page) |
| Word target | ~900 words (soft) | None | ~900 words (soft) |
| Render attempts | Up to 8 | 1 | Up to 8 |
| Report | `fit-report.md` | `master-report.md` | `market-report.md` |

The helper writes `status.json`. A successful result must report `validated`; a failed result must remain clearly marked `failed`. If the helper fails or is unavailable, report the failure and never claim validation succeeded.

## Content revision guidance (tailored and market only)

When below the word target, add the strongest omitted evidence from the next relevance tier, prioritizing impactful contributions and outcomes; update the matching source map and report. If the PDF exceeds one page, remove the lowest marginal-value evidence first, then condense the summary, skills, and other optional content. Re-render after each change with the next sequential attempt.

Continue through relevance tiers until the resume is near 900 words, no distinct supported evidence would improve role fit, the next addition would exceed one page or reduce readability, or the retry budget is exhausted. Stop early when another iteration would not materially improve the resume.

The 900-word target is a soft fullness measure, not a reason to pad; some evidence-based resumes may remain below it. Never add filler.

## Preserved content (all modes)

Preserve contact details and employment role/company/date chronology. Do not silently shrink typography. Omit empty section headings.
