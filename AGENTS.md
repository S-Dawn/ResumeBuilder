# ResumeBuilder — Agent Runtime Guide

This repo ships agent skills under `skills/` and a Python engine under `python_engine/`.
Agent runtimes (Claude Code, OpenCode, GitHub Copilot, Codex, VS Code, Gemini CLI, universal agents)
read `skills/*/SKILL.md` and execute the shell commands referenced inside them.

## Running skills locally without installing from PyPI

Developer skill commands should run against local `python_engine/` code — no `uvx`, no PyPI package,
no version bump required for iteration.

### 1. Set dev mode in your shell

```bash
export RESUMEBUILDER_TOOLS_MODE=dev
```

This makes `./scripts/resume-tools` run `uv run -m python_engine.resume_tools` (local code) instead of
`uvx resumebuilder-tools@latest` (published package).

### 2. Create a local config (gitignored, one-time)

```bash
cat > resumebuilder-skills.config.json <<EOF
{
  "profile_dir": "profile",
  "generated_dir": "generated"
}
EOF
```

`resumebuilder-skills.config.json` is gitignored. It supplies `profile_dir` and `generated_dir` to the engine.

### 3. Invoke skills through the agent runtime

The agent reads `skills/*/SKILL.md` and runs commands like:

```bash
./scripts/resume-tools validate-profile --profile-dir profile
./scripts/resume-tools stage-profile-update --operations /tmp/ops.json
./scripts/resume-tools create-draft --application my-app
```

With `RESUMEBUILDER_TOOLS_MODE=dev` set, these run against your local edits immediately.

### 4. Return to production (published package)

```bash
unset RESUMEBUILDER_TOOLS_MODE
# or
export RESUMEBUILDER_TOOLS_MODE=production
```

Default (unset) runs `uvx resumebuilder-tools@latest` — the latest published PyPI package.

---

## How skills are resolved by runtime

| Runtime | Skill discovery | Local registration |
|---|---|---|
| **Claude Code** | `.claude-plugin/plugin.json` lists skill dirs | Add `"./skills/<new-skill>"` to the `skills` array |
| **OpenCode** | `.opencode/skills/*/` | Copy/symlink `skills/<new-skill>` into `.opencode/skills/` |
| **Codex** | `@resumebuilder` marketplace → `.claude-plugin/plugin.json` | Symlink `skills/<new-skill>` into `.agents/skills/` |
| **GitHub Copilot** | `@resumebuilder` marketplace → `.claude-plugin/plugin.json` | Symlink `skills/<new-skill>` into `.agents/skills/` |
| **VS Code** | Chat: Install Plugin From Source → `.claude-plugin/plugin.json` | Symlink `skills/<new-skill>` into `.agents/skills/` |
| **Gemini CLI** | `gemini skills install ... --path skills/` | Point `--path` at `.agents/skills/` or `skills/` |
| **Universal (skills.sh)** | `npx skills@latest add S-Dawn/ResumeBuilder -a <agent>` | Clones repo, copies `skills/` |

Skills are explicitly registered — there is no auto-scan for new `SKILL.md` files.

`.agents/skills/` already contains symlinks to all resumebuilder skills. When you add a new skill
under `skills/`, symlink it into `.agents/skills/` as well:

```bash
ln -s "../../skills/<new-skill>" .agents/skills/<new-skill>
```

---

## Adding a new skill

1. Create `skills/<new-skill>/SKILL.md` using `./scripts/resume-tools <subcommand>` commands (no `uvx`).
2. Register it:
   - Claude Code: add `"./skills/<new-skill>"` to `.claude-plugin/plugin.json`.
   - OpenCode: copy/symlink into `.opencode/skills/`.
   - Codex / Copilot / VS Code / universal: symlink into `.agents/skills/`.
3. Test manually first:

   ```bash
   export RESUMEBUILDER_TOOLS_MODE=dev
   ./scripts/resume-tools <subcommand> [args]
   ```

4. Then invoke through the agent runtime.

---

## Key files

| File | Purpose |
|---|---|
| `scripts/resume-tools` | Wrapper: dev mode → `uv run -m python_engine.resume_tools`; production → `uvx resumebuilder-tools@latest` |
| `python_engine/cli_invoke.py` | Shared Python helper: `resolve_command(*args)` / `run(*args)` honoring `RESUMEBUILDER_TOOLS_MODE` |
| `skills/*/SKILL.md` | Skill instructions; commands now use `./scripts/resume-tools` instead of `uvx` |
| `.claude-plugin/plugin.json` | Claude Code / Codex / Copilot / VS Code skill registration |
| `.claude-plugin/marketplace.json` | Marketplace manifest for Codex / Copilot / VS Code |
| `.agents/skills/` | Local skills directory symlinked to `skills/` for Codex / Copilot / VS Code / Gemini / universal |
| `.opencode/skills/` | Local skills directory symlinked to `skills/` for OpenCode |
| `.agents/install-block.md` | Canonical install instructions per agent runtime |
| `resumebuilder-skills.config.json` | Local dev config (gitignored): `profile_dir`, `generated_dir` |
