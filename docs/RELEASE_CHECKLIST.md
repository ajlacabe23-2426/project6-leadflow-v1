# LeadFlow V1 Release Checklist

## Code and tests

- [x] Core qualification engine implemented.
- [x] API and persistence implemented.
- [x] 49 Python regression tests pass locally on 2026-10-19 (synthetic data).
- [x] Chromium refresh regression integrated into CI; final-branch CI still needs checking.
- [x] Refresh fix merged to `main` in PR #21; synthetic persistence acceptance merged in PR #26.
- [x] GitHub Actions CI repaired and confirmed green.
- [x] Python syntax/import check included in CI.
- [x] Dependency consistency check included in CI.
- [x] Docker build validation included in CI.

## Repository quality

- [x] Professional README.
- [x] Architecture documentation.
- [x] Security policy.
- [x] Roadmap.
- [x] API examples.
- [x] Development guide.
- [x] Deployment guide.
- [x] Interview talking points.
- [x] Evidence checklist.
- [x] Issue templates.
- [x] Docker packaging.

## Manual evidence still required

- [ ] Run application on AJ's computer.
- [ ] Capture intake-form screenshot.
- [ ] Submit complete sample lead.
- [ ] Capture 100/100 qualification screenshot.
- [ ] Capture operator queue screenshot.
- [ ] Confirm persisted lead survives restart.
- [ ] Capture final green GitHub Actions run at the exact release SHA.
- [ ] On owner device, retest Refresh and intake failure/recovery; CI cannot substitute for owner acceptance.
- [ ] Optional short demo recording.

## Production integrations intentionally not part of V1

- [ ] Real outbound email/SMS.
- [ ] Real calendar booking.
- [ ] CRM synchronization.
- [ ] Multi-tenant authentication/authorization.
- [ ] Managed production database.
- [x] Local provider-free durable outbox with idempotent claim, bounded retry and dead letter; **not** a production sender.

## Production/customer-data gate (not satisfied)

- [ ] Authenticated operator access and tenant authorization where needed.
- [ ] Managed persistence with backups, recovery evidence, and retention/deletion policy.
- [ ] Rate limiting, monitoring, incident response, and provider consent enforcement verified.
- [ ] Production deployment and all external communication side effects separately authorized and tested.

V1 can be considered **portfolio-demo ready** once the manual evidence section
is completed. It must not be described as ready for public customer-data use.
