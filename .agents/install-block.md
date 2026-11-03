# The canonical install block

One install story, one wording. `README.md`, `.changeset/*`, and every page
under `docs/` must say **this** and nothing else. Change it here first, then
propagate.

## Managed installs first

Lead with installs that update themselves. Fall back to skills.sh, labelled
"manual updates", only for agents that have no such install. Call a route
managed only if it updates without the user running a command. Put any one-time
opt-in beside its install command. Never promise "instant".

Claude Code installs from its official marketplace. Every other managed route
installs from this repo's own marketplace, `.claude-plugin/marketplace.json`
and `.claude-plugin/plugin.json`. Those routes reinstall only when the `version`
in `plugin.json` changes. The Release workflow runs `npm run version`, which
copies that field from `package.json`, so users get a release when the "chore:
version skills" PR merges.

| Agent         | Route                            | Updates itself?                                                  |
|-------------- |----------------------------------|------------------------------------------------------------------|
| Claude Code   | `claude plugin install`          | Yes, by default                                                  |
| Codex         | `@resumebuilder` marketplace     | Yes, at startup, by default                                      |
| Copilot CLI   | `@resumebuilder` marketplace     | Yes, after a one-time `autoUpdate: true`                         |
| VS Code       | Chat: Install Plugin From Source | Yes, daily, by default                                           |
| Gemini CLI    | `gemini skills install` (copies) | No. Re-run to update.                                            |
| Everyone else | skills.sh                        | No. Run `npx skills update`, and re-run `add` for new skills     |

## Claude Code

<canonical-block name="claude-code">

```bash
claude plugin install resumebuilder-skills
```

Updates itself by default.

</canonical-block>

## Codex

<canonical-block name="codex">

```bash
codex plugin marketplace add S-Dawn/ResumeBuilder
codex plugin add resumebuilder-skills@resumebuilder
```

Updates itself at startup.

</canonical-block>

## GitHub Copilot (CLI and VS Code)

Use the marketplace. Copilot has deprecated direct repo installs, and they
can't auto-update. The `extraKnownMarketplaces` entry follows the documented
schema.

<canonical-block name="copilot">

```bash
copilot plugin marketplace add S-Dawn/ResumeBuilder
copilot plugin install resumebuilder-skills@resumebuilder
```

Then, once, add to `~/.copilot/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "resumebuilder": { "source": { "source": "github", "repo": "S-Dawn/ResumeBuilder" }, "autoUpdate": true }
  }
}
```

In VS Code, run **Chat: Install Plugin From Source** and enter
`https://github.com/S-Dawn/ResumeBuilder`. It updates daily.

</canonical-block>

## Gemini CLI

Gemini doesn't read `.claude-plugin`, and `--path` takes one folder. One install
per folder gives the promoted set.

<canonical-block name="gemini">

```bash
gemini skills install https://github.com/S-Dawn/ResumeBuilder.git --path skills/
```

Re-run to update.

</canonical-block>

## Every other agent, or editable files (skills.sh)

`-a` preselects the agent. Prefer skills.sh to an agent's own repo installer.

<canonical-block name="other-agents">

```bash
npx skills@latest add S-Dawn/ResumeBuilder -a <agent>  # cursor, opencode, devin, windsurf, amp, pi; omit -a to choose
```

When the installer asks which skills to take, include
`setup-resumebuilder-skills`. To update, run `npx skills@latest update`, and
re-run `add` to pick up new skills.

</canonical-block>

<canonical-block name="skills-sh-one-skill">

```bash
npx skills@latest add S-Dawn/ResumeBuilder --skill=<name>
```

```bash
npx skills@latest update <name>
```

</canonical-block>

`skills@latest` is the pinned spelling everywhere.

## The two routes are exclusive

The plugin is a managed, read-only bundle you subscribe to. skills.sh writes
files you own and edit. Installing both leaves the user with every skill twice:
always say "pick one".

## Step 2: Run /setup-resumebuilder-skills

In your agent, run it once per repo. It will:

- Ask where your canonical profile lives (`profile/`)
- Ask where resume drafts should be saved (`generated/`)
- Ask which ATS validation you want (WeasyPrint, pypdf, or both)
