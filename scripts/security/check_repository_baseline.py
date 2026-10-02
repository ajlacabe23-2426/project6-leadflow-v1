"""Validate repository security posture using only the Python standard library."""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path.cwd()
failures: list[str] = []

def fail(message: str) -> None:
    failures.append(message)

tracked = subprocess.run(["git", "ls-files", "-z"], text=True, capture_output=True, check=False)
if tracked.returncode != 0:
    print("Repository baseline could not enumerate tracked files.", file=sys.stderr)
    raise SystemExit(2)
files = [item for item in tracked.stdout.split("\0") if item]

env_like = re.compile(r"(^|/)\.env(?:\.[^/]+)?$", re.I)
allowed_env = re.compile(r"(^|/)\.env(?:\.[^/]+)?\.example$|(^|/)\.env\.example$", re.I)
key_like = re.compile(r"(^|/)(id_rsa|id_ed25519)(\.|$)|\.(pem|key|p12|pfx)$", re.I)
for item in files:
    normalized = item.replace("\\", "/")
    if key_like.search(normalized):
        fail(f"Tracked secret-like key material is not allowed: {normalized}")
    if env_like.search(normalized) and not allowed_env.search(normalized):
        fail(f"Tracked environment file is not allowed: {normalized}")

workflows = [item for item in files if re.match(r"^\.github/workflows/.*\.ya?ml$", item, re.I)]
if not workflows:
    fail("No tracked GitHub Actions workflows were found.")

for item in workflows:
    source = (ROOT / item).read_text(encoding="utf-8")
    if re.search(r"^\s*pull_request_target\s*:", source, re.M):
        fail(f"{item} uses pull_request_target, which is prohibited.")
    if re.search(r"^\s*permissions\s*:\s*write-all\s*$", source, re.M):
        fail(f"{item} grants permissions: write-all.")
    if not re.search(r"^permissions\s*:\s*$", source, re.M):
        fail(f"{item} must declare explicit top-level permissions.")
    for action in re.findall(r"^\s*uses:\s*([^\s#]+)", source, re.M):
        if action.startswith("./"):
            continue
        ref = action.rsplit("@", 1)[-1] if "@" in action else ""
        if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
            fail(f"{item} uses an unpinned remote action: {action}")
    lines = source.splitlines()
    for index, line in enumerate(lines):
        if re.search(r"uses:\s*actions/checkout@[0-9a-fA-F]{40}", line):
            nearby = "\n".join(lines[index + 1:index + 12])
            if not re.search(r"persist-credentials:\s*false", nearby, re.I):
                fail(f"{item} checkout must set persist-credentials: false.")

required = (
    ".github/dependabot.yml",
    ".github/workflows/security-monitor.yml",
    "SECURITY.md",
    "scripts/security/scan_git_history.py",
    "scripts/security/check_repository_baseline.py",
)
for item in required:
    if item not in files:
        fail(f"Required security control is missing: {item}")

dependabot_path = ROOT / ".github/dependabot.yml"
if dependabot_path.exists():
    dependabot = dependabot_path.read_text(encoding="utf-8")
    for ecosystem in ("pip", "github-actions"):
        if not re.search(rf"package-ecosystem:\s*[\"']?{re.escape(ecosystem)}[\"']?", dependabot):
            fail(f"Dependabot coverage is missing for {ecosystem}.")

if failures:
    print("Repository security baseline failed:", file=sys.stderr)
    for message in failures:
        print(f"- {message}", file=sys.stderr)
    raise SystemExit(1)

print(f"Repository security baseline passed: {len(files)} tracked files checked.")
