# Security autofix changes

## 2026-11-03

### PR #2 — Brotli dependencies

- Updated `brotli` from 1.2.0 to 1.2.1 and `brotlicffi` from 1.2.0.1 to 1.2.1.0.
- Dependabot findings: 114 and 115.
- Validation passed: `poetry check --lock`, both `poetry show` version checks, all 30 unit tests, and profile validation (26 records, 174 record/evidence IDs).

### PR #3 — Pillow security updates

- Updated the lockfile with Pillow 13.0.0 for Python 3.13+ and Pillow 12.3.0 for Python versions below 3.13.
- Dependabot findings: 101, 113, 120, 34, and 35.
- Validation passed: `poetry check --lock`, `poetry show pillow`, all 30 unit tests, and profile validation (26 records, 174 record/evidence IDs).

### PR #4 — pypdf

- Raised the `pypdf` constraint from `^5.4.0` to `^6.21.3`; Poetry resolved version 6.21.4.
- Dependabot findings: 116, 117, 118, 121, and 122.
- Validation passed: `poetry check --lock`, `poetry show pypdf`, all 30 unit tests, and profile validation (26 records, 174 record/evidence IDs).

### PR #5 — Pillow 13 and Python support

- Raised the minimum supported Python version from 3.10 to 3.11 and constrained Pillow to `^13.0`, removing Pillow 12.3.0 from the supported lock resolution.
- Dependabot findings: 103, 104, 106, 107, and 108.
- Validation passed: `poetry check --lock`, `poetry show pillow`, all 30 unit tests, and profile validation (26 records, 174 record/evidence IDs) on Python 3.14.4.
