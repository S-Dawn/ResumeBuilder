# ResumeBuilder

Turn your career history into a stronger, role-ready resume—without losing sight of the evidence behind every claim. ResumeBuilder brings a suite of AI agent skills and a Python engine together to help you build a reusable career profile, evaluate how your experience maps to a job, and create tailored, master, or market-focused resumes. Use the skills in the agent runtime you prefer—including Claude Code, Codex, OpenCode, GitHub Copilot, and more. Every draft is traceable to your profile, validated, and ready for your review.

You stay in control: ResumeBuilder never invents qualifications or submits applications on your behalf.

## Install the skills

Install the skills in the project where you want to use them. ResumeBuilder supports a range of agent runtimes, including Claude Code, Codex, OpenCode, and GitHub Copilot. Use the runtime's native plugin route when available, or install with skills.sh. To choose an agent interactively with skills.sh:

```bash
npx skills@latest add S-Dawn/ResumeBuilder
```

Or select an agent explicitly:

```bash
npx skills@latest add S-Dawn/ResumeBuilder -a <agent>
```

When prompted to select skills, install `setup-resumebuilder-skills` along with the skills you plan to use. You can install one skill by name:

```bash
npx skills@latest add S-Dawn/ResumeBuilder --skill=setup-resumebuilder-skills
```

The skills.sh installer installs skill files for the agent you select. To update installed skills, run:

```bash
npx skills@latest update
npx skills@latest add S-Dawn/ResumeBuilder
```

This route uses manual updates. The repository also supports agent-native plugin installation routes; see [the install guide](.agents/install-block.md) for those options.

## Onboard a project

Set up ResumeBuilder once in each project where you plan to use it:

1. Open that project in your agent and run `/setup-resumebuilder-skills`.
2. Follow the prompts to choose the canonical profile directory (default: `profile/`), draft output directory (default: `generated/`), and PDF/ATS validation tools.
3. Make sure `uv` is installed. The setup skill uses `uvx` to run the published `resumebuilder-tools` engine. It writes `resumebuilder-skills.config.json` in the project root; the file is gitignored.
4. Add or maintain your career profile in the configured profile directory. See [profile/README.md](profile/README.md) for its record format and evidence conventions.
5. Use the relevant skill below. The profile and job-description content needed for a task may be sent to your configured agent model; the skills disclose this and request confirmation before reading files where required. Do not put secrets in your profile.

The setup skill is a per-project configuration step, not a profile editor. Run it before using the other ResumeBuilder skills.

## ResumeBuilder skills

Invoke these skills by name in your agent:

| Skill | What it does |
|---|---|
| `setup-resumebuilder-skills` | Configures profile and draft paths plus PDF validation for the current project. Run once per project, before the other skills. |
| `maintain-profile` | Consolidates a full, general resume or career facts into the canonical profile. Prepares and validates a complete proposed diff, then waits for your explicit approval before applying it. |
| `update-projects` | Adds or refines a project record, and updates the skills record when supported by the project evidence. Also previews and validates the whole change before asking for approval. |
| `analyze-profile-fit` | Compares the profile with a job description and reports evidence-backed matches, gaps, and positioning opportunities. It does not create a resume or save a report. |
| `tailor-resume` | Creates a job-tailored draft when you provide a job description; without one, helps create a complete master resume or a market-oriented resume. It renders and validates output for your review. |

### Maintaining your profile

Use `/maintain-profile` for broad updates from a full, general resume or career facts you provide. Use `/update-projects` for a focused project addition or revision. Both skills:

- Read the profile's editing contract and preserve existing supported claims.
- Ask you to resolve ambiguous or conflicting facts rather than guessing.
- Stage and validate a complete proposed change, show you the diff, and only apply it after you approve that exact diff.

Do not use a tailored application resume as the source for your canonical profile. Do not edit the generated `profile/index.yaml` by hand; it is rebuilt from profile metadata.

### Analyzing and creating resumes

- **Fit analysis:** Run `/analyze-profile-fit` with a pasted job description or a path to one. The assessment describes what the profile documents; it is not a hiring prediction and profile silence does not mean you lack a qualification.
- **Tailored resume:** Run `/tailor-resume` with a job description to create an application draft, fit report, source map, HTML, and PDF under the configured output directory. Review the content yourself; no application is submitted.
- **Master resume:** Run `/tailor-resume` without a job description and ask for a complete career archive. It includes distinct supported profile evidence and reports conflicts that need clarification.
- **Market resume:** Run `/tailor-resume` without a job description and ask for a market-oriented resume. The skill confirms a target role with you and uses current role-trend research when web search is available.

## Codebase and local development

### Repository layout

- `skills/` — installable skill instructions.
- `python_engine/` — profile, draft, validation, and PDF-rendering implementation.
- `profile/` — example canonical profile records and their format guide.
- `tests/` — Python unit tests.
- `pyproject.toml` and `uv.lock` — Python package metadata, dependencies, and lockfile.
- `.claude-plugin/` — plugin manifests for supported native installation routes.

### Set up the development environment

Requirements: Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/S-Dawn/ResumeBuilder.git
cd ResumeBuilder
uv sync
```

### Run the tests and tools

Run the test suite:

```bash
uv run python -m unittest discover -s tests
```

Show the profile and draft utility commands:

```bash
uv run python -m python_engine.resume_tools --help
```

For example, validate the profile and rebuild its compact index:

```bash
uv run python -m python_engine.resume_tools validate-profile
uv run python -m python_engine.resume_tools profile-index
```

To render a resume from a YAML file, provide that file using the renderer's schema:

```bash
uv run python -m python_engine.ResumeBuilder \
  --config path/to/resume.yaml \
  --output-dir generated/
```

Add `--strict-one-page` to require a one-page PDF with extractable text and expected headings. The renderer reads `resume.yaml` by default if `--config` is omitted. See [python_engine/ResumeBuilder.py](python_engine/ResumeBuilder.py) and [python_engine/resume_tools.py](python_engine/resume_tools.py) for implementation and CLI details.

## Contributing

Contributions are welcome. For a substantial change, open an issue first to discuss the behavior or approach. For a pull request:

1. Keep changes focused and update the relevant skill or documentation alongside code changes.
2. Run the tests with `uv run python -m unittest discover -s tests`.
3. For changes to distributable skills, include a Changesets entry so the plugin release can be versioned.
4. Describe what changed, how you tested it, and any user-facing behavior changes.

## Bug reports

Report bugs in the [GitHub issue tracker](https://github.com/S-Dawn/ResumeBuilder/issues/new/choose). Include steps to reproduce, the expected and actual behavior, the agent/OS where relevant, and any error output. Remove personal profile data, job descriptions, credentials, and other private information from reports and logs.
