# ResumeBuilder Skills Distribution Design

## Goal

Enable users to install ResumeBuilder agent skills into their machine/agent runtime via an install command (e.g. `npx skills@latest add S-Dawn/ResumeBuilder`, `claude plugin install resumebuilder-skills`, etc.), with automatic updates for managed routes.

## Distributable skills (non-openspec only)

The openspec skills (`openspec-*`) are local tooling for this repo's spec-driven workflow and are **excluded** from distribution.

Promoted (shipped) skills:

| Skill | Purpose |
|-------|---------|
| `tailor-resume` | Create a job-tailored/master/market resume from the canonical profile |
| `maintain-profile` | Update the canonical career profile from user-provided facts/resume |
| `analyze-profile-fit` | Compare profile against a job description; report fit, gaps, improvements |
| `update-projects` | Refine or add a project in the canonical career profile |

Plus a setup skill:

| Skill | Purpose |
|-------|---------|
| `setup-resumebuilder-skills` | One-time per-repo configuration (profile path, output dir, ATS settings) |

## Distribution model (mirrors mattpocock/skills)

The repo does **not** publish an npm package containing the skill code. Instead:

1. Skills live as `SKILL.md` files with YAML frontmatter under `.opencode/skills/`.
2. A `.claude-plugin/plugin.json` manifest lists the promoted skill directories (single source of truth, curated subset).
3. A `.claude-plugin/marketplace.json` makes the repo its own marketplace for Codex, Copilot, and VS Code.
4. A root `package.json` holds the version used by managed routes to detect updates.
5. A `scripts/sync-plugin-version.mjs` keeps `plugin.json` version in sync with `package.json`.
6. `@changesets/cli` drives version bumps and git tags via a GitHub Actions release workflow.
7. `.agents/install-block.md` is the single source of truth for per-agent install wording, copied verbatim into `README.md`.
8. `npx skills@latest add S-Dawn/ResumeBuilder -a <agent>` is the universal fallback (skills.sh) for agents without a native plugin system.

## Install routes

| Agent | Command | Auto-updates? |
|-------|---------|---------------|
| Claude Code | `claude plugin install resumebuilder-skills` | Yes (official marketplace) |
| Codex | `codex plugin marketplace add S-Dawn/ResumeBuilder` then `codex plugin add resumebuilder-skills@S-Dawn` | Yes (at startup) |
| Copilot CLI / VS Code | `copilot plugin marketplace add S-Dawn/ResumeBuilder` then `copilot plugin install resumebuilder-skills@S-Dawn` (+ `autoUpdate: true` in settings) | Yes |
| Gemini CLI | `gemini skills install https://github.com/S-Dawn/ResumeBuilder.git --path .opencode/skills` | No (re-run to update) |
| Any other agent | `npx skills@latest add S-Dawn/ResumeBuilder -a <agent>` | No (`npx skills update` + re-run `add`) |

## Files to create / modify

| File | Purpose |
|------|---------|
| `package.json` | Root package; name `resumebuilder-skills`, version, devDeps (`@changesets/cli`) |
| `.claude-plugin/plugin.json` | Claude Code plugin manifest; lists promoted skill paths + version |
| `.claude-plugin/marketplace.json` | Repo-owned marketplace for Codex/Copilot/VS Code |
| `.agents/install-block.md` | Canonical per-agent install wording (single source of truth) |
| `scripts/sync-plugin-version.mjs` | Syncs `plugin.json` version from `package.json` |
| `.changeset/config.json` | Changeset configuration |
| `.github/workflows/release.yml` | Release workflow: version PR + tag on push to main |
| `README.md` | Install section (copied from `.agents/install-block.md`) |
| `skills/setup-resumebuilder-skills/SKILL.md` | New setup skill (one-time per-repo config) |
| `DESIGN.md` | This document |

## Invocation model

Each skill is either:
- **User-invoked**: reachable only by the human (`disable-model-invocation: true` in frontmatter; `policy.allow_implicit_invocation: false` in `agents/openai.yaml`).
- **Model-invoked**: default; reachable by model or user.

All ResumeBuilder distributable skills are user-invoked (the human chooses when to tailor, maintain, analyze, or update).

## Update mechanism

- Managed routes (Claude Code, Codex, Copilot, VS Code) use the `version` field in `plugin.json` to decide when installed users receive an update.
- `npm run version` runs `changeset version` then `sync-plugin-version.mjs` to keep versions aligned.
- The universal fallback (`npx skills@latest`) requires the user to re-run `npx skills update` and `add` to pick up new/changed skills.
