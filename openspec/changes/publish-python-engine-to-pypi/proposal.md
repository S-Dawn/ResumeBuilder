## Why

Distributable ResumeBuilder skills call Python scripts (`resume_tools.py`, `ResumeBuilder.py`) that live only in this repo. On a host machine where a user has installed the skills via `npx skills@latest add S-Dawn/ResumeBuilder`, those Python scripts are absent, so commands like `poetry run python resume_tools.py profile-index` fail. Following mattpocock/skills' proven pattern, the Python engine should be published to PyPI and invoked by skills via `uvx`/`pipx` at runtime — no `git clone` or `poetry install` prerequisite on the host machine.

## What Changes

- Publish a Python engine package (e.g. `resumebuilder-tools`) to PyPI containing `resume_tools.py` and `ResumeBuilder.py` with console script entry points.
- Update all distributable skills to invoke the engine via `uvx resumebuilder-tools@<version> <command>` (or `pipx run`) instead of `poetry run python resume_tools.py <command>`.
- Add `compatibility` frontmatter to each skill declaring the Python/runtime requirement.
- Update `setup-resumebuilder-skills` to verify the PyPI engine resolves (uvx/pipx available).
- Add PyPI publishing workflow (GitHub Actions on tag/release).
- **BREAKING**: Skills no longer require `poetry`; they require `uvx` or `pipx` and network access to resolve the engine package.

## Capabilities

### New Capabilities
- `python-engine-pypi`: PyPI-distributed Python engine providing CLI commands that ResumeBuilder skills invoke at runtime (profile index, draft creation, rendering, validation, profile stage/promote).

### Modified Capabilities
None — skill behavior requirements are unchanged; only the engine invocation mechanism changes from `poetry run python` to `uvx`/`pipx`.

## Impact

- `skills/*/SKILL.md` — invocation commands updated from `poetry run python resume_tools.py` to `uvx resumebuilder-tools@<version>`
- `skills/*/SKILL.md` — `compatibility` frontmatter added
- `skills/setup-resumebuilder-skills/SKILL.md` — setup verifies uvx/pipx + engine resolution
- New PyPI package (engine source, pyproject.toml, console scripts)
- `.github/workflows/` — PyPI publish workflow on release tag
- `package.json` / `.claude-plugin/plugin.json` — version alignment (engine version vs skills version)
