# Development Guide

## Principles

LeadFlow V1 follows four rules:

1. Keep qualification deterministic and explainable.
2. Keep communication generation separate from scoring authority.
3. Do not fake external integrations.
4. Add tests for any behavior-changing rule.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

## Useful checks

```bash
python -m compileall -q app tests scripts
python -m pip check
python -m pytest -q
python scripts/demo.py
```

## Architecture boundaries

- `app/models.py`: request/response contracts
- `app/scoring.py`: deterministic qualification authority
- `app/followup.py`: communication draft generation
- `app/storage.py`: persistence
- `app/main.py`: HTTP composition layer
- `static/index.html`: browser interface

Do not place provider credentials, production lead data, or local database files in the repository.

## Change discipline

A scoring-rule change should include:

- rationale
- expected score/routing effect
- boundary cases
- regression tests
- README/docs update if user-visible behavior changes
