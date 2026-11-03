## Why

Distributable ResumeBuilder skills currently live under `.agents/skills/`, a directory meant for local agent runtime setup rather than distribution. Following the mattpocock/skills convention, distributable skills should live under a root-level `skills/` directory so they are discoverable by `npx skills@latest add S-Dawn/ResumeBuilder` (Route A) without publishing an npm package. The current `.claude-plugin/plugin.json` also references skill paths under `.opencode/skills/`, which do not exist for distributable skills — it dangles. Relocating to root `skills/` makes the npx install route work end-to-end.

## What Changes

- Move the 5 distributable skills from `.agents/skills/` to root `skills/` (flat layout): `tailor-resume`, `maintain-profile`, `analyze-profile-fit`, `update-projects`, `setup-resumebuilder-skills`.
- Delete `.agents/skills/` after the move (it becomes empty).
- Update `DESIGN.md`: distribution model states skills live under `skills/`; install routes table (gemini `--path skills/`); "Files to create / modify" table.
- Update `.agents/install-block.md`: gemini `--path .opencode/skills` → `--path skills/`.
- Update `README.md`: gemini `--path .opencode/skills` → `--path skills/`.
- Update `.claude-plugin/plugin.json`: 5 skill paths from `./.opencode/skills/...` to `./skills/...`.
- No changes to `.claude-plugin/marketplace.json`, `.github/workflows/release.yml`, `.changeset/`, or `scripts/sync-plugin-version.mjs` (managed plugin/marketplace routes deferred to a later change).

## Capabilities

### New Capabilities
None — this is a relocation/refactor of existing distributable skills; no new capability or behavior is introduced.

### Modified Capabilities
None — no existing spec-level behavior changes.

## Impact

- `.agents/skills/` — removed
- `skills/` — added (5 skill directories, content unchanged from `.agents/skills/`)
- `DESIGN.md` — path references and install routes updated
- `.agents/install-block.md` — gemini install path updated
- `README.md` — gemini install path updated
- `.claude-plugin/plugin.json` — skill paths updated
