Task ID: P6-REFRESH-BROWSER-VERIFICATION-2026-10-12
Title: Verify the operator Refresh control in actual Chromium
Status: READY_FOR_AJ
Risk Tier: TIER_1
Base SHA: c1057738434e0ec0ba4166745bff00c5de7623c7

## Objective
Complete the missing real browser regression for the existing refresh correction on PR #21.

## Authorized implementation paths
- .codex/CURRENT_TASK.md
- .github/workflows/ci.yml
- .github/workflows/security-monitor.yml

## Authorized test paths
- tests/refresh.browser.cjs
- tests/test_api.py

## Acceptance criteria
- Actual Chromium clicks reload a lead created through the real local API and temporary SQLite database.
- Empty, loading, duplicate click, HTTP/JSON/network failures and subsequent recovery behave correctly.
- Failed requests preserve the prior queue; untrusted text renders escaped.
- Keyboard activation, live status and mobile control visibility pass.
- Existing Python suite, compile, pip health, dependency audit, security and exact-head CI pass.
- Owner Lenovo retest remains separately NOT_RUN until performed.

## Explicit non-goals
- No provider execution, outbound sends, auth, lead logic, hosted changes, secrets, main merge or deployment.

## Required gates
- CI including the real loopback browser test; Security Monitor; scoped read-only review.

## Local verification limitation
Local Python tests/compile/pip health pass. Chromium download in this session returned an invalid archive; real browser acceptance must be observed in CI. Browser tooling installs only in ephemeral runner storage, not application dependencies.

## Source verification
The browser/API/SQLite regression passed in CI 38318157515 on the prior source revision. Final workflows now explicitly check out the PR head, avoiding implicit merge-ref evidence. All final-candidate gates must pass before delivery; owner device acceptance remains separate.
