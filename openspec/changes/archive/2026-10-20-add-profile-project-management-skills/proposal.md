## Why

The canonical career profile already supports structured Markdown records and stable evidence IDs, but users currently have no guided workflow for incorporating new resume information or maintaining project records. Two focused skills will make profile updates repeatable while protecting existing evidence from accidental replacement or unsupported consolidation.

## What Changes

- Add a profile-maintenance skill that accepts user-provided facts and resumes readable by the active Copilot environment, matches them to existing profile records, and proposes consolidated changes.
- Add a project-updates skill that refines existing project records or proposes new records using profile evidence and, when explicitly selected, read-only project-repository evidence.
- Require source disclosure/confirmation, a validated whole-batch preview, and explicit user approval before either skill writes canonical profile records.
- Preserve IDs when factual meaning is unchanged; use new IDs for changed claims, identify conflicts, and request resolution rather than guessing.
- Exclude resumes identified as generated or job-specific; do not retain source documents in the repository.
- Add validated source notes for new or materially changed claims, extend profile validation to check note references, and rebuild the generated index after approved changes.

## Capabilities

### New Capabilities
- `profile-maintenance`: Review full resumes or user-provided facts and safely propose consolidated updates to canonical career profile records.
- `project-updates`: Refine or add project records with traceable claims, metadata, and user-approved changes.

### Modified Capabilities

## Impact

- Adds two GitHub Copilot skills under `.github/skills/`.
- Uses the existing `profile/` records with a keyed Source notes body convention and `resume_tools.py`; extends profile validation while preserving the generated index workflow.
- Does not change the resume-tailoring workflow or renderer contract.
