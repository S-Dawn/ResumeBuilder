---
name: setup-resumebuilder-skills
description: Configure this repo for the ResumeBuilder skills (profile path, output dir, ATS validation). Run once per repo before using the other skills.
disable-model-invocation: true
compatibility: Requires Python and uv/uvx to invoke the resumebuilder-tools engine package from PyPI.
---

# Set up ResumeBuilder skills

Run this skill once per repository to configure the ResumeBuilder skills
(`tailor-resume`, `maintain-profile`, `analyze-profile-fit`,
`update-projects`) for your environment.

## What it does

Asks you for three pieces of configuration and writes them into a local
`resumebuilder-skills.config.json` (gitignored):

1. **Profile location** — the `profile_dir` path for your canonical career
   profile (default: `profile/`).
2. **Draft output directory** — the `generated_dir` path for tailored/master/
   market resume drafts (default: `generated/`).
3. **ATS validation** — which validation tools to run (WeasyPrint PDF, pypdf
   text extraction, or both).

The config contains `profile_dir` and `generated_dir` string values. Relative
paths are resolved from the directory containing the config file. For example:

```json
{
  "profile_dir": "career/profile",
  "generated_dir": "output/resumes"
}
```

The engine searches the current directory and its parents for this config.
Commands run from that workspace automatically use these paths unless an
explicit path option overrides them. Without a config file, paths default to
`profile/` and `generated/` in the current directory.

## When to reach for it

Run this the first time you use any ResumeBuilder skill in a new repo, or
whenever you want to change the profile path, output directory, or ATS
validation tools.

## How it works

0. Checks that `uv`/`uvx` is installed; if not, instructs you to install it
   (e.g., `pip install uv` or `brew install uv`) before proceeding.
1. Prompts you for each configuration value, with sensible defaults.
2. Writes `resumebuilder-skills.config.json` next to the repo root.
3. Confirms that `./scripts/resume-tools profile-index` works
   against your configured profile directory.
4. Tells you which skills are now available: `/tailor-resume`,
   `/maintain-profile`, `/analyze-profile-fit`, `/update-projects`.

## It's working if

- `uv`/`uvx` is installed (or you installed it after the setup prompt).
- `resumebuilder-skills.config.json` exists at the repo root with your
  chosen values.
- `./scripts/resume-tools profile-index` exits successfully.
- Running `/tailor-resume`, `/maintain-profile`, `/analyze-profile-fit`, or
  `/update-projects` reads the config and operates on your profile.
