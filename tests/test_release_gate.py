"""Checks that the release preflight never asserts revenue or production readiness."""
from pathlib import Path

from scripts.release_gate import app_routes, inspect_checkout

ROOT = Path(__file__).resolve().parents[1]

def test_checkout_contract_and_explicit_hard_stops():
    result = inspect_checkout(ROOT)
    assert result["status"] == "CHECKOUT_CONTRACT_PASS", result
    assert result["local_demo_only"] is True
    assert result["public_deployment_authorized"] is False
    assert result["customer_data_authorized"] is False
    assert result["revenue_readiness_proven"] is False

def test_route_detector_ignores_fake_paths_in_strings_and_comments():
    source = """
const = 'app.get("/fake")'
# @app.get("/fake-comment")
from fastapi import FastAPI
app = FastAPI()
@app.get("/real")
def fn():
    return {}
"""
    assert app_routes(source) == {"/real"}
