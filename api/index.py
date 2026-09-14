"""
Vercel Serverless Function Entrypoint for Drishti CCTV Intelligence Platform.
Restores request scope path from Vercel rewrite headers.
"""
import os
import sys
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
    ASGI middleware to ensure request paths and query parameters
    route correctly inside Vercel's serverless environment.
    """
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            headers = {k.decode("latin1").lower(): v.decode("latin1") for k, v in scope.get("headers", [])}
            
            original_path = (
                headers.get("x-matched-path")
                or headers.get("x-vercel-matched-path")
                or headers.get("x-forwarded-uri")
                or headers.get("x-now-route-matches")
            )
            
            curr_path = scope.get("path", "")
            if original_path and not original_path.startswith("/api/index"):
                clean_path = original_path.split("?")[0]
                scope["path"] = clean_path
                scope["raw_path"] = clean_path.encode("utf-8")
            elif curr_path in ("/api/index.py", "/api/index", "/api"):
                scope["path"] = "/"

        await self.asgi_app(scope, receive, send)

app = VercelPathFixer(base_app)
handler = app
