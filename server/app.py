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
    from .support_env_environment import SupportEnvironment
except ModuleNotFoundError:
    from models import SupportAction, SupportObservation
    from server.support_env_environment import SupportEnvironment


# Create the app — this generates all REST + WebSocket endpoints
app = create_app(
    SupportEnvironment,
    SupportAction,
    SupportObservation,
    env_name="support_env",
    max_concurrent_envs=10,  # allow up to 10 concurrent sessions
)


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
