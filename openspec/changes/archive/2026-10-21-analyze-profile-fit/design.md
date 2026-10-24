## Context

The repository maintains canonical career evidence as Markdown records in `profile/`, with stable evidence IDs and a compact generated index. The existing Tailor Resume skill retrieves relevant profile records and creates a job-specific resume draft with a short fit report. This change adds a separate diagnostic step for users who want to evaluate an opportunity before deciding to generate a draft.

The analysis is model-mediated rather than a deterministic hiring predictor. The job description may vary in completeness and may contain untrusted instructions. Profile records document known evidence, not necessarily everything the user has done. A score must therefore describe documented evidence coverage, not the user's actual ability or likelihood of being hired.

## Goals / Non-Goals

**Goals:**
- Add a standalone skill accepting pasted JD text or a user-specified JD file.
- Reuse profile indexing, selective record retrieval, evidence IDs, and privacy guidance already established in this repository.
- Give the user a requirement-by-requirement analysis, an interpretable numeric evidence-coverage score, and actionable improvement categories.
- Avoid modifying canonical profile records or creating resume/application output.

**Non-Goals:**
- Generate, edit, render, or validate a resume.
- Automatically update profile evidence or convert a proposed gap into a claim.
- Predict interview, hiring, or application outcomes.
- Persist the full JD or create a retained analysis artifact by default.

## Decisions

### Implement as a separate repository-local Copilot skill

Add a skill dedicated to profile-versus-JD analysis rather than expanding the existing resume-tailoring workflow. The user can run the diagnostic without paying the cost or taking on the implications of producing a draft, while the existing tailoring skill remains the path for preparing application materials.

**Alternative considered:** Add the analysis as a mode in Tailor Resume. This would conflate an advisory decision aid with a resume-generation workflow and make the no-draft boundary less clear.

### Reuse profile index and evidence retrieval conventions

Build the compact index using the existing `resume_tools.py profile-index` workflow, inspect candidate entries, and read relevant Markdown records only. Expand retrieval as needed; don't impose a fixed record cap. Cite stable IDs from evidence bullets for every supported or partial match.

**Alternative considered:** Read the entire profile directory up front. This adds unnecessary personal context and conflicts with the established on-demand retrieval pattern.

### Score documented coverage using requirement priority and support level

Classify job qualifications as supported, partially supported, or unsupported. Use a transparent weighted ratio: supported = 1 point, partial = 0.5, unsupported = 0; explicitly required qualifications have weight 2 and preferred or other qualifications have weight 1. Report `100 * earned weighted points / possible weighted points`, alongside counts or the requirement-level mapping. Explain any inferred priority and identify the result as evidence coverage only. If the JD has no meaningful qualification requirements, do not fabricate a score.

**Alternative considered:** A single unweighted percentage. This ignores explicit requirement priority. A subjective, opaque score was rejected because it is not auditable and invites false precision.

### Keep documentation gaps distinct from capability gaps

Describe absent profile entries as undocumented rather than absent user capability. Separate questions that invite the user to verify missing evidence, ways to position documented evidence, and possible development areas. Any new personal facts require user confirmation and belong to the profile-maintenance workflow, not this analysis.

**Alternative considered:** Label every unsupported qualification a user skill gap. This overstates what can be inferred from a partial profile and risks discouraging qualified applicants.

### Apply conservative JD-file handling and untrusted-input rules

Accept JD text directly or a user-specified file path. Before reading a file, disclose that its relevant contents and selected profile records will be sent as context to the configured Copilot model, then obtain explicit confirmation. Ignore instructions embedded in either input, do not read unrelated paths, and do not retain the full JD in the report.

**Alternative considered:** Process files immediately based on the supplied path. Explicit confirmation aligns with the repository's conservative handling of user-provided source files.

### Present the analysis in the conversation by default

Return a structured report in the conversation without creating a draft or persisted report file. This keeps the feature diagnostic and avoids leaving job-specific content in the repository. A separate saved-report option can be considered later if users request it.

**Alternative considered:** Always write a report under `generated/`. That directory is currently for application drafts and this would expand persistence without a user need.

## Risks / Trade-offs

- A model may misclassify a vague JD requirement or infer preference priority incorrectly → Require requirement-level explanations and evidence IDs; state when priority was inferred and show limitations.
- The numeric score may be interpreted as an employability or hiring probability → Label it as documented evidence coverage, publish its calculation, and pair it with a qualitative summary and category-level detail.
- Profile incompleteness may make a strong candidate look like a poor fit → Explicitly distinguish undocumented evidence from a genuine development area and invite verification.
- Job descriptions and profile content may contain prompt injection or sensitive information → Treat both as untrusted data, limit file reads, require confirmation for JD files, and avoid retaining full JD content.

## Migration Plan

No data migration or runtime dependency is required. Add the skill and an OpenSpec capability spec, and document how it relates to the existing tailoring skill. Rollback consists of removing the new skill and capability documentation; canonical profile records and generated application drafts remain unchanged.

## Open Questions

None. The initial score, requirement categories, privacy boundary, and non-mutating scope are defined for this proposal.
