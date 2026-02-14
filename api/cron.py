"""
Vercel Cron Job — triggers a daily redeployment via Deploy Hook.

Set the VERCEL_DEPLOY_HOOK env var to your Deploy Hook URL
(create one in Vercel Dashboard → Project → Settings → Git → Deploy Hooks).
"""
import json
import logging
import os
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Verify the request comes from Vercel Cron (optional security)
        auth = self.headers.get("Authorization", "")
        cron_secret = os.getenv("CRON_SECRET", "")
        if cron_secret and auth != f"Bearer {cron_secret}":
            self._respond(401, {"error": "Unauthorized"})
            return

        deploy_hook = os.getenv("VERCEL_DEPLOY_HOOK", "")
        if not deploy_hook:
            self._respond(500, {"error": "VERCEL_DEPLOY_HOOK env var not set"})
            return

        try:
            req = Request(deploy_hook, method="POST", data=b"")
            with urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read())
                logger.info("Deploy triggered: %s", body)
                self._respond(200, {"success": True, "deploy": body})
        except Exception as e:
            logger.error("Failed to trigger deploy: %s", e, exc_info=True)
            self._respond(500, {"error": str(e)})

    def _respond(self, status: int, body: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, indent=2).encode())
