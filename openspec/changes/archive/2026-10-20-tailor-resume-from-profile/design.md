## Context

The project is a Python CLI that reads YAML and renders HTML/PDF with WeasyPrint. `--config` already allows a tailored YAML input, but root `resume.yaml` currently contains the career evidence and the presentation for one resume. The renderer uses `highlights` for experience and project bullets; the README example uses `bullets`, so generated data and documentation must match the actual renderer contract.

The current renderer emits headings even for empty sections, has no PDF page-count or extracted-text validation, and the repository has no rendering tests. The repository's Copilot customization convention is `.github/skills/<name>/SKILL.md`, but it does not define a specific runtime tool contract for invoking the helper. The design therefore keeps generation checks in a documented deterministic Python CLI that the skill invokes and reports honestly if execution is unavailable or fails.

## Goals / Non-Goals

**Goals:**
- Migrate all existing identity, summary, skills, work history, projects, education, certifications, and achievements from `resume.yaml` into a maintainable, searchable evidence profile.
- Retrieve profile details on demand and produce role-focused, factual, traceable resume drafts from pasted or file-based job descriptions.
- Validate generated YAML and provenance, safely preserve prior drafts, and render/check output deterministically.
- Verify one-page PDF output and measurable ATS-oriented structure, with bounded content trimming and visible failure.
- Preserve existing YAML rendering by default and require a human to review each draft.

**Non-Goals:**
- Supporting agent runtimes other than GitHub Copilot in VS Code.
- Adding hosted services, persistent databases, embeddings, or vector search.
- Automatically submitting an application, claiming universal ATS compatibility, or approving a draft without human review.
- Retaining the full job description in generated artifacts or replacing the existing YAML input workflow.

## Decisions

### Use Markdown records with minimal frontmatter and claim-level IDs

Maintain the canonical profile as Markdown records. Each record has required `id`, `type`, `title`, and short `summary` frontmatter; optional metadata can include employer, role, dates, skills, domains, tags, and aliases. Keep role/project context in the record and give each individual evidence claim a stable ID in the Markdown body, with a factual statement and optional action, impact, verified metric, technologies, and tags. Do not require every claim to use a rigid STAR template.

Migrate all evidence currently in `resume.yaml`, preserving its detail. Stable IDs on both records and claims enable fine-grained retrieval and provenance. Flexible optional metadata avoids a rigid taxonomy while ensuring a minimum amount of searchable context.

### Rebuild a compact index and retrieve adaptively

At the start of each run, deterministic Python tooling derives a compact index from profile frontmatter, validating required fields and duplicate IDs without loading full Markdown bodies into the model context. The Copilot skill uses the index to open relevant records, then expands retrieval when necessary for a coherent and factually complete resume. Do not impose a fixed maximum number of records that could hide relevant evidence. Report selected source record/evidence IDs in generated artifacts.

Support a job description pasted into the skill invocation or supplied as a file. Ask for company, role, or application-label metadata when it cannot be identified reliably; do not guess. Treat the JD and profile text as untrusted data, never as instructions to the agent or authorization to read/change unrelated files.

### Keep AI judgment and deterministic operations separate

The GitHub Copilot skill interprets the job description, selects evidence, and rewrites/reorders claims. It may use broad phrasing changes, but must not invent or alter factual claims, including dates, metrics, technologies, responsibilities, or outcomes. If source records conflict, exclude the disputed claim from the resume and flag the conflict with source IDs for user review.

The skill invokes deterministic Python tooling to rebuild/validate the index, validate generated YAML against the renderer contract, validate source-ID references, handle application output directories, render HTML/PDF, and verify PDF properties. If terminal/tool execution is unavailable or fails, the skill reports that limitation and must not claim a validated output. Avoid an external LLM API inside the renderer.

### Retain isolated application drafts and ask on collisions

Each application draft directory under `generated/` contains the tailored `resume.yaml`, a source-mapping manifest, `fit-report.md`, rendered HTML, and PDF. The source map associates each tailored content item with one or more profile evidence IDs. The fit report maps major JD requirements to supporting evidence and identifies unsupported or weakly supported requirements without reproducing the full JD.

Require the fit report to contain `Evidence-backed matches` and `Unsupported or weakly supported requirements` sections. Each matched item cites one or more known evidence IDs; unsupported/weak entries are explicitly labeled, and weak entries may cite evidence IDs.

