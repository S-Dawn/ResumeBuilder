## ADDED Requirements

### Requirement: Python engine published to PyPI
The system SHALL publish the Python engine (`resume_tools.py`, `ResumeBuilder.py`) as a pip-installable package on PyPI so skills can resolve it at runtime without a repo clone.

#### Scenario: Engine installable via uvx
- **WHEN** a user runs `uvx resumebuilder-tools@<version> --help`
- **THEN** the PyPI package resolves and displays help output

#### Scenario: Engine has console script entry point
- **WHEN** the package is installed
- **THEN** the single `resumebuilder-tools` command is available on PATH with subcommands: `profile-index`, `create-draft`, `render`, `validate-profile`, `stage-profile-update`, `promote-profile-update`

### Requirement: Skills invoke engine via uvx
The system SHALL update all distributable skills to invoke the Python engine through version-pinned `uvx` commands instead of `poetry run python`.

#### Scenario: Skill calls engine via uvx
- **WHEN** a skill runs `profile-index`
- **THEN** it executes `uvx resumebuilder-tools@<version> profile-index`

#### Scenario: Engine version pinned in skill
- **WHEN** a skill references the engine
- **THEN** the command includes an exact version pin (`@<version>` or `==<version>`)

### Requirement: Skills declare runtime compatibility
The system SHALL add `compatibility` frontmatter to each distributable skill declaring the Python/uv requirement.

#### Scenario: Skill frontmatter includes compatibility
- **WHEN** a skill's SKILL.md is read
- **THEN** it contains a `compatibility` field stating Python and `uv`/`uvx` are required

### Requirement: Setup skill verifies engine resolution
The system SHALL update `setup-resumebuilder-skills` to verify `uv`/`uvx` availability and that the engine package resolves.

#### Scenario: Setup checks uv/uvx
- **WHEN** setup-resumebuilder-skills runs
- **THEN** it confirms `uv` or `uvx` is available and `resumebuilder-tools` resolves

#### Scenario: Setup guides engine install if missing
- **WHEN** uv/uvx is not available
- **THEN** setup instructs the user to install `uv` before proceeding

### Requirement: PyPI publishing automated via GitHub Actions trusted publishing
The system SHALL automate PyPI package publishing via GitHub Actions triggered on release tag, using trusted publishing (OIDC, no API token secrets).

#### Scenario: Publish on release tag
- **WHEN** a release tag is pushed
- **THEN** GitHub Actions builds the engine package and publishes it to PyPI via trusted publishing
