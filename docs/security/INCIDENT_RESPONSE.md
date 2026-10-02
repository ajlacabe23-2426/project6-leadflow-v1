# Project 6 Incident Response

Updated: 2026-10-02

## Priorities

1. Stop unsafe promotion or outbound side effects.
2. Protect lead/customer data and credentials.
3. Preserve evidence without copying secrets into tickets or logs.
4. Restore a known-good commit and rerun deterministic verification.

## Credential or secret exposure

- Do not paste the suspected value into an issue, commit, CI log, or chat.
- Identify the provider and affected scope.
- Revoke/rotate through the provider control plane when applicable.
- Scan reachable Git history and deployment artifacts.
- Verify the old credential is invalid before closing the incident.

## Suspicious repository or workflow change

- Freeze promotion.
- Compare with the last verified main commit.
- Review Action SHAs, workflow permissions, checkout credential handling, dependency changes, outbound-action code, and storage/auth boundaries.
- Rerun the history secret scan, repository baseline, dependency audit, tests, demo smoke test, and Docker build.

## Data or automation incident

Unexpected duplicate outbound actions, state corruption, unauthorized queue access, PII leakage, or provider replay behavior is a release blocker. Preserve identifiers and timestamps without copying unnecessary customer content.

## Recovery evidence

Record affected commit, corrected commit, passing verification runs, known limitations, and any external action still requiring owner approval.