Never overwrite the canonical profile or root `resume.yaml`. On an existing application path, ask whether to create a numbered draft, explicitly replace the existing draft, or cancel. If interaction is unavailable, cancel without writing over existing files. The render helper accepts only a direct child of the configured generated-output root, rejecting arbitrary paths and symlinks. Retain generated artifacts when validation or page-fit fails, mark/report the draft as failed, and never present it as ready to submit. Do not include the full JD in retained artifacts by default.

### Validate the YAML contract before rendering

The helper validates the tailored YAML's root mapping, required resume sections, field names, and value types against the schema actually consumed by the renderer. It also rejects source-map references to unknown profile evidence IDs. Invalid input produces an actionable error instead of relying on permissive renderer defaults. Keep the legacy default `--config resume.yaml` flow unchanged unless strict validation is explicitly requested by the tailored workflow.

### Enforce one page through measured, staged retries

The tailored workflow enables strict page validation and checks the actual rendered PDF, not estimated text length or HTML dimensions. Use a maintained PDF library for deterministic page counting and selectable-text extraction; keep page checking testable independently. The initial render plus at most three retries is allowed.

For retries, progressively reduce the lowest-relevance evidence bullets/projects first, then condense the summary, skills, and other optional content. Do not remove contact details or employment role/company/date chronology. Omit a section heading and wrapper if its content becomes empty. If protected content still exceeds one page after three retries, retain the artifacts, mark the run failed, and explain the page-count result; do not silently shrink typography or claim success.

### Define ATS-oriented checks without claiming universal compatibility

Keep a text-based, single-column layout with conventional section headings and stable document reading order. Deterministic checks verify that the actual PDF text positions do not show repeated left/right column flows, along with extractable/selectable PDF text, expected headings/order, and no unsupported YAML fields. HTML is also checked for unsupported multi-column constructs. These are measurable ATS-oriented safeguards, not a guarantee that every ATS vendor parses the document identically. Semantic relevance and factual fidelity are reviewed with role-distinct Copilot smoke cases and a human reviewer rather than an asserted model score.

### Document Copilot data handling

Explain that selected profile records and the provided job description are sent as context to the user's configured Copilot model. Advise users not to store secrets in profile records. The workflow does not copy the full job description into generated application artifacts.

## Risks / Trade-offs

- [Frontmatter metadata or IDs may be incomplete or duplicated] -> Validate required metadata and uniqueness on every run and provide actionable file/record diagnostics.
- [Indexing only frontmatter may miss relevant evidence] -> Keep summaries and tags useful, permit adaptive retrieval expansion, and test role-distinct cases.
- [Rewriting may distort a claim even with instructions] -> Require claim-level provenance, conflict reporting, deterministic ID validation, and human review.
- [Strict one-page output may omit relevant evidence] -> Preserve employment chronology and contact information, trim by relevance in stages, and fail visibly rather than violating the page limit.
- [PDF extraction checks cannot prove compatibility with every ATS] -> Report only the checks actually performed and avoid universal compatibility claims.
- [A repeated draft can collide with an existing output] -> Prompt for numbered draft, explicit replacement, or cancel; default to cancel without interaction.
- [Copilot context may contain personal career information] -> Document that profile/JD content is sent to the configured model and discourage secrets in profile files.
- [The new Python PDF dependency may vary in runtime support] -> Select a maintained library compatible with supported Python versions and cover it with focused page/text extraction tests.

## Migration Plan

1. Define profile record and evidence-block formats, then migrate all current `resume.yaml` evidence into records and validate the generated metadata index. Keep root `resume.yaml` unchanged for backward compatibility.
2. Add the deterministic Python helper for index generation, schema/provenance validation, collision handling, rendering, and PDF checks.
3. Add the repository-local Copilot skill, fit report/source map formats, user review instructions, and privacy guidance.
4. Add empty-section handling, strict page-count/text validation, and tests; exercise no more than three content-trimming retries.
5. Test with distinct backend and Forward Deployed Engineer descriptions, verify selection/provenance and output isolation, and have a human review semantic relevance and factual fidelity.
6. Rollback is non-destructive: stop using the skill and continue rendering from unchanged root `resume.yaml`; generated drafts can be retained or removed by the user.

## Open Questions

None. Profile migration covers all current evidence; one-page generation allows three retries after the initial render.
