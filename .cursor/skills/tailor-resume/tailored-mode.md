# Tailored mode

Use when a job description is supplied (pasted or via file path).

## Steps

### 1. Create a fit report

Create a concise fit report that maps major job requirements to evidence IDs and identifies unsupported or weakly supported requirements. Do not paste the complete job description into the report.

Use these required sections and entry formats:

```markdown
# Fit report

## Evidence-backed matches
- Backend APIs — evidence: `optum-backend-services`, `provider-search-nlp`
- None identified

## Unsupported or weakly supported requirements
- Distributed tracing — weakly supported; evidence: `provider-search-tracing`
- Formal SRE ownership — unsupported
- None identified
```

Use `None identified` only when that section has no entries. Every evidence ID must exist in the profile.

### 2. Generate `resume.yaml`

Generate a complete `resume.yaml` using only the renderer's supported fields and the selected evidence. Build a ranked pool of relevant evidence before writing:

- First pass: direct matches to core job requirements and the strongest role-aligned achievements.
- Next passes: moderately related evidence with impactful contributions, concrete outcomes, scale, or transferable skills.
- Final pass: other complementary evidence only when it adds distinct value and there is room.

Begin with the strongest evidence, then use word-count-guided revisions to consider the next most valuable omitted items rather than treating the first selection as final. Favor concrete outcomes and meaningful contributions over redundant keyword lists.

Aim for 900 words in the rendered resume, but never add filler, duplicate claims, or unsupported facts just to reach the target.

### 3. Generate `source-map.json`

See [rendering.md](rendering.md).

### 4. Create the draft

For a tailored draft:

```sh
poetry run python resume_tools.py create-draft --application <company-role-slug>
```

Write `resume.yaml`, `source-map.json`, and `fit-report.md` in the returned directory. Do not write the job description there.

### 5. Validate, render, and fit

See [rendering.md](rendering.md). Tailored drafts:

- Strict one-page check
- ~900-word soft target
- Up to eight sequential render attempts

If the eighth tailored render still fails, retain all draft artifacts, explain the validation failure, and do not present the draft as ready to submit.
