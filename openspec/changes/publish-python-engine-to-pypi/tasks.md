## 1. Create PyPI package for the Python engine

- [x] 1.1 Extract `resume_tools.py` and `ResumeBuilder.py` into a package directory (e.g. `python_engine/`)
- [x] 1.2 Add `pyproject.toml` with package name `resumebuilder-tools`, version, dependencies (weasyprint, pypdf, pillow, pyyaml), Python >=3.11, using `uv` as the toolchain (dev, build, publish)
- [x] 1.3 Run `uv lock` to generate `uv.lock` from `pyproject.toml`; remove `poetry.lock`
- [x] 1.4 Define single console script entry point `resumebuilder-tools` with subcommands (`profile-index`, `create-draft`, `render`, `validate-profile`, `stage-profile-update`, `promote-profile-update`)
- [x] 1.5 Verify package builds locally (`uv build`)
- [x] 1.6 Verify `resumebuilder-tools --help` and `resumebuilder-tools profile-index --help` work locally via `uv run`

## 2. Publish engine to PyPI via GitHub Actions trusted publishing

- [ ] 2.1 Configure PyPI trusted publishing for `resumebuilder-tools` project name
- [x] 2.2 Add PyPI publish job to `.github/workflows/release.yml` using `uv publish` with trusted publishing (OIDC), triggered on release tag
- [ ] 2.3 Publish initial version `1.0.0` of `resumebuilder-tools` to PyPI via the release workflow
- [ ] 2.4 Confirm package is installable: `uvx resumebuilder-tools@1.0.0 --help`

## 3. Update skills to invoke engine via uvx

- [x] 3.1 Update `tailor-resume/SKILL.md`: replace `poetry run python resume_tools.py` with `uvx resumebuilder-tools@1.0.0` (all subcommands)
- [x] 3.2 Update `maintain-profile/SKILL.md`: replace `poetry run python resume_tools.py` with `uvx resumebuilder-tools@1.0.0`
- [x] 3.3 Update `analyze-profile-fit/SKILL.md`: replace `poetry run python resume_tools.py` with `uvx resumebuilder-tools@1.0.0`
- [x] 3.4 Update `update-projects/SKILL.md`: replace `poetry run python resume_tools.py` with `uvx resumebuilder-tools@1.0.0`
- [x] 3.5 Update `setup-resumebuilder-skills/SKILL.md`: replace `poetry run python resume_tools.py` with `uvx resumebuilder-tools@1.0.0`

## 4. Add compatibility frontmatter and setup verification

- [x] 4.1 Add `compatibility` frontmatter to each of the 5 skills declaring Python + uv/uvx requirement
- [x] 4.2 Update `setup-resumebuilder-skills` to verify `uv`/`uvx` availability and `resumebuilder-tools` resolution
- [x] 4.3 Update `setup-resumebuilder-skills` to guide user to install `uv` if missing

## 5. Verify end-to-end

- [x] 5.1 Confirm `npx skills@latest add S-Dawn/ResumeBuilder --list` still surfaces all 5 skills
- [x] 5.2 Confirm no `poetry run python resume_tools.py` references remain in `skills/` SKILL.md files
- [x] 5.3 Confirm all `compatibility` frontmatter fields are present and valid
- [x] 5.4 Confirm `uv.lock` exists and `poetry.lock` is removed
