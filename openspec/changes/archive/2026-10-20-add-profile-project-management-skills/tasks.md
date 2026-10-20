## 1. Profile Maintenance Skill

- [x] 1.1 Add a Copilot skill for updating the canonical profile from user-provided facts and resumes readable by the active Copilot environment.
- [x] 1.2 Specify source disclosure/confirmation, unreadable-source fallback, exclusion of identified job-specific resumes, and no source-document copies.
- [x] 1.3 Specify record matching/consolidation, omission preservation, factual ID lifecycle, explicit deletion, and conflict/ambiguity clarification.
- [x] 1.4 Require a validated whole-batch diff, explicit approval, stale-file recheck, and no writes when the user declines.
- [x] 1.5 Stage, validate, and index a candidate before preview; promote approved changes with backups/rollback and explicit partial-failure reporting.

## 2. Project Updates Skill

- [x] 2.1 Add a Copilot skill for refining or adding project records using the current Markdown/frontmatter format and canonical profile guide.
- [x] 2.2 Support read-only inspection only of explicitly selected project repositories/paths; report checkout/dirty state and do not execute code or write to project sources.
- [x] 2.3 Limit repository evidence to implementation details; require confirmation for personal attribution, impact, production, adoption, and metrics.
- [x] 2.4 Require supported claims, unique stable IDs, validated source notes, and clarification for ambiguous targets or conflicting facts.
- [x] 2.5 Use the same validated preview, approval, stale-file, staging, and rollback contract as profile maintenance.

## 3. Documentation and Verification

- [x] 3.1 Extend `resume_tools.py validate-profile` to validate keyed `## Source notes` lines and reject malformed, duplicate, or orphan evidence references.
- [x] 3.2 Implement staged candidate validation/index generation and promotion with backups/rollback; report rollback failures and affected paths.
- [x] 3.3 Update `profile/README.md` as the canonical editing contract, including source-note syntax, provenance scope, privacy, and repository-evidence boundaries.
- [x] 3.4 Ensure both skills read the canonical guide before editing and keep their self-contained safety summaries consistent with it.
- [x] 3.5 Add focused tests for source-note validation, staged validation/index behavior, and rollback/error cases.
- [x] 3.6 Run profile validation and OpenSpec change validation; confirm existing tailoring behavior and canonical profile data are unchanged.
