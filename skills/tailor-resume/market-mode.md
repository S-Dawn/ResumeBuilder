# Market mode

Use when no job description is supplied and you want a market-oriented, one-page resume (~900 words) curated for current MNC hiring trends.

## Steps

### 1. Infer and confirm the target role

Infer a candidate target role from the profile's current title, domains, skills, and experience evidence. Present the inferred role to the user for confirmation; the user may confirm, provide a corrected role, or exit. Do not curate or render until the role is confirmed.

### 2. Research MNC hiring trends

Invoke web search per skill call to gather current MNC expectations, required skills, and hiring trends for the confirmed role. Use queries such as:

- `"<role> resume skills MNC 2026"`
- `"<role> hiring expectations top companies 2026"`
- `"<role> ATS keywords 2026"`

### 3. Curate evidence aligned to trends

Select profile evidence that matches in-demand skills and expectations for the confirmed role, favoring concrete outcomes and transferable skills.

Apply the same word-limit constraint as tailored mode:

- ~900 words measured from extractable PDF text
- Strict one-page fit
- Up to eight sequential render attempts

Do not add filler, duplicate claims, or unsupported facts. Trend alignment affects evidence selection and ordering only; do not invent or alter factual claims such as metrics, dates, tools, responsibilities, or outcomes.

### 4. Web search unavailable

If web search fails, prompt the user to proceed with the LLM knowledge base or exit the operation. Never silently fail or fabricate trend data.

### 5. Generate `market-report.md`

Create `market-report.md` with these sections:

```markdown
# Market resume report

## Role
- <confirmed role>

## Trend Sources
- <title>: <URL>

## Omitted Evidence
- <evidence-id>: <rationale for omission>

## Conflicting Claims
- Conflicting claims — evidence: `evidence-id-1`, `evidence-id-2`
```

Or `- None identified` when a section has no entries.

### 6. Create the draft

For a market resume, use the stable label `market-resume` and select market mode:

```sh
uvx resumebuilder-tools@1.0.0 create-draft --application market-resume --type market
```

Write `resume.yaml`, `source-map.json`, and `market-report.md` in the returned directory. Do not write the job description there.

### 7. Validate, render, and fit

See [rendering.md](rendering.md) for the render command and validation rules. Market drafts reuse the tailored pipeline:

- Strict one-page check
- ~900-word soft target
- Up to eight sequential render attempts
- `market-report.md` instead of a fit report

If the eighth market render still fails, retain all draft artifacts, explain the validation failure, and do not present the draft as ready to submit.
