## Context

The ResumeBuilder project supports two resume draft modes today: `tailored` (job-description-driven, one page, ~900-word target) and `master` (all evidence, multi-page, no limit). The canonical profile lives in `profile/` as Markdown records with YAML frontmatter and stable evidence IDs, and `resume_tools.py` provides deterministic validation, source-map checking, HTML/PDF rendering, page counting, and word-count measurement.

Users who invoke the tailor-resume skill without a job description currently get only master mode — a complete archive. That is valuable as a career record, but it is not curated for market desirability and does not apply the one-page/~900-word constraint that tailored mode enforces. There is demand for a middle ground: a curated, market-oriented resume that infers the target role, researches current MNC expectations, and produces a tight one-page resume without requiring the user to supply a job description.

## Goals / Non-Goals

**Goals:**
- Add a `market` draft mode alongside `tailored` and `master`.
- Infer the target role from the canonical profile and present it to the user for confirmation before curating.
- Research current MNC expectations, required skills, and hiring trends for the inferred role via web search (one search per skill call).
- Curate profile evidence aligned to those trends, applying the same word-limit constraint as tailored mode: ~900 words measured from extractable PDF text, strict one-page fit, up to eight sequential render attempts.
- Reuse the existing `resume_tools.py` helper (`create-draft --type market`, `render`, `validate_pdf_output`, `count_pdf_output`) without modifying master or tailored behavior.
- Produce a `market-report.md` documenting the inferred role, trend sources, omitted-evidence rationale, and excluded conflicting claims.
- If web search is unavailable, prompt the user to proceed with the LLM knowledge base or exit; never silently fail or fabricate trend data.

**Non-Goals:**
- Do not change master mode requirements (all evidence, multi-page, no word/page limit).
- Do not change tailored mode requirements (job-description-driven).
- Do not modify the canonical profile or root `resume.yaml`.
- Do not attempt to guarantee ATS compatibility with every vendor.
- Do not implement real-time job-board scraping or application submission.

## Decisions

### 1. Market mode reuses the tailored rendering pipeline instead of master
**Decision:** Market mode uses `create-draft --type market` and the same strict one-page validation as tailored mode (`PageFitError` unless exactly 1 page), rather than master's multi-page path.
**Rationale:** The proposal explicitly requires the same word-limit constraint as any other resume (~900 words, one page, max 8 attempts). Reusing the tailored pipeline avoids duplicating page-fit logic and keeps one code path for the constraint.
**Alternatives considered:** Reuse master's multi-page path (rejected — violates the word-limit requirement); build a new renderer (rejected — unnecessary duplication).

### 2. Role inference is a skill-level step with user confirmation
**Decision:** The tailor-resume skill infers a candidate role from profile metadata (title, domains, skills, experience evidence) and presents it to the user for confirmation. The user can confirm, correct, or exit.
**Rationale:** Role inference is load-bearing — an incorrect role produces misaligned market curation. The skill's existing principle is "ask rather than guess" (SKILL.md:14). Confirmation keeps the user in the loop without making inference fully manual.
**Alternatives considered:** Fully automatic inference (rejected — risk of wrong-role optimization); fully manual role entry (rejected — adds friction, duplicates information already in the profile).

### 3. Web search is per skill call, not cached across runs
**Decision:** Each market-mode invocation performs fresh web searches for current MNC expectations for the confirmed role.
**Rationale:** Hiring trends change; stale trend data could produce outdated curation. Per-call search reflects "current" market state.
**Alternatives considered:** Cache search results (rejected — staleness risk); skip search and use LLM knowledge only (rejected — fails the "invoke web search requests per skill call" requirement unless unavailable).

### 4. Web-search unavailability degrades gracefully with a user prompt
**Decision:** If web search fails, the skill prompts the user: proceed with the LLM knowledge base, or exit the operation.
**Rationale:** Prevents silent failure and prevents fabricating trend data. Gives the user agency.
**Alternatives considered:** Hard-fail the operation (rejected — poor UX when search is transiently unavailable); silently proceed without disclosure (rejected — violates trust-boundary transparency).

### 5. Market mode is a new draft type, not a modification of master or tailored
**Decision:** `market` is added as a third value alongside `tailored` and `master` in `create-draft --type`.
**Rationale:** Keeps all three modes independently testable and preserves existing contracts. Master mode remains the complete archive; tailored remains job-specific; market becomes role-inferred + trend-curated + one-page.
**Alternatives considered:** Make market the default master behavior (rejected — breaks existing master contract); add a `--market` flag to master (rejected — conflates two distinct semantics).

### 6. `market-report.md` documents role, sources, omissions, and conflicts
**Decision:** Market mode emits `market-report.md` with: confirmed role, trend sources (URLs/titles from web search), omitted-evidence rationale (what was cut and why to meet one page), and conflicting claims excluded.
**Rationale:** Auditability — the user needs to understand why evidence was omitted and which trends informed the curation. Mirrors `master-report.md`'s conflict-reporting role but adds trend attribution.
**Alternatives considered:** Reuse `master-report.md` (rejected — different semantics; master reports conflicts only, market reports trend-driven curation decisions).

## Risks / Trade-offs

[Risk] Role inference may select the wrong target role → Mitigation: user confirmation step before any curation; user can correct the role.
[Risk] Web search returns stale or irrelevant trend data → Mitigation: per-call fresh search; user can review cited sources in market-report.md.
[Risk] Web search unavailable → Mitigation: prompt user to proceed with LLM knowledge base or exit.
[Risk] Curating a 6+ year rich profile into ~900 words/one page requires aggressive cutting → Mitigation: document omitted evidence and rationale in market-report.md; the 900-word target is soft ("some evidence-based resumes may remain below it").
[Risk] Market desirability is not deterministically validatable by resume_tools.py → Mitigation: the skill (model) owns the curation judgment; the helper owns structure, traceability, page count, and word count only.
[Risk] Trend language from search results could drift claim wording away from profile evidence → Mitigation: skill must not invent or alter factual claims (dates, metrics, tools, responsibilities, outcomes); trend alignment affects selection and ordering, not claim facts.

## Migration Plan

No migration of existing data is required. Market mode is additive:
1. Add `--type market` support to `create-draft` and `render` in `resume_tools.py`.
2. Add market-mode steps to the tailor-resume skill.
3. Add `specs/market-resume-mode/spec.md` requirement scenarios.
4. Add tests for market mode.
Existing `tailored` and `master` drafts remain valid; no backward-compatibility shims needed.

## Resolved Open Questions

- **Draft label:** Market mode uses a distinct label `market-resume` (via `--application market-resume --type market`) to avoid colliding with master drafts (`master-resume`).
- **Web-search queries:** The skill uses these per confirmed role, tunable in the skill:
  - `"<role> resume skills MNC 2026"`
  - `"<role> hiring expectations top companies 2026"`
  - `"<role> ATS keywords 2026"`
- **Role override:** Market mode allows the user to supply an optional role override after inference, instead of only accepting the inferred role.
