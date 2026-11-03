# Publishing `resumebuilder-tools` to PyPI

A step-by-step guide for first-time PyPI publishers using **GitHub Actions trusted publishing (OIDC)** — no API tokens or passwords required.

---

## What you'll do, in short

1. Create a free PyPI account (if you don't have one)
2. Create the `resumebuilder-tools` project on PyPI
3. Connect PyPI to this GitHub repository via trusted publishing (OIDC)
4. Push a git tag to trigger the automated build + publish workflow
5. Verify the package installs with `uvx`

---

## Prerequisites

You need:
- A GitHub account with write access to `S-Dawn/ResumeBuilder`
- A PyPI account (free)
- About 15–30 minutes

No Python packaging experience is assumed.

---

## Step 1: Create a PyPI account

1. Go to https://pypi.org/account/register/
2. Fill in your email, username, and password
3. Check your email for the verification message and click the link
4. Sign in to https://pypi.org/ to confirm your account is active

> **Tip:** Use the same email address you use for GitHub — it makes things easier, though it's not required.

---

## Step 2: Create the `resumebuilder-tools` project on PyPI

1. Sign in to https://pypi.org/
2. Click your username (top right) → **Account settings**
3. In the left sidebar, click **Projects**
4. Click **Create project**
5. Fill in:
   - **Project name:** `resumebuilder-tools`
   - **Description:** (optional) Profile-driven ATS-friendly resume generator engine for ResumeBuilder agent skills.
6. Click **Create project**

> **Important:** The name `resumebuilder-tools` must be available on PyPI. If someone already took it, you'll need a different name and update `pyproject.toml` accordingly.

---

## Step 3: Configure trusted publishing (OIDC)

Trusted publishing lets GitHub Actions publish to PyPI on your behalf without you creating or storing an API token.

### 3a. Get PyPI to trust your GitHub repository

1. On PyPI, go to your **Account settings** → **Trusted publishers** (left sidebar)
2. Click **Add trusted publisher**
3. Fill in:
   - **Publisher:** GitHub
   - **Owner:** `S-Dawn`
   - **Repository:** `ResumeBuilder`
   - **Workflow name:** `release.yml` (exact filename in `.github/workflows/`)
   - **Environment:** (leave blank unless you use GitHub Environments)
4. Click **Add trusted publisher**

You should now see `S-Dawn/ResumeBuilder` → `release.yml` listed under trusted publishers.

### 3b. Verify the GitHub Actions workflow already exists

I already added a `publish-python` job to `.github/workflows/release.yml` in this change. It looks like:

```yaml
publish-python:
    name: Publish Python engine to PyPI
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    permissions:
      contents: read
      id-token: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install uv
        uses: astral-sh/setup-uv@v3
      - name: Build and publish to PyPI
        run: |
          uv build
          uv publish
```

Key points:
- `if: github.event_name == 'release'` — it only runs when you publish a GitHub release, not on every push
- `id-token: write` — grants the workflow an OIDC token that PyPI trusts
- `uv publish` — reads the trusted publisher config from PyPI and uploads the built package

---

## Step 4: Publish version 1.0.0

Since trusted publishing is now configured, publishing is just a git tag away.

### 4a. Make sure everything is committed

```bash
git status
```

You should see the changes from this implementation session:
- `python_engine/` (new)
- `pyproject.toml` (modified)
- `uv.lock` (new)
- `poetry.lock` (deleted)
- `.github/workflows/release.yml` (modified)
- `skills/*` (modified)
- `openspec/changes/publish-python-engine-to-pypi/*` (new)

Commit them:

```bash
git add -A
git commit -m "feat: publish Python engine to PyPI via uv"
```

### 4b. Create and push a release tag

```bash
git tag v1.0.0
git push origin v1.0.0
```

### 4c. Watch the workflow run

1. Go to https://github.com/S-Dawn/ResumeBuilder/actions
2. You should see a workflow called **"Publish Python engine to PyPI"** start running
3. Click into it to watch the steps:
   - Checkout → Setup Python → Install uv → Build and publish to PyPI
4. When it finishes successfully, the package is live on PyPI

> **Note:** If the workflow fails, check the "Publish Python engine to PyPI" job logs. Common causes: trusted publisher not yet active on PyPI, project name mismatch, or permissions issue.

---

## Step 5: Verify the package installed correctly

On your local machine (or any machine with `uv` installed):

```bash
# Install uv if you don't have it
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uvx resumebuilder-tools@1.0.1 --help
```

You should see the CLI help with all subcommands:
- `profile-index`
- `create-draft`
- `render`
- `validate-profile`
- `stage-profile-update`
- `promote-profile-update`
- `discard-profile-update`

You can also check the package on PyPI at:
https://pypi.org/project/resumebuilder-tools/

---

## Step 6: How future updates work

Once trusted publishing is set up, you never touch PyPI manually again:

1. Make changes to `python_engine/` or bump the version in `pyproject.toml`
2. Push the changes to `main`, create a GitHub Release for the matching tag (for example, `v1.0.2`), and publish the release
3. The release-triggered GitHub Actions workflow automatically builds and publishes
4. Skills using `uvx resumebuilder-tools@1.0.2` will pick it up

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| Workflow fails: "no trusted publisher found" | Trusted publisher not added on PyPI, or workflow name mismatch | Double-check Step 3a; workflow filename must be exactly `release.yml` |
| Workflow fails: "project name not found" | Project `resumebuilder-tools` not created on PyPI | Complete Step 2 |
| `uvx resumebuilder-tools@1.0.1 --help` says package not found | Publish hasn't finished, or version mismatch | Wait for the workflow to complete; check https://pypi.org/project/resumebuilder-tools/ |
| ImportError when running locally | Running `resume_tools.py` directly instead of as a module | Use `uv run -m python_engine.resume_tools <command>` or `uvx resumebuilder-tools@1.0.1 <command>` |

---

## Files changed in this publishing setup

| File | What it does |
|------|-------------|
| `pyproject.toml` | Defines the `resumebuilder-tools` package, dependencies, and console script entry point |
| `python_engine/__init__.py` | Makes `python_engine` a Python package |
| `python_engine/resume_tools.py` | The engine code (moved from repo root, relative import fixed) |
| `uv.lock` | Locked dependency resolution (replaces `poetry.lock`) |
| `.github/workflows/release.yml` | Contains the `publish-python` job that builds and publishes on release tags |

---

## Summary

You now have a fully automated PyPI publishing pipeline:
- **No API tokens** — trusted publishing via OIDC
- **No manual builds** — GitHub Actions builds and publishes on release tags
- **Version-pinned skills** — your agent skills invoke `uvx resumebuilder-tools@1.0.1`, so they always get a known, tested engine version
