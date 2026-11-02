## 1. Helper: add market draft type to resume_tools.py

- [x] 1.1 Add `market` to supported draft types in `create_draft` validation
- [x] 1.2 Add `market` to supported draft types in `render_draft` validation
- [x] 1.3 Route market drafts through strict one-page validation (same as tailored)
- [x] 1.4 Reuse `count_pdf_words` word-count measurement for market drafts
- [x] 1.5 Update `create-draft` CLI help text to document `--type market`
- [x] 1.6 Update `render` CLI help text to document market draft rendering

## 2. Skill: add market mode to tailor-resume skill

- [x] 2.1 Add role-inference step from profile metadata (title, domains, skills, experience)
- [x] 2.2 Add user confirmation step for inferred role (confirm / correct / exit)
- [x] 2.3 Add web-search-per-skill-call for MNC expectations of confirmed role
- [x] 2.4 Add web-search-unavailable prompt (proceed with LLM knowledge or exit)
- [x] 2.5 Add evidence curation aligned to market trends under one-page/~900-word constraint
- [x] 2.6 Add `market-report.md` generation (role, trend sources, omitted-evidence rationale, conflicts)
- [x] 2.7 Ensure factual claims are not altered for trend alignment (selection/ordering only)
- [x] 2.8 Update skill mirrors under `.cursor/skills/` and `.github/skills/`

## 3. Specs: add market-mode requirements to profile-based-resume-tailoring

- [x] 3.1 Add market-mode requirement scenarios to `openspec/specs/profile-based-resume-tailoring/spec.md`
- [x] 3.2 Ensure master and tailored requirements are unchanged in the spec

## 4. Tests: add market mode coverage

- [x] 4.1 Add test for market draft creation with `--type market`
- [x] 4.2 Add test for market one-page validation (PageFitError on >1 page)
- [x] 4.3 Add test for market word-count measurement in status.json
- [x] 4.4 Add test for web-search-unavailable prompt path

## 5. Docs: document market mode

- [x] 5.1 Update `README.md` to document the market mode option
- [x] 5.2 Verify change artifacts pass `openspec validate`
