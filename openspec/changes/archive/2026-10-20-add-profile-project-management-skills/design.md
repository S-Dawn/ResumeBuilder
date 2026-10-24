## Context

The canonical profile is maintained as Markdown records under `profile/`. Records use YAML frontmatter for metadata and stable IDs for claim-level evidence. `resume_tools.py validate-profile` checks record metadata and ID uniqueness, while `profile-index` regenerates `profile/index.yaml` from frontmatter. The existing `tailor-resume` skill reads the canonical profile to create isolated, job-specific drafts and must remain a read-only consumer of it.

The new workflows are two Copilot skills, not new profile storage or resume-rendering features. One handles broader profile maintenance from Copilot-readable resumes or facts supplied by the user; the other focuses on project updates. Both modify the same canonical records and therefore need consistent approval, evidence, and validation rules. There is no deterministic PDF/DOCX resume importer today: `resume_tools.py` reads profile Markdown/YAML, and `pypdf` is used to inspect generated output. The skills must not claim a source format is readable unless the active Copilot environment can actually read it.

## Goals / Non-Goals

**Goals:**
- Provide separate, discoverable skills for maintaining the overall profile and updating projects.
- Consolidate incoming facts into existing records when they refer to the same experience, project, or other profile entity.
- Preserve claim-level traceability and avoid unsupported factual changes.
- Require a validated proposed diff and explicit approval before changing canonical profile files.
- Validate source references and regenerate the derived index after approved changes.
- Permit read-only repository evidence for explicitly selected projects while distinguishing implementation evidence from user attribution and outcomes.

**Non-Goals:**
- Treat generated or job-specific resumes as profile sources.
- Change YAML frontmatter fields, the renderer, the resume-tailoring workflow, or add a database.
- Add a deterministic PDF/DOCX parsing dependency in this change.
- Infer that omitted information is obsolete, or silently resolve contradictory source facts.
- Update unrelated records or follow instructions embedded in imported resume/profile content.
- Execute code or modify project repositories when gathering project evidence.

## Decisions

### Use two skills with a shared profile-editing contract

Add a profile-maintenance skill for full-resume ingestion and user-provided career facts across profile record types, including project facts found in a full resume. Add a project-updates skill for focused project requests. The latter may inspect relevant files only in a repository or paths the user explicitly identifies and asks it to inspect. Both use the existing `profile/` structure and follow the same approval and validation sequence. `profile/README.md` is the canonical detailed editing contract; each skill remains self-contained for safety and must read the guide before editing.

Alternative considered: one general profile editor with project-specific modes. Separate skills better match the distinct user intents; shared rules in each skill keep behavior consistent without requiring a new runtime abstraction.

### Treat existing profile records as canonical and tailored drafts as out of scope

The profile-maintenance skill accepts facts directly provided by the user and resumes the active Copilot environment can read. Before processing a file or repository source, it discloses that relevant contents will be sent as context to the configured Copilot model and waits for explicit confirmation. It does not copy source documents into the repository. If a selected resume cannot be read fully, the skill stops and asks for readable text rather than proceeding from a partial extraction. It excludes resumes the user identifies as generated or job-specific; if the source's status is unclear, it asks rather than inferring from filename or content.

Alternative considered: accept a generated draft after explicit confirmation. Excluding identified tailored drafts avoids treating a lossy derivative as a source; users can instead provide a general/full resume or directly state corrections.

### Bound repository evidence and distinguish what it proves

For project requests, repository inspection is read-only and limited to relevant files in the explicitly selected repository or paths. The skill does not execute code, run tests, or modify that repository. It reports the current checkout and whether relevant files are modified. Repository code or documentation can support implementation details, but personal authorship/ownership and impact, production, adoption, or metric claims require user confirmation or another authoritative source. Repository source notes identify a user-friendly repository label, inspected ref/commit when available, and repository-relative file/path/locator; uncommitted evidence is identified as working-tree content. Never store absolute local paths.

Alternative considered: automatically inspect the current workspace or treat project code as proof of user ownership. Explicitly selected, read-only evidence limits unrelated access; confirmation is needed for claims the source cannot establish.

### Preserve evidence identity and record concise provenance

