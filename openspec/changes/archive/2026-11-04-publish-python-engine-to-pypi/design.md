## Context

Distributable ResumeBuilder skills (tailor-resume, maintain-profile, analyze-profile-fit,
update-projects, setup-resumebuilder-skills) invoke Python scripts that live only in this repo:
`resume_tools.py` (profile index, draft creation, rendering, validation, stage/promote) and
`ResumeBuilder.py` (legacy YAML renderer). On a host machine where a user has installed the skills
via `npx skills@latest add S-Dawn/ResumeBuilder`, only the SKILL.md files are copied — the Python
engine is absent. Running `poetry run python resume_tools.py profile-index` therefore fails.

The skills also assume `poetry` is available on the host, which is not guaranteed for users who
only want to run skills, not develop the repo.

Following the mattpocock/skills pattern (skills invoke external packages via `uvx` at
runtime rather than requiring pre-installation), the Python engine should be published to PyPI and
skills should invoke it through `uvx resumebuilder-tools@<version> <command>`.

## Goals / Non-Goals

**Goals:**
- Make the Python engine installable on any host machine via `uvx` without requiring `git clone`, `poetry install`, or `pipx`.
- Skills invoke the engine via version-pinned `uvx resumebuilder-tools@<version> <command>`.
- No behavioral change to skill logic — only the engine invocation mechanism changes.
- `setup-resumebuilder-skills` verifies `uv`/`uvx` availability and engine resolution.
- `uv` is the single toolchain for local development, building, publishing, and runtime resolution.

**Non-Goals:**
- Merging the Python engine into this repo's poetry project permanently (long-term it may live elsewhere).
- Changing what each skill does (tailor, maintain, analyze, update, setup remain the same).
- Supporting `poetry run python resume_tools.py` as a primary path (Poetry is removed from the toolchain).
- Supporting `pipx` as an alternative runtime resolver (uv/uvx is the single standard).

## Decisions

| Decision | Rationale | Alternatives considered |
|---|---|---|
| PyPI package name `resumebuilder-tools` | Clear, discoverable, matches the "tools" nature of `resume_tools.py`. | `resumebuilder-engine`, `resume-cli` — less descriptive. |
| Console entry point: single `resumebuilder-tools` with subcommands (`profile-index`, `create-draft`, `render`, `validate-profile`, `stage-profile-update`, `promote-profile-update`) | One command, one version pin per skill; extensible; discoverable via `--help`; matches mattpocock pattern (`uvx ruff@0.8.0 check .`). | Multiple entry points (`resume-index`, `resume-render`) — more surface area, each needs its own version pin. |
| Engine lives in this repo (for now, coupled release) | One changeset, one release workflow, one tag bumps both skills and engine; no version alignment problem; less overhead. | Separate repo — independent versioning but more overhead; revisit when versioning needs diverge. |
| Invoke via `uvx resumebuilder-tools@<version>` | mattpocock-recommended standard; isolated env, version-pinned, no pre-install on host. | `pipx run` — broader OS availability but slower cold start. |
| Skills pin exact engine version via `@<version>` | Reproducible behavior; no surprise breaking changes from engine updates. | Floating version (`>=1.0`) — risk of silent breakage. |
| `uv` throughout (dev, build, publish, runtime) | One toolchain everywhere; `uv` already required on hosts for `uvx` runtime; `uv.lock` replaces `poetry.lock`; `uv publish` supports trusted publishing natively. | Keep Poetry for dev + uv for runtime — two tools, two lockfiles, migration friction. |

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| `uv`/`uvx` not installed on host machine. | `setup-resumebuilder-skills` checks for `uv`/`uvx` and guides installation; `compatibility` frontmatter documents requirement. |
| Network required to resolve engine package at skill runtime. | Documented in `compatibility`; offline use not supported by design. |
| Engine version drift from skills version. | Skills pin exact engine version; coupled release bumps both together via changesets. |
| `poetry run python resume_tools.py` no longer works in skills. | `poetry` removed from toolchain; `resume_tools.py` remains in repo for reference; skills use `uvx` path exclusively. |
| PyPI publish credentials/token management. | GitHub Actions trusted publishing via OIDC — no long-lived API tokens stored as repo secrets; every publish tied to a git tag. |
| `uv` migration from existing `poetry.lock`. | Run `uv lock` to generate `uv.lock` from existing `pyproject.toml`; remove `poetry.lock`; update CI to use `uv sync`/`uv build`/`uv publish`. |

## Migration Plan

1. Migrate local dev toolchain to `uv` throughout: run `uv lock` to generate `uv.lock` from `pyproject.toml`, remove `poetry.lock`, update CI to use `uv sync`/`uv build`/`uv publish`.
2. Create PyPI package source (`pyproject.toml`, console scripts) from existing `resume_tools.py` + `ResumeBuilder.py`.
3. Publish initial version `1.0.0` to PyPI via GitHub Actions trusted publishing on release tag.
4. Update each skill's SKILL.md: replace `poetry run python resume_tools.py X` with `uvx resumebuilder-tools@<version> X`.
5. Add `compatibility` frontmatter to each skill.
6. Update `setup-resumebuilder-skills` to verify `uv`/`uvx` availability and engine resolution.
7. Extend `.github/workflows/release.yml` with a PyPI publish job (trusted publishing) triggered on release tag.
8. Test end-to-end: fresh machine, `pip install uv` (or `brew install uv`), `npx skills@latest add S-Dawn/ResumeBuilder`, run a skill.

Rollback: revert skills to `poetry run python resume_tools.py` and keep engine local-only (requires restoring `poetry` toolchain).

## Open Questions

None — all decisions (flat skills layout, single `resumebuilder-tools` entry point, same-repo coupled release, GitHub Actions trusted publishing, `uv` throughout) are resolved.
