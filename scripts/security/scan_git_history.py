"""Fail on high-confidence credential material anywhere in reachable Git history."""
from __future__ import annotations

import subprocess
import sys

RULES = (
    ("GitHub classic token", r"gh[pousr]_[A-Za-z0-9]{30,}"),
    ("GitHub fine-grained token", r"github_pat_[A-Za-z0-9_]{40,}"),
    ("Supabase secret key", r"sb_secret_[A-Za-z0-9_-]{20,}"),
    ("Stripe live secret", r"sk_live_[A-Za-z0-9]{16,}"),
    ("OpenAI project secret", r"sk-proj-[A-Za-z0-9_-]{20,}"),
    ("Anthropic API key", r"sk-ant-api03-[A-Za-z0-9_-]{20,}"),
    ("private key", r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ("credentialed Postgres URL", r"postgres(ql)?://[^[:space:]@]+:[^[:space:]@]+@"),
)

def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)

revs = run("git", "rev-list", "--all")
if revs.returncode != 0:
    print("Secret scan could not enumerate Git history.", file=sys.stderr)
    raise SystemExit(2)

commits = [item for item in revs.stdout.split() if item]
if not commits:
    print("Secret scan found no reachable commits.", file=sys.stderr)
    raise SystemExit(2)

findings: list[tuple[str, str]] = []
for name, pattern in RULES:
    for commit in commits:
        result = run("git", "grep", "-I", "-q", "-E", "-e", pattern, commit, "--", ".")
        if result.returncode == 0:
            findings.append((name, commit))
            break
        if result.returncode != 1:
            print(f"Secret scan failed while checking {name}.", file=sys.stderr)
            raise SystemExit(2)

if findings:
    print("Potential credential material exists in reachable Git history.", file=sys.stderr)
    for name, commit in findings:
        print(f"- {name}: candidate found in commit {commit[:12]}", file=sys.stderr)
    print("Values are suppressed. Review and rotate/revoke before promotion.", file=sys.stderr)
    raise SystemExit(1)

print(f"Secret-history scan passed: {len(commits)} reachable commits checked across {len(RULES)} high-confidence credential classes.")
