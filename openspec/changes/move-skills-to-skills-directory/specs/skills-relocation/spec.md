## ADDED Requirements

### Requirement: Skills discoverable from root skills/ directory
The system SHALL expose all 5 distributable skills under a root-level `skills/` directory so the `npx skills` CLI discovers them when resolving `S-Dawn/ResumeBuilder`.

#### Scenario: npx list surfaces all skills
- **WHEN** a user runs `npx skills@latest add S-Dawn/ResumeBuilder --list`
- **THEN** the CLI surfaces `tailor-resume`, `maintain-profile`, `analyze-profile-fit`, `update-projects`, and `setup-resumebuilder-skills`

#### Scenario: Skill directory structure
- **WHEN** the repository is cloned or fetched by the `npx skills` CLI
- **THEN** each skill exists at `skills/<skill-name>/SKILL.md` with valid `name` and `description` frontmatter matching its parent directory name

### Requirement: Old skills location removed
The system SHALL not retain distributable skills under `.agents/skills/` after the relocation.

#### Scenario: Legacy location removed
- **WHEN** the change is applied
- **THEN** `.agents/skills/` no longer exists (empty directory deleted)

### Requirement: Path references updated
The system SHALL update every path reference that pointed to the old skill location so none are dangling.

#### Scenario: plugin.json paths resolve
- **WHEN** `.claude-plugin/plugin.json` is read
- **THEN** each skill path is `./skills/<name>` (not `./.opencode/skills/<name>`)

#### Scenario: Install documentation paths consistent
- **WHEN** `DESIGN.md`, `.agents/install-block.md`, or `README.md` reference the skills install path
- **THEN** they reference `skills/` (not `.opencode/skills/` or `.agents/skills/`)

### Requirement: No behavior change to skills
The system SHALL preserve skill content unchanged during relocation.

#### Scenario: Skill content intact after move
- **WHEN** each skill is moved from `.agents/skills/` to `skills/`
- **THEN** `SKILL.md` frontmatter (`name`, `description`, `disable-model-invocation`) and body are byte-for-byte identical
