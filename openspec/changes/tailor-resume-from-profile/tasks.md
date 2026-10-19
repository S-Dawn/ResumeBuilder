## 1. Define and migrate the canonical profile

- [ ] 1.1 Define Markdown record frontmatter (`id`, `type`, `title`, `summary` plus optional metadata) and claim-level evidence blocks with stable IDs.
- [ ] 1.2 Migrate all current identity, summary, skills, experience, projects, education, certifications, and achievements from `resume.yaml` into profile records while retaining all source detail and leaving root `resume.yaml` unchanged.
- [ ] 1.3 Define a compact frontmatter-derived index and document record creation, evidence IDs, optional tags/aliases, and index behavior.
- [ ] 1.4 Implement deterministic index rebuild and profile validation for required metadata and duplicate record/evidence IDs; report actionable source locations.

## 2. Build safe tailoring and validation workflow

- [ ] 2.1 Add a repository-local GitHub Copilot in VS Code skill using the repository's `.github/skills/<name>/SKILL.md` convention; accept pasted or file-based job descriptions.
- [ ] 2.2 Specify skill behavior for index-first adaptive detail retrieval, untrusted JD/profile text, factual claim preservation, conflict reporting, and requesting ambiguous application metadata.
- [ ] 2.3 Define and implement a deterministic helper interface invoked by the skill for index generation, tailored YAML validation, source-ID validation, rendering, and PDF checks; report tool failures without success-shaped fallback.
- [ ] 2.4 Validate tailored YAML root, required sections, supported field names, and value types against the renderer contract before rendering.
- [ ] 2.5 Define the source-mapping manifest so each tailored evidence item maps to one or more stable profile evidence IDs; reject unknown IDs.
- [ ] 2.6 Generate `fit-report.md` mapping major job requirements to evidence IDs and listing unsupported/weakly supported requirements without retaining the full JD.
- [ ] 2.7 Write YAML, source map, fit report, HTML, and PDF into isolated per-application draft directories without changing the canonical profile or root `resume.yaml`.
- [ ] 2.8 Implement collision interaction for numbered draft, explicit replacement, or cancel; default to cancel when interaction is unavailable and retain prior drafts.
- [ ] 2.9 Retain failed generated artifacts and record a clear failed status; present successful drafts for human review only and never submit externally.
- [ ] 2.10 Document that selected profile records and the JD are sent as context to the configured Copilot model and advise against storing secrets in profile records.

## 3. Enforce one-page and ATS-oriented rendering

- [ ] 3.1 Add deterministic PDF page counting and selectable-text extraction using a maintained library compatible with supported Python versions.
- [ ] 3.2 Add an opt-in strict one-page mode for tailored outputs while preserving existing default YAML rendering behavior.
- [ ] 3.3 Omit a section heading and wrapper when its section has no content; preserve the order of non-empty sections.
- [ ] 3.4 Implement staged relevance-based trimming for at most three retries after initial render: trim lowest-relevance evidence first, then condense summary/skills/optional content, preserving contact details and employment chronology.
- [ ] 3.5 On persistent page overflow, retain artifacts, mark the draft failed, and report actual page count without claiming success or shrinking typography silently.
- [ ] 3.6 Verify the generated PDF's text extraction, conventional headings/order, and single-column structure; describe these as measurable safeguards rather than universal ATS compatibility.
- [ ] 3.7 Reconcile README YAML examples with actual renderer field names and document profile, output, review, collision, and privacy behavior.

## 4. Verify profile selection and end-to-end behavior

- [ ] 4.1 Add tests for index metadata/ID validation, YAML schema and provenance validation, output isolation/collision behavior, and failure reporting.
- [ ] 4.2 Add rendering tests for empty sections, one-page success, multi-page failure, three bounded trim retries, and selectable text/heading order.
- [ ] 4.3 Run role-distinct Copilot smoke cases for backend and Forward Deployed Engineer job descriptions; have a human review relevance, factual fidelity, source mapping, and fit-report gaps.
- [ ] 4.4 Confirm a second application draft does not change root `resume.yaml`, canonical profile records, or earlier application outputs; verify the full JD is not copied into retained artifacts.
