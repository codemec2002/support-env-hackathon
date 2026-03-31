# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Customer Support Triage Environment.

This environment simulates a Tier-1 customer support workflow.
An AI agent receives customer tickets and must triage them by:
  - Reading ticket details
  - Requesting additional information from the customer
  - Resolving tickets (with a resolution message)
  - Escalating tickets to a senior agent

The environment grades the agent on accuracy, efficiency, and policy compliance.
"""

from typing import List, Optional, Dict, Any
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field


# ---------------------------------------------------------------------------
# ACTION — what the AI agent can do each turn
# ---------------------------------------------------------------------------

class SupportAction(Action):
    """
    One action the agent takes per step.

    Allowed action_type values:
        - "read_ticket"   → Read the current ticket details (no extra fields needed)
        - "request_info"  → Ask the customer a clarifying question
        - "resolve"       → Close the ticket with a resolution
        - "escalate"      → Pass the ticket to a senior support agent

    Fields:
        action_type: One of the four action types above.
        message: Required for "request_info" and "resolve" actions.
                 For request_info: the question to ask the customer.
                 For resolve: the resolution summary given to the customer.
    """

    action_type: str = Field(
        ...,
        description="One of: read_ticket, request_info, resolve, escalate",
    )
    message: str = Field(
        default="",
        description="Message for request_info (question) or resolve (resolution summary)",
    )


# ---------------------------------------------------------------------------
# OBSERVATION — what the environment sends back to the agent after each action
# ---------------------------------------------------------------------------

class SupportObservation(Observation):
    """
    Observation returned after every step.

    Fields (in addition to base `done`, `reward`):
        ticket_id:          Unique ID of the current ticket.
        ticket_subject:     Short subject line of the ticket.
        ticket_body:        Full customer message (visible after read_ticket).
        ticket_category:    Ground-truth category (hidden from agent, shown after done).
        ticket_priority:    "low", "medium", or "high".
        ticket_sentiment:   "positive", "neutral", or "negative".
        customer_response:  Reply from the simulated customer (after request_info).
        feedback:           System feedback on the action the agent just took.
        tickets_remaining:  How many tickets are left in the queue.
        current_task:       Which graded task is active ("easy", "medium", "hard").
        steps_taken:        Number of steps used so far on this ticket.
        max_steps:          Maximum steps allowed per ticket.
    """

    ticket_id: str = Field(default="", description="Current ticket ID")
    ticket_subject: str = Field(default="", description="Ticket subject line")
    ticket_body: str = Field(default="", description="Full ticket body (after read)")
    ticket_category: str = Field(default="", description="Ticket category")
    ticket_priority: str = Field(default="", description="low / medium / high")
    ticket_sentiment: str = Field(default="", description="positive / neutral / negative")
    customer_response: str = Field(default="", description="Simulated customer reply")
    feedback: str = Field(default="", description="System feedback message")
    tickets_remaining: int = Field(default=0, description="Tickets left in queue")
    current_task: str = Field(default="", description="easy / medium / hard")
    steps_taken: int = Field(default=0, description="Steps used on current ticket")
    max_steps: int = Field(default=0, description="Max steps allowed per ticket")


# ---------------------------------------------------------------------------
# STATE — internal environment state (exposed via /state endpoint)
# ---------------------------------------------------------------------------

class SupportState(State):
    """
    Internal state of the environment.

    Extends the base State (which already has episode_id, step_count).
    """

    current_task: str = Field(default="easy", description="Active task difficulty")
    tickets_completed: int = Field(default=0, description="Tickets processed so far")
    total_tickets: int = Field(default=0, description="Total tickets in this task")
    cumulative_score: float = Field(default=0.0, description="Running score total")
