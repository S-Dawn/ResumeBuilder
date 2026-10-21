## Why

The existing resume-tailoring workflow reports matches and gaps only while generating an application draft. Users need a separate way to assess whether their canonical profile supports an application, understand evidence-backed strengths and gaps, and identify practical improvements before deciding whether to tailor a resume.

## What Changes

- Add a standalone GitHub Copilot skill that compares the canonical career profile with a pasted or file-based job description without generating or modifying a resume or profile.
- Produce an evidence-traceable fit analysis covering supported, partially supported, and unsupported requirements, with an explained numeric fit score and qualitative interpretation.
- Identify profile evidence the user may be able to verify, positioning opportunities based on existing evidence, and genuine skill-development areas without inventing qualifications.
- Preserve privacy and trust boundaries: treat profile and job-description content as untrusted data, avoid retaining the full job description, and cite profile evidence IDs.

## Capabilities

### New Capabilities
- `profile-fit-analysis`: Analyze the canonical profile against a job description and report evidence-backed fit, gaps, and improvement opportunities without creating an application draft.

### Modified Capabilities

## Impact

- New repository-local Copilot skill under `.github/skills/`.
- New OpenSpec capability specification and documentation of the workflow and report contract.
- Uses the existing `profile/` records, generated index workflow, and conventions established by the Tailor Resume skill; no new runtime dependencies or changes to resume rendering are expected.
