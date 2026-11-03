# Master mode

Use when no job description is supplied and you want a complete, multi-page archive of all profile evidence with no word-count target or page limit.

## Steps

### 1. Read all profile records

Read every indexed profile record and all of its evidence claims. Do not filter the records by job relevance.

### 2. Include all supported details

Include all supported details from every profile record, not only the details currently used in `resume.yaml`. Preserve all distinct evidence claims, skills, employment and project history, education, certifications, and achievements.

Combine only genuinely duplicate facts; do not drop relevant-looking or lower-priority content to shorten the document.

The master resume has no word-count target or page limit. Broad rewriting and reordering are allowed, but do not invent or alter facts such as metrics, dates, tools, responsibilities, or outcomes.

### 3. Generate `master-report.md`

Create `master-report.md` with this structure:

```markdown
# Master resume report

## Conflicting evidence excluded
- None identified
```

If conflicting claims are excluded, replace `None identified` with one or more entries such as:

```markdown
- Conflicting claims — evidence: `evidence-id-1`, `evidence-id-2`
```

and note the conflict for user clarification.

### 4. Create the draft

For a master resume, use the stable label `master-resume` and select master mode:

```sh
uvx resumebuilder-tools@1.0.0 create-draft --application master-resume --type master
```

Write `resume.yaml`, `source-map.json`, and `master-report.md` in the returned directory.

### 5. Validate, render, and fit

See [rendering.md](rendering.md) for the render command and validation rules. Master drafts:

- May span multiple pages (no strict one-page check)
- No word-count target; do not use word count to add, remove, or condense content
- Validate extractable text, conventional section headings/order, and single-column structure

Render once and verify the PDF is readable and has extractable text.
