# Evidence Checklist

## Repository evidence

- [ ] GitHub Actions CI is green.
- [ ] Six tests pass.
- [ ] No secrets are committed.
- [ ] Runtime SQLite database is ignored.
- [ ] README accurately distinguishes V1 from deferred integrations.

## Runtime evidence

- [ ] `GET /health` returns `status: ok`.
- [ ] Intake form loads.
- [ ] A complete sample lead is accepted.
- [ ] Sample lead scores 100/100.
- [ ] Sample lead routes to `qualified`.
- [ ] Priority is `high`.
- [ ] Next action is `human-priority-review`.
- [ ] Follow-up draft is generated.
- [ ] Lead appears in operator queue.
- [ ] Refresh/restart preserves the lead in SQLite.

## Failure / edge evidence

- [ ] Missing value/timeline routes to `needs-info`.
- [ ] Low-intent complete lead routes to `nurture`.
- [ ] Invalid email is rejected by the API contract.
- [ ] Score breakdown sums to final score.
- [ ] Repeating the same input returns the same qualification result.
