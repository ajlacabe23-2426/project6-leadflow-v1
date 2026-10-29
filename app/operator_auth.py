"""Local/demo operator API guard; not multi-tenant customer authentication.

When LEADFLOW_OPERATOR_TOKEN is configured, sensitive operator APIs require
an exact Bearer token. LEADFLOW_REQUIRE_OPERATOR_AUTH=1 fails closed if the
token is missing or weak. Public lead intake remains separate from operator access.
"""
from __future__ import annotations

import hmac
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


def _operator_api(request: Request) -> bool:
    path = request.url.path
    return path.startswith("/api/") and not (
        path == "/api/leads" and request.method == "POST"
    )


def _authentication_expected() -> bool:
    flag = os.getenv("LEADFLOW_REQUIRE_OPERATOR_AUTH", "").strip().lower()
    environment = os.getenv("LEADFLOW_ENV", "local").strip().lower()
    return environment in {"production", "staging"} or flag not in ("", "0", "false", "no", "off")


class OperatorAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if _operator_api(request):
            token = os.getenv("LEADFLOW_OPERATOR_TOKEN", "")
            if token or _authentication_expected():
                # Do not allow an accidentally empty/weak deployment secret.
                if len(token.encode("utf-8")) < 32:
                    return JSONResponse(
                        {"detail": "Operator access is not configured"},
                        status_code=503,
                        headers={"Cache-Control": "no-store"},
                    )

                scheme, separator, credential = request.headers.get(
                    "authorization", ""
                ).partition(" ")
                authenticated = (
                    separator == " "
                    and scheme.lower() == "bearer"
                    and hmac.compare_digest(
                        credential.encode("utf-8"), token.encode("utf-8")
                    )
                )
                if not authenticated:
                    return JSONResponse(
                        {"detail": "Operator authentication required"},
                        status_code=401,
                        headers={
                            "WWW-Authenticate": "Bearer",
                            "Cache-Control": "no-store",
                        },
                    )

        response = await call_next(request)
        # Prevent browsers/intermediaries from caching lead records and API output.
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response