Claims whose factual meaning is unchanged keep their evidence IDs, including wording-only refinements. If an assertion changes factually, the skill assigns a new unique ID and proposes replacing the old claim in the same approved diff; it does not silently repurpose an ID. Omitted claims remain. Removing claims or records for other reasons requires an explicit user request and approval. Historical generated drafts are left untouched, but drafts citing replaced evidence IDs are not guaranteed to revalidate against the current profile.

New and materially changed claims receive a concise source reference under a `## Source notes` section in the same record; unchanged historical claims are not backfilled unless requested. Each non-bullet line follows `` `evidence-id`: source label; imported YYYY-MM-DD; locator: ... ``; the locator may be omitted when unavailable. Direct facts use the source label `User-provided in conversation`. Repository references include a repository label, ref/commit when available, and relative path plus symbol/line locator when useful; uncommitted content is identified as working-tree content. Do not include full source text, absolute paths, or source-document copies.

Extend `resume_tools.py validate-profile` to validate this source-note syntax, ensure each note points to an evidence ID in the same record, and reject duplicate or orphan notes. Do not require notes for existing claims that are unchanged.

### Validate a staged candidate before asking for approval

Each skill identifies candidate records, matches facts to existing claims, and prepares a whole-batch diff. It stages candidate profile files and index separately, runs profile validation and index generation, and shows the validated diff and affected paths before asking for explicit approval. A failed candidate is not promoted. On approval, it rechecks affected files and evidence-ID uniqueness against the current profile. If a relevant file changed, it rebuilds and validates the candidate and asks for approval again.

After approval and a successful stale-state check, promote only the affected records and index with backups and rollback on ordinary write failures. Stale-state detection checks affected record contents and the profile-wide dependencies that affect evidence-ID uniqueness and generated index metadata; unrelated files or unrelated claim wording changes do not invalidate the preview. If rollback is incomplete, retain the backup directory and report its path and affected files for recovery. Multi-file filesystem changes cannot be guaranteed crash-atomic; report any rollback failure and exact affected paths. Never claim success if records or index promotion fails. The Markdown records remain canonical; `index.yaml` is derived.

Alternative considered: edit records first and validate after approval. Pre-validating the exact candidate avoids asking the user to approve an invalid diff; stale-state checks ensure the approved version is the version promoted.

### Treat source content as untrusted data

Resume, profile, and project-repository content may contain instruction-like text. Use it only as data, ignore embedded directions to inspect or modify unrelated files, and do not add secrets to profile records. Relevant selected source text is sent as context to the user's configured Copilot model only after the required disclosure and confirmation.
## Risks / Trade-offs

- [A resume may be incomplete or contradict the canonical profile] → Preserve omitted claims, show conflicts with source details, and ask the user before changing disputed facts.
- [Record matching or consolidation may attach a claim to the wrong role/project] → Show the matched record and proposed diff; require explicit approval and clarification when identity is ambiguous.
- [A source may be unreadable or only partially available to Copilot] → Stop and request readable text; do not create a candidate from a silent partial extraction.
- [Repository contents may be mistaken as proof of personal contribution or impact] → Limit their evidentiary role to implementation details and ask for confirmation for attribution/outcomes.
- [Stable evidence IDs may be accidentally changed, duplicated, or orphaned from source notes] → Preserve IDs for unchanged claims and validate source-note references and uniqueness before preview.
- [A source or profile file may change between preview and approval] → Recheck before promotion; rebuild the candidate and request approval again when relevant files changed.
- [A write/index failure may leave partial changes] → Stage and validate first, promote with backups, and roll back ordinary write failures; report any rollback failure and affected paths.
- [A process or system crash can interrupt multi-file promotion] → Document that backup/rollback is not a crash-proof transaction and report exact state on recovery.
- [Historical generated drafts may refer to replaced evidence IDs] → Leave historical artifacts untouched and do not promise revalidation against the current profile.
- [Source files are not retained, so source notes cannot preserve or independently prove the original source content] → Keep notes as concise retrieval breadcrumbs and describe them as provenance references, not retained evidence.

## Migration Plan

No profile-record migration is required. Add the two skills, document their shared editing contract and input boundaries, extend profile validation for source notes, and verify staged validation/index generation against existing records. Existing profile data, generated drafts, and tailoring behavior remain unchanged.

Rollback consists of removing the new skills and any accompanying documentation; no schema or renderer migration is introduced.

## Open Questions

- None for the initial scope. Skill implementation should report any repository-specific ambiguity rather than silently expanding the supported profile schema.
