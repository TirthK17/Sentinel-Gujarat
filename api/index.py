"""
Vercel Serverless Function Entrypoint for Drishti CCTV Intelligence Platform.
Restores original route path using deterministic query param or Vercel edge headers.
"""
import os
import sys
import urllib.parse
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Mark serverless environment
os.environ.setdefault("VERCEL", "1")

from backend.app.main import app as base_app

class VercelPathFixer:
    """
    ASGI middleware that deterministically restores original request path
    on Vercel serverless functions.
    """
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            qs_bytes = scope.get("query_string", b"")
            qs_str = qs_bytes.decode("latin1", errors="replace")
            params = urllib.parse.parse_qs(qs_str)
            
            # 1. Check deterministic __path passed via vercel.json rewrite
            if "__path" in params and params["__path"]:
                target_path = params["__path"][0]
                scope["path"] = target_path
                scope["raw_path"] = target_path.encode("utf-8")
                # Clean __path out of query string
                remaining = {k: v for k, v in params.items() if k != "__path"}
                new_qs = urllib.parse.urlencode(remaining, doseq=True)
                scope["query_string"] = new_qs.encode("latin1")
            else:
                # 2. Fallback to header inspection
                headers = {k.decode("latin1").lower(): v.decode("latin1") for k, v in scope.get("headers", [])}
                original = (
                    headers.get("x-matched-path")
                    or headers.get("x-vercel-matched-path")
                    or headers.get("x-forwarded-uri")
                )
                if original and not original.startswith("/api/index"):
                    clean = original.split("?")[0]
                    scope["path"] = clean
                    scope["raw_path"] = clean.encode("utf-8")

        await self.asgi_app(scope, receive, send)

app = VercelPathFixer(base_app)
handler = app
