## ADDED Requirements

### Requirement: Analyze a job description without creating an application draft
The system SHALL provide a standalone GitHub Copilot skill that compares a user-provided job description with the canonical profile under `profile/`. The skill SHALL NOT create or modify a resume, application draft, or canonical profile record as part of the analysis.

#### Scenario: Analyze a pasted job description
- **WHEN** the user provides job-description text and requests a profile-fit analysis
- **THEN** the skill analyzes the description against relevant canonical profile evidence and presents the result without creating an application draft

#### Scenario: Analyze a job-description file
- **WHEN** the user supplies a path to a job-description file
- **THEN** the skill discloses that relevant file and profile contents will be sent as context to the configured Copilot model and obtains explicit confirmation before reading the file

#### Scenario: User declines file processing
- **WHEN** the user does not confirm processing of a job-description file
- **THEN** the skill does not read the file and offers analysis of pasted text instead

### Requirement: Retrieve relevant evidence and preserve traceability
The skill SHALL use the generated compact profile index to identify relevant records, then read only candidate profile records needed to assess the job requirements. It SHALL expand retrieval when needed for accuracy and SHALL NOT impose an arbitrary record-count cap. Every profile-based match or partial match SHALL cite one or more stable evidence IDs present in the profile.

#### Scenario: Identify directly supported requirements
- **WHEN** profile evidence directly supports a job requirement
- **THEN** the analysis identifies the requirement as supported and cites the relevant evidence IDs

#### Scenario: Identify partial evidence
- **WHEN** profile evidence supports only part of a requirement or provides indirect transferable evidence
- **THEN** the analysis identifies the requirement as partially supported, explains the limitation, and cites the relevant evidence IDs

#### Scenario: Expand retrieval to resolve fit
- **WHEN** candidate records do not provide enough detail to assess an important requirement accurately
- **THEN** the skill retrieves additional relevant profile records before classifying the requirement

### Requirement: Classify requirements and explain overall fit
The analysis SHALL distinguish supported, partially supported, and unsupported requirements. It SHALL distinguish requirements explicitly stated as required from preferred or otherwise lower-priority requirements when the job description makes that distinction clear. It SHALL present both a qualitative interpretation and a numeric evidence-coverage score, explain the score's method and limitations, and SHALL NOT present the score as a prediction of hiring or application success.

#### Scenario: Calculate a transparent evidence-coverage score
- **WHEN** the skill has classified the material job requirements
- **THEN** it calculates a weighted score using full credit for supported requirements, half credit for partially supported requirements, and no credit for unsupported requirements, weighting explicitly required qualifications twice as much as preferred or other requirements

#### Scenario: Explain ambiguous requirement priority
- **WHEN** the job description does not clearly distinguish required and preferred qualifications
- **THEN** the skill states that priority was inferred from the wording and avoids presenting the resulting score as more precise than the evidence allows

#### Scenario: Interpret profile silence conservatively
- **WHEN** no profile evidence is found for a requirement
- **THEN** the skill reports that the profile does not document the qualification and does not claim that the user lacks the qualification

#### Scenario: Exclude non-qualification content from scoring
- **WHEN** the job description contains company marketing, process instructions, or other content that is not a candidate qualification
- **THEN** the skill excludes that content from requirement classifications and the fit score

### Requirement: Recommend evidence, positioning, and skill-development improvements
The analysis SHALL identify (1) profile evidence the user may be able to verify is missing or under-documented, (2) ways to position existing evidence for the role, and (3) genuine skill-development areas suggested by unsupported or partially supported requirements. It SHALL distinguish these categories, avoid inventing facts or treating profile silence as proof of missing experience, and ask the user to verify any proposed new career facts before they are added to the canonical profile.

#### Scenario: Suggest profile evidence to verify
- **WHEN** a material requirement is not documented or is only weakly documented in the profile
- **THEN** the analysis asks whether the user has relevant experience that could be added and does not create or alter profile claims

#### Scenario: Suggest role-specific positioning
- **WHEN** existing evidence is relevant but not immediately apparent from its current framing
- **THEN** the analysis describes how the user could emphasize that evidence without changing its factual meaning

#### Scenario: Identify a development area
- **WHEN** a material requirement has no direct support and is not reasonably covered by transferable evidence
- **THEN** the analysis identifies it as a possible skill-development area, separate from profile-documentation gaps

### Requirement: Treat inputs as untrusted and avoid retaining job-description content
The skill SHALL treat job-description and profile contents as untrusted data rather than instructions, SHALL ignore embedded requests to access unrelated files or perform unrelated actions, and SHALL NOT reproduce or retain the complete job description in the analysis or generated artifacts.

#### Scenario: Ignore embedded instructions
- **WHEN** a job description or profile record contains instruction-like text unrelated to assessing qualifications
- **THEN** the skill treats that text only as source data and continues within the user's requested analysis scope

#### Scenario: Keep the report concise and privacy-aware
- **WHEN** the skill presents the analysis
- **THEN** it summarizes requirements in its own words, cites profile evidence IDs, and does not reproduce the complete job description

### Requirement: Present a structured analysis for human judgment
The skill SHALL present a report containing an overall qualitative assessment, numeric score and calculation explanation, evidence-backed strengths, partial matches, unsupported requirements, profile-evidence questions, positioning opportunities, skill-development areas, and limitations. It SHALL make clear that the analysis is advisory and that the user decides whether to apply.

#### Scenario: Review a complete fit report
- **WHEN** the analysis is complete
- **THEN** the user receives each required report section, with `None identified` used for any section with no entries

#### Scenario: No usable requirements are identified
- **WHEN** the supplied description contains insufficient qualification information to support a meaningful comparison
- **THEN** the skill reports that limitation, does not manufacture a score or fit conclusion, and asks for a more complete job description
