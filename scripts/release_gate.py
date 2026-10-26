"""Offline checkout audit for a demo candidate. NOT a production certification."""
from __future__ import annotations

import ast
import json
from pathlib import Path

PROJECT="Project 6 LeadFlow"
EXPECTED_ROUTES=["/health","/api/leads","/api/outbox"]
REQUIRED_FILES=("README.md", "requirements.txt", "app/main.py")

def app_routes(source: str) -> set[str]:
    tree=ast.parse(source)
    routes=set()
    for node in ast.walk(tree):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator,ast.Call) or not isinstance(decorator.func,ast.Attribute):
                continue
            receiver=decorator.func.value
            if (not isinstance(receiver,ast.Name) or receiver.id!="app"
                    or decorator.func.attr not in {"get","post","patch","put","delete"}):
                continue
            if decorator.args and isinstance(decorator.args[0],ast.Constant) and isinstance(decorator.args[0].value,str):
                routes.add(decorator.args[0].value)
    return routes

def inspect_checkout(root: Path) -> dict:
    root=Path(root)
    missing=[p for p in REQUIRED_FILES if not (root/p).is_file()]
    routes=app_routes((root/"app/main.py").read_text(encoding="utf-8")) if not missing else set()
    missing_routes=sorted(set(EXPECTED_ROUTES)-routes)
    test_files=list((root/"tests").rglob("test_*.py")) if (root/"tests").is_dir() else []
    workflows=[* (root/".github/workflows").glob("*.yml"),* (root/".github/workflows").glob("*.yaml")] if (root/".github/workflows").is_dir() else []
    checks={
        "required_files_present":not missing,
        "documented_routes_present":not missing_routes,
        "regression_tests_present":bool(test_files),
        "ci_workflow_present":bool(workflows),
    }
    return {
        "schema":"portfolio-local-demo-preflight-v1",
        "project":PROJECT,
        "status":"CHECKOUT_CONTRACT_PASS" if all(checks.values()) else "CHECKOUT_CONTRACT_FAIL",
        "checks":checks,
        "missing_files":missing,
        "missing_routes":missing_routes,
        "local_demo_only":True,
        "public_deployment_authorized":False,
        "customer_data_authorized":False,
        "revenue_readiness_proven":False,
        "next_verification":[
            "Run the complete repository test and security suites in CI.",
            "Perform operator-browser acceptance and isolated persistence checks.",
            "Require authentication, tenant isolation, backup/restore, rate limits and privacy review before customer data.",
            "Obtain explicit approval for any hosted migration, paid service, or production change.",
        ]
    }

def main() -> None:
    result=inspect_checkout(Path(__file__).resolve().parents[1])
    print(json.dumps(result,indent=2))
    if result["status"]!="CHECKOUT_CONTRACT_PASS":
        raise SystemExit(1)

if __name__=="__main__":
    main()
