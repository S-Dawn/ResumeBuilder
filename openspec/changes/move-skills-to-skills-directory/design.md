## Context

Distributable ResumeBuilder skills (tailor-resume, maintain-profile, analyze-profile-fit,
update-projects, setup-resumebuilder-skills) currently live under `.agents/skills/`. That directory is
intended for local agent runtime setup, not distribution. Following the mattpocock/skills convention,
distributable skills should live under a root-level `skills/` directory so they are discoverable by
`npx skills@latest add S-Dawn/ResumeBuilder` (Route A) without publishing an npm package.

Additionally, `.claude-plugin/plugin.json` references skill paths under `./.opencode/skills/...`, which do
not exist for distributable skills — it dangles. The skills are real only under `.agents/skills/`.

This change relocates the 5 skills to root `skills/` (flat layout) and updates all path references so the
npx install route works end-to-end. Managed plugin/marketplace routes (Claude Code plugin, Codex/Copilot
marketplace) are deferred to a later change; plugin.json paths are updated now only to avoid dangling
references.

## Goals / Non-Goals

**Goals:**
- Make `npx skills@latest add S-Dawn/ResumeBuilder --list` surface all 5 distributable skills.
- Keep the layout flat: `skills/<skill-name>/SKILL.md` (no buckets, single domain).
- Preserve skill content unchanged (move only).
- Remove `.agents/skills/` after the move.
- Update every path reference that pointed to the old location.

**Non-Goals:**
- No npm package publication (Route B is explicitly out of scope).
- No changes to managed plugin/marketplace routes beyond updating `plugin.json` paths (deferred).
- No behavior change to skills themselves.
- No changes to openspec skills under `.opencode/skills/` (those stay put; they are local tooling).

## Decisions

| Decision | Rationale | Alternatives considered |
|---|---|---|
| Root `skills/` (flat) | Matches mattpocock/skills convention; `npx skills` CLI scans `skills/` natively; simple for a single-domain project. | Bucketed (`skills/engineering/`, etc.) — over-engineering for one domain; can be added later if the catalog grows. |
| Keep `.agents/install-block.md` as canonical wording | It is already the single source of truth for install wording; no need to relocate. | Move it — unnecessary churn. |
| Update `plugin.json` paths now | Prevents dangling references even though the plugin route is deferred. | Leave dangling — inconsistent and misleading. |
| Do not publish to npm | DESIGN.md explicitly states the repo does not publish skill code; Route A uses GitHub as source. | Route B (`npm install -g`) — contradicts DESIGN; adds publish/maintenance burden. |

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Plugin/marketplace routes (Claude Code, Codex, Copilot) still untested after path update. | Deferred to a later change; updating paths now is harmless and keeps the manifest consistent. |
| `.gitignore` ignores `.opencode/skills/openspec-*/` only; root `skills/` is tracked and committed. | No action needed — root `skills/` is not ignored. |
| Users who already installed via `.agents/skills/` may have stale copies. | skills.sh `update` re-fetches from the new location; documented as "pick one route" in install-block. |

## Migration Plan

1. Move each skill directory from `.agents/skills/<name>/` to `skills/<name>/` (content unchanged).
2. Delete `.agents/skills/` once empty.
3. Update `DESIGN.md`, `.agents/install-block.md`, `README.md` (gemini `--path`).
4. Update `.claude-plugin/plugin.json` (5 skill paths).
5. Verify with `npx skills@latest add S-Dawn/ResumeBuilder --list`.

Rollback: move `skills/` back to `.agents/skills/` and revert path references.

## Open Questions

None — all decisions (flat layout, root `skills/`, deferred plugin route, update plugin.json now) are resolved.
