# Evidence Checklist

## Repository evidence

- [x] Nine tests pass.
- [x] GitHub Actions repair run is green.
- [x] Runtime SQLite database is ignored.
- [x] README accurately distinguishes V1 from deferred integrations.
- [x] Security boundary is documented.
- [x] V2 integration risks are documented.
- [x] Docker packaging is present.
- [x] Demo smoke script is present.
- [x] Deployment/API/development documentation is present.
- [x] Resume and interview evidence is documented.

## Runtime evidence already exercised programmatically

- [x] `GET /health` returns `status: ok`.
- [x] A complete sample lead is accepted.
- [x] Sample lead scores 100/100.
- [x] Sample lead routes to `qualified`.
- [x] Priority is `high`.
- [x] Next action is `human-priority-review`.
- [x] Follow-up draft is generated.
- [x] Lead appears in operator queue API.
- [x] SQLite persistence path is exercised.
- [x] Invalid email is rejected.
- [x] Missing value/timeline routes to `needs-info`.
- [x] Low-intent complete lead routes to `nurture`.
- [x] Score breakdown sums to final score.
- [x] Repeating the same input returns the same qualification result.

## Manual computer-oriented evidence remaining

- [ ] Run final application locally.
- [ ] Screenshot lead-intake form.
- [ ] Submit complete sample lead in browser.
- [ ] Screenshot 100/100 result.
- [ ] Screenshot operator queue.
- [ ] Restart app and visually confirm persisted lead remains.
- [ ] Screenshot final green hardened GitHub Actions run.
- [ ] Optional 30–60 second demo recording.
