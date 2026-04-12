# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Client for the Customer Support Triage Environment.

Translates between typed Python models and the JSON wire format
used by the WebSocket / HTTP transport.
"""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

from .models import SupportAction, SupportObservation, SupportState


class SupportEnv(
    EnvClient[SupportAction, SupportObservation, SupportState]
):
    """
    Client for the Customer Support Triage Environment.

    Example:
        >>> with SupportEnv(base_url="http://localhost:8000").sync() as env:
        ...     obs = env.reset(task="easy")
        ...     result = env.step(SupportAction(action_type="read_ticket"))
        ...     print(result.observation.ticket_body)
    """

    def _step_payload(self, action: SupportAction) -> Dict:
        """Convert a SupportAction into a JSON-serialisable dict."""
        return {
            "action_type": action.action_type,
            "message": action.message,
        }

    def _parse_result(self, payload: Dict) -> StepResult[SupportObservation]:
        """Parse the server's JSON response into a typed StepResult."""
        obs_data = payload.get("observation", {})
        observation = SupportObservation(
            done=payload.get("done", False),
            reward=payload.get("reward"),
            ticket_id=obs_data.get("ticket_id", ""),
            ticket_subject=obs_data.get("ticket_subject", ""),
            ticket_body=obs_data.get("ticket_body", ""),
            ticket_category=obs_data.get("ticket_category", ""),
            ticket_priority=obs_data.get("ticket_priority", ""),
            ticket_sentiment=obs_data.get("ticket_sentiment", ""),
            customer_response=obs_data.get("customer_response", ""),
            feedback=obs_data.get("feedback", ""),
            tickets_remaining=obs_data.get("tickets_remaining", 0),
            current_task=obs_data.get("current_task", ""),
            steps_taken=obs_data.get("steps_taken", 0),
            max_steps=obs_data.get("max_steps", 0),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> SupportState:
        """Parse server state response into a typed SupportState."""
        return SupportState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            current_task=payload.get("current_task", "easy"),
            tickets_completed=payload.get("tickets_completed", 0),
            total_tickets=payload.get("total_tickets", 0),
            cumulative_score=payload.get("cumulative_score", 0.0),
        )
