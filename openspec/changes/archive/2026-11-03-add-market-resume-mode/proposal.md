## Why

Users who want a resume without a job description currently get only a "master" mode: an unfiltered, multi-page archive of all profile evidence with no word or page limit. That is useful as a complete career record, but it is not optimized for market desirability. There is no mode that infers the user's target role from their profile, researches current MNC hiring trends for that role, and curates the evidence into a tight, ATS-oriented one-page resume (~900 words) that makes the user desirable in today's market. This change adds that mode without altering the existing master or tailored workflows.

## What Changes

- Add a new `market` draft mode alongside `tailored` and `master` in the tailor-resume skill and `resume_tools.py`.
- In market mode, infer the target role from the canonical profile and present it to the user for confirmation before curating.
- When a role is confirmed, invoke web search per skill call to gather current MNC expectations, required skills, and hiring trends for that role.
- Curate profile evidence aligned to those market trends, applying the same word-limit constraint as tailored mode: ~900 words measured from extractable PDF text, strict one-page fit, and up to eight sequential render attempts.
- Keep master mode unchanged: all evidence, multi-page, no word-count target or page limit.
- Keep tailored mode unchanged: job-description-driven, one page, ~900-word target.
- Add a `market-report.md` artifact documenting the inferred role, trend sources used, omitted-evidence rationale, and any conflicting claims excluded.
- If web search is unavailable, prompt the user to proceed with the LLM knowledge base or exit the operation; never silently fail or fabricate trend data.

## Capabilities

### New Capabilities

- `market-resume-mode`: A curated market-oriented resume mode that infers role from the profile, researches current MNC trends via web search, and renders a one-page ~900-word resume optimized for market desirability. Creates `specs/market-resume-mode/spec.md`.

### Modified Capabilities

- (none) — master and tailored mode requirements are intentionally unchanged.

## Impact

- `.opencode/skills/tailor-resume/SKILL.md` (and mirrors under `.cursor/skills/` and `.github/skills/`): add market-mode steps.
- `openspec/specs/profile-based-resume-tailoring/spec.md`: add market-mode requirement scenarios (no change to master/tailored requirements).
- `resume_tools.py`: support `--type market` in `create-draft` and `render`; reuse existing one-page validation and word-count measurement.
- `README.md`: document the new market mode option.
- Tests: add coverage for market mode (role inference confirmation, word-limit enforcement, web-search-unavailable prompt).
