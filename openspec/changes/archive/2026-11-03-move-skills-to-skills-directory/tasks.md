## 1. Relocate distributable skills

- [x] 1.1 Move `tailor-resume/` from `.agents/skills/` to `skills/`
- [x] 1.2 Move `maintain-profile/` from `.agents/skills/` to `skills/`
- [x] 1.3 Move `analyze-profile-fit/` from `.agents/skills/` to `skills/`
- [x] 1.4 Move `update-projects/` from `.agents/skills/` to `skills/`
- [x] 1.5 Move `setup-resumebuilder-skills/` from `.agents/skills/` to `skills/`
- [x] 1.6 Delete `.agents/skills/` directory once empty

## 2. Update path references

- [x] 2.1 Update `DESIGN.md`: skills live under `skills/`; install routes table (gemini `--path skills/`); "Files to create / modify" table
- [x] 2.2 Update `.agents/install-block.md`: gemini `--path .opencode/skills` → `--path skills/`
- [x] 2.3 Update `README.md`: gemini `--path .opencode/skills` → `--path skills/`
- [x] 2.4 Update `.claude-plugin/plugin.json`: 5 skill paths from `./.opencode/skills/...` to `./skills/...`

## 3. Verify

- [x] 3.1 Run `npx skills@latest add S-Dawn/ResumeBuilder --list` and confirm all 5 skills surface
- [x] 3.2 Confirm no dangling references to `.opencode/skills/` for distributable skills remain
