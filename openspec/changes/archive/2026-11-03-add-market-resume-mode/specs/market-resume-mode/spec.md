## ADDED Requirements

### Requirement: Market mode infers target role from profile
The system SHALL analyze the canonical profile (title, domains, skills, experience evidence) to infer a candidate target role.

#### Scenario: Role inferred from profile metadata
- **WHEN** market mode is invoked without a job description
- **THEN** the system infers a candidate target role from the profile's current title, domains, skills, and experience evidence

#### Scenario: User confirms or corrects inferred role
- **WHEN** the system presents an inferred role to the user
- **THEN** the user may confirm the role, provide a corrected role, or exit the operation

#### Scenario: Curating proceeds only after role confirmation
- **WHEN** the user has not confirmed or corrected the inferred role
- **THEN** the system does not curate evidence or render a market resume

### Requirement: Market mode researches MNC hiring trends via web search
The system SHALL invoke web search per skill call to gather current MNC expectations, required skills, and hiring trends for the confirmed role.

#### Scenario: Web search gathers trend data
- **WHEN** the user confirms a target role
- **THEN** the system performs web searches for current MNC expectations, required skills, and hiring trends for that role

#### Scenario: Trend sources are cited in market report
- **WHEN** web search returns results
- **THEN** the system records the sources used (titles and URLs) in `market-report.md`

### Requirement: Market mode curates evidence aligned to market trends
The system SHALL select profile evidence that aligns with current MNC expectations for the confirmed role, favoring concrete outcomes and transferable skills.

#### Scenario: Evidence selected for market alignment
- **WHEN** trend data is available for the confirmed role
- **THEN** the system selects profile evidence that matches in-demand skills and expectations for that role

#### Scenario: Factual claims are not altered for trend alignment
- **WHEN** curating evidence for market fit
- **THEN** the system does not invent or alter dates, metrics, technologies, responsibilities, or outcomes; trend alignment affects selection and ordering only

### Requirement: Market mode applies the same word-limit constraint as tailored mode
The system SHALL render a one-page resume with a ~900-word soft target measured from extractable PDF text, allowing up to eight sequential render attempts.

#### Scenario: Market resume fits one page
- **WHEN** the market resume is rendered
- **THEN** the generated PDF contains exactly one page with extractable text and conventional section headings

#### Scenario: Market resume approaches word target without filler
- **WHEN** the rendered PDF is below the ~900-word target
- **THEN** the system adds the strongest omitted role-fit evidence from relevance tiers without adding filler, duplicate claims, or unsupported facts

#### Scenario: Market render retries are bounded
- **WHEN** the initial render exceeds one page
- **THEN** the system allows up to seven sequential content revisions (eight total render attempts) to achieve one-page fit

### Requirement: Market mode produces a market report
The system SHALL emit a `market-report.md` documenting the confirmed role, trend sources, omitted-evidence rationale, and excluded conflicting claims.

#### Scenario: Market report includes role and sources
- **WHEN** a market resume is generated
- **THEN** `market-report.md` contains the confirmed role and the trend sources used

#### Scenario: Market report documents omitted evidence
- **WHEN** profile evidence is excluded to meet one-page fit
- **THEN** `market-report.md` lists the omitted evidence IDs and the rationale for omission

### Requirement: Market mode handles web search unavailability
The system SHALL prompt the user when web search is unavailable, offering to proceed with the LLM knowledge base or exit.

#### Scenario: Web search unavailable prompts user
- **WHEN** web search fails during market mode
- **THEN** the system informs the user and offers to proceed with the LLM knowledge base or exit the operation

#### Scenario: No trend data fabricated when search unavailable
- **WHEN** the user chooses to proceed without web search
- **THEN** the system uses only the LLM knowledge base and does not fabricate trend sources or MNC expectations

### Requirement: Market mode preserves master and tailored mode contracts
The system SHALL not alter master mode (all evidence, multi-page, no word/page limit) or tailored mode (job-description-driven, one page).

#### Scenario: Master mode unchanged
- **WHEN** market mode is added
- **THEN** master mode continues to preserve all distinct supported profile evidence with no word-count target or page limit

#### Scenario: Tailored mode unchanged
- **WHEN** market mode is added
- **THEN** tailored mode continues to require a job description, produce a fit report, and enforce strict one-page fit

### Requirement: Market mode does not modify canonical profile or root resume.yaml
The system SHALL store market-mode artifacts (resume.yaml, source-map.json, market-report.md, HTML, PDF, status.json) in an isolated draft directory under `generated/`.

#### Scenario: Market draft is isolated
- **WHEN** a market resume draft is created
- **THEN** all artifacts are written to an isolated directory under `generated/` and the canonical profile and root `resume.yaml` are not modified
