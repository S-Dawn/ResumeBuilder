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
`resumebuilder-skills.config.json` (gitignored) that the other skills read:

1. **Profile location** — where your canonical career profile lives
   (default: `profile/`).
2. **Draft output directory** — where tailored/master/market resume drafts
   are saved (default: `generated/`).
3. **ATS validation** — which validation tools to run (WeasyPrint PDF, pypdf
   text extraction, or both).

## When to reach for it

Run this the first time you use any ResumeBuilder skill in a new repo, or
whenever you want to change the profile path, output directory, or ATS
validation tools.

## How it works

0. Checks that `uv`/`uvx` is installed; if not, instructs you to install it
   (e.g., `pip install uv` or `brew install uv`) before proceeding.
1. Prompts you for each configuration value, with sensible defaults.
2. Writes `resumebuilder-skills.config.json` next to the repo root.
3. Confirms that `uvx resumebuilder-tools@1.0.0 profile-index` works
   against your profile directory.
4. Tells you which skills are now available: `/tailor-resume`,
   `/maintain-profile`, `/analyze-profile-fit`, `/update-projects`.

## It's working if

- `uv`/`uvx` is installed (or you installed it after the setup prompt).
- `resumebuilder-skills.config.json` exists at the repo root with your
  chosen values.
- `uvx resumebuilder-tools@1.0.0 profile-index` exits successfully.
- Running `/tailor-resume`, `/maintain-profile`, `/analyze-profile-fit`, or
  `/update-projects` reads the config and operates on your profile.
