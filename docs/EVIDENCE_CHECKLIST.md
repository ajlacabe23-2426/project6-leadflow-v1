# Evidence Checklist

## Repository evidence

- [ ] GitHub Actions CI is green.
- [x] Nine tests pass in independent execution.
- [x] Runtime SQLite database is ignored.
- [x] README accurately distinguishes V1 from deferred integrations.
- [x] Security boundary is documented.
- [x] V2 integration risks are documented.

## Runtime evidence

- [x] `GET /health` returns `status: ok`.
- [ ] Intake form visual/browser smoke test captured.
- [x] A complete sample lead is accepted.
- [x] Sample lead scores 100/100.
- [x] Sample lead routes to `qualified`.
- [x] Priority is `high`.
- [x] Next action is `human-priority-review`.
- [x] Follow-up draft is generated.
- [x] Lead appears in operator queue API.
- [x] SQLite persistence path is exercised.

## Failure / edge evidence

- [x] Missing value/timeline routes to `needs-info`.
- [x] Low-intent complete lead routes to `nurture`.
- [x] Invalid email is rejected by the API contract.
- [x] Score breakdown sums to final score.
- [x] Repeating the same input returns the same qualification result.

## Still useful to capture manually

- [ ] Screenshot of lead-intake form.
- [ ] Screenshot of 100/100 result.
- [ ] Screenshot of operator queue.
- [ ] Screenshot of GitHub Actions green run.
