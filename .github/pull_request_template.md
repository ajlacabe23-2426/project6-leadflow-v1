## What changed

Describe the scoped change.

## Why

Explain the problem being solved.

## Verification

- [ ] `python -m compileall -q app tests scripts`
- [ ] `python -m pip check`
- [ ] `python -m pytest -q`
- [ ] Docker build passes when packaging is affected.

## Safety / boundaries

- [ ] No secrets or production PII added.
- [ ] Scoring/routing changes are explicitly documented and tested.
- [ ] No fake external integration behavior introduced.
- [ ] Human-review boundary remains intentional.
