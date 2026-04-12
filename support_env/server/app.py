# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Customer Support Triage Environment.

Endpoints created automatically by create_app():
    - POST /reset   → Reset the environment
    - POST /step    → Execute an action
    - GET  /state   → Get current environment state
    - GET  /health  → Health check
    - WS   /ws      → WebSocket for persistent sessions

Usage:
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core"
    ) from e

try:
    from ..models import SupportAction, SupportObservation
except (ImportError, ModuleNotFoundError):
    from models import SupportAction, SupportObservation

from .support_env_environment import SupportEnvironment


# Create the app — this generates all REST + WebSocket endpoints
app = create_app(
    SupportEnvironment,
    SupportAction,
    SupportObservation,
    env_name="support_env",
    max_concurrent_envs=10,  # allow up to 10 concurrent sessions
)

from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html><head><title>Support Env</title></head>
<body style="font-family:sans-serif;max-width:700px;margin:60px auto;padding:20px">
<h1>🏢 Customer Support Triage Environment</h1>
<p>This is an OpenEnv environment for the Meta PyTorch Hackathon.</p>
<h3>API Endpoints</h3>
<ul>
<li><code>POST /reset</code> — Reset environment</li>
<li><code>POST /step</code> — Execute an action</li>
<li><code>GET /state</code> — Current state</li>
<li><code>GET /health</code> — Health check</li>
</ul>
<p>Status: ✅ Running</p>
</body></html>"""


def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution.

    Run with:
        uv run --project . server
        python -m support_env.server.app
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
