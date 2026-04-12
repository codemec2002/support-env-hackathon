# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Customer Support Triage Environment Implementation.

A real-world simulation of Tier-1 customer support triage.
The agent receives customer tickets and must:
  - Read them to understand the issue
  - Optionally request more information
  - Resolve or escalate based on company policy

Three graded tasks with increasing difficulty:
  EASY   → Categorise simple, clear-cut tickets (3 tickets)
  MEDIUM → Resolve straightforward refund / replacement tickets following policy (3 tickets)
  HARD   → Handle ambiguous tickets requiring info-gathering before deciding (3 tickets)
"""

import copy
import uuid
from typing import List, Dict, Any, Optional

from openenv.core.env_server.interfaces import Environment

try:
    from ..models import SupportAction, SupportObservation, SupportState
except (ImportError, ModuleNotFoundError):
    from models import SupportAction, SupportObservation, SupportState


# ============================================================================
# TICKET DATABASE — realistic customer support scenarios
# ============================================================================

# Each ticket has:
#   id, subject, body, category, priority, sentiment,
#   correct_action ("resolve" or "escalate"),
#   resolution_keywords (words a good resolution should contain),
#   customer_clarification (what the customer says if agent asks for info),
#   needs_info (True if agent SHOULD request_info before acting)

EASY_TICKETS = [
    {
        "id": "EASY-001",
        "subject": "Password reset not working",
        "body": (
            "Hi, I've been trying to reset my password for the last 30 minutes "
            "but the reset email never arrives. I've checked my spam folder. "
            "My email is user123@example.com. Can you help?"
        ),
        "category": "account_access",
        "priority": "medium",
        "sentiment": "neutral",
        "correct_action": "resolve",
        "resolution_keywords": ["password", "reset", "email", "sent"],
        "customer_clarification": "Yes my email is user123@example.com and I last logged in yesterday.",
        "needs_info": False,
    },
    {
        "id": "EASY-002",
        "subject": "App crashes on startup",
        "body": (
            "Your mobile app crashes immediately when I open it. "
            "I'm on iPhone 14 running iOS 17.2. I've tried reinstalling "
            "but the issue persists. This started after the last update."
        ),
        "category": "technical_bug",
        "priority": "high",
        "sentiment": "negative",
        "correct_action": "escalate",
        "resolution_keywords": ["crash", "engineering", "escalat", "investigate"],
        "customer_clarification": "It crashes with a white screen, no error message shown.",
        "needs_info": False,
    },
    {
        "id": "EASY-003",
        "subject": "How do I export my data?",
        "body": (
            "Hello, I'd like to download all my account data as a CSV. "
            "I looked in settings but couldn't find the option. "
            "Could you point me in the right direction?"
        ),
        "category": "general_inquiry",
        "priority": "low",
        "sentiment": "positive",
        "correct_action": "resolve",
        "resolution_keywords": ["export", "settings", "data", "download"],
        "customer_clarification": "I'm using the web version, not the mobile app.",
        "needs_info": False,
    },
]

MEDIUM_TICKETS = [
    {
        "id": "MED-001",
        "subject": "I want a refund for my last order",
        "body": (
            "I ordered a wireless keyboard (Order #88421) and it arrived "
            "with a broken spacebar. I want a full refund. I've had the "
            "item for 3 days."
        ),
        "category": "refund_request",
        "priority": "medium",
        "sentiment": "negative",
        "correct_action": "resolve",
        "resolution_keywords": ["refund", "process", "order", "88421"],
        "customer_clarification": "The item is unused other than testing. I still have the packaging.",
        "needs_info": False,
        "policy_note": "Refund allowed within 30 days for defective items.",
    },
    {
        "id": "MED-002",
        "subject": "Wrong item delivered",
        "body": (
            "I ordered a blue backpack (Order #77210) but received a red one. "
            "I need a replacement sent ASAP. I'm traveling next week."
        ),
        "category": "order_issue",
        "priority": "high",
        "sentiment": "negative",
        "correct_action": "resolve",
        "resolution_keywords": ["replacement", "ship", "order", "77210"],
        "customer_clarification": "I can drop off the wrong item at a nearby store.",
        "needs_info": False,
        "policy_note": "Wrong-item deliveries get free replacement + return label.",
    },
    {
        "id": "MED-003",
        "subject": "Subscription charged twice",
        "body": (
            "I was charged $14.99 twice on March 15th for my monthly plan. "
            "Please fix this. My account email is jdoe@mail.com."
        ),
        "category": "billing",
        "priority": "high",
        "sentiment": "negative",
        "correct_action": "resolve",
        "resolution_keywords": ["refund", "duplicate", "charge", "credit"],
        "customer_clarification": "Both charges show on my Visa ending in 4421.",
        "needs_info": False,
        "policy_note": "Duplicate charges are auto-refunded once confirmed in billing system.",
    },
]

HARD_TICKETS = [
    {
        "id": "HARD-001",
        "subject": "Account compromised?",
        "body": (
            "I noticed a login from an IP address I don't recognise and "
            "my profile picture was changed. I'm worried my account has "
            "been hacked. What should I do?"
        ),
        "category": "security",
        "priority": "high",
        "sentiment": "negative",
        "correct_action": "escalate",
        "resolution_keywords": ["security", "escalat", "password", "lock"],
        "customer_clarification": (
            "The unrecognised login was from 185.22.100.50 at 3:14 AM. "
            "I also received an email about a password change I didn't make."
        ),
        "needs_info": True,
    },
    {
        "id": "HARD-002",
        "subject": "Feature not working after upgrade",
        "body": (
            "I upgraded to the Pro plan yesterday but I still can't access "
            "the analytics dashboard. It just says 'upgrade required'. "
            "I've already been charged for Pro."
        ),
        "category": "billing",
        "priority": "medium",
        "sentiment": "negative",
        "correct_action": "resolve",
        "resolution_keywords": ["pro", "access", "grant", "sync"],
        "customer_clarification": (
            "I upgraded through the iOS app. My receipt from Apple shows "
            "the charge on March 14th. Order ID: APP-9981234."
        ),
        "needs_info": True,
    },
    {
        "id": "HARD-003",
        "subject": "Intermittent data loss in reports",
        "body": (
            "Some of our team's reports are showing missing data for the "
            "last 2 weeks. It's not consistent — some reports are fine, "
            "others have gaps. We rely on these for client presentations."
        ),
        "category": "technical_bug",
        "priority": "high",
        "sentiment": "negative",
        "correct_action": "escalate",
        "resolution_keywords": ["engineering", "escalat", "data", "investigat"],
        "customer_clarification": (
            "Affected reports: Weekly Sales Summary, Client Metrics Q1. "
            "We're on the Enterprise plan, team of 12 users. "
            "The issue started around March 1st."
        ),
        "needs_info": True,
    },
]

TASK_TICKET_MAP = {
    "easy": EASY_TICKETS,
    "medium": MEDIUM_TICKETS,
    "hard": HARD_TICKETS,
}


# ============================================================================
# ENVIRONMENT
# ============================================================================

class SupportEnvironment(Environment):
    """
    Customer Support Triage Environment.

    Lifecycle per episode:
      1. reset(task="easy"|"medium"|"hard") → loads 3 tickets for that task
      2. For each ticket the agent loops through step() calls:
         - read_ticket  → see the ticket body
         - request_info → get clarification from the customer (optional)
         - resolve / escalate → close the ticket (graded immediately)
      3. After all tickets are processed, done=True and final reward is the
         average score across all tickets (0.0–1.0).

    Scoring per ticket (partial credit):
      +0.30  read the ticket before acting
      +0.20  correct action type (resolve vs escalate)
      +0.20  resolution message quality (keyword overlap)
      +0.15  requested info when needed (hard tickets)
      +0.15  efficiency bonus (fewer steps = better)
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    MAX_STEPS_PER_TICKET = 6  # generous limit per ticket

    def __init__(self):
        self._state = SupportState()
        self._tickets: List[Dict[str, Any]] = []
        self._current_ticket_idx: int = 0
        self._current_ticket: Optional[Dict[str, Any]] = None
        self._has_read: bool = False
        self._has_requested_info: bool = False
        self._ticket_step_count: int = 0
        self._ticket_scores: List[float] = []
        self._task: str = "easy"

    # ------------------------------------------------------------------
    # reset
    # ------------------------------------------------------------------

    def reset(self, task: str = "easy", **kwargs) -> SupportObservation:
        """
        Reset the environment for a specific task difficulty.

        Args:
            task: "easy", "medium", or "hard"
        """
        self._task = task if task in TASK_TICKET_MAP else "easy"
        self._tickets = copy.deepcopy(TASK_TICKET_MAP[self._task])
        self._current_ticket_idx = 0
        self._ticket_scores = []
        self._ticket_step_count = 0
        self._has_read = False
        self._has_requested_info = False

        self._state = SupportState(
            episode_id=str(uuid.uuid4()),
            step_count=0,
            current_task=self._task,
            tickets_completed=0,
            total_tickets=len(self._tickets),
            cumulative_score=0.0,
        )

        self._current_ticket = self._tickets[0]

        return SupportObservation(
            done=False,
            reward=0.0,
            ticket_id=self._current_ticket["id"],
            ticket_subject=self._current_ticket["subject"],
            ticket_body="",  # must read_ticket first
            ticket_category="",
            ticket_priority=self._current_ticket["priority"],
            ticket_sentiment=self._current_ticket["sentiment"],
            customer_response="",
            feedback=(
                f"Task '{self._task}' started. You have {len(self._tickets)} tickets to handle. "
                f"Use 'read_ticket' to see the first ticket, then decide how to act."
            ),
            tickets_remaining=len(self._tickets),
            current_task=self._task,
            steps_taken=0,
            max_steps=self.MAX_STEPS_PER_TICKET,
        )

    # ------------------------------------------------------------------
    # step
    # ------------------------------------------------------------------

    def step(self, action: SupportAction) -> SupportObservation:  # type: ignore[override]
        """Process one agent action."""

        self._state.step_count += 1
        self._ticket_step_count += 1

        if self._current_ticket is None:
            return self._done_observation("No more tickets. Episode is over.")

        ticket = self._current_ticket
        action_type = action.action_type.strip().lower()
        feedback = ""
        reward = 0.0
        done = False
        customer_response = ""
        ticket_body = ticket["body"] if self._has_read else ""

        # ---- ACTION: read_ticket ----
        if action_type == "read_ticket":
            self._has_read = True
            ticket_body = ticket["body"]
            feedback = "Ticket loaded. Review the details and decide your next action."

        # ---- ACTION: request_info ----
        elif action_type == "request_info":
            self._has_requested_info = True
            customer_response = ticket.get("customer_clarification", "No additional info provided.")
            feedback = "Customer responded to your question."

        # ---- ACTION: resolve ----
        elif action_type == "resolve":
            score = self._grade_ticket(ticket, "resolve", action.message)
            self._ticket_scores.append(score)
            reward = score
            feedback = f"Ticket {ticket['id']} resolved. Score: {score:.2f}/1.00"
            done = self._advance_to_next_ticket()

        # ---- ACTION: escalate ----
        elif action_type == "escalate":
            score = self._grade_ticket(ticket, "escalate", action.message)
            self._ticket_scores.append(score)
            reward = score
            feedback = f"Ticket {ticket['id']} escalated. Score: {score:.2f}/1.00"
            done = self._advance_to_next_ticket()

        else:
            feedback = (
                f"Unknown action_type '{action_type}'. "
                "Use: read_ticket, request_info, resolve, or escalate."
            )

        # Check if agent exceeded step limit for this ticket
        if self._ticket_step_count > self.MAX_STEPS_PER_TICKET and not done:
            self._ticket_scores.append(0.001)
            feedback = f"Step limit exceeded for ticket {ticket['id']}. Score: 0.00"
            done = self._advance_to_next_ticket()

        # Calculate final reward when all tickets done
        if done:
            final_score = (
                sum(self._ticket_scores) / len(self._ticket_scores)
                if self._ticket_scores
                else 0.001
            )
            final_score = max(0.001, min(0.999, final_score))
            self._state.cumulative_score = final_score
            reward = final_score

        # Build observation
        current_ticket = self._current_ticket or ticket
        reward = max(0.001, min(0.999, reward))
        return SupportObservation(
            done=done,
            reward=round(reward, 4),
            ticket_id=current_ticket["id"],
            ticket_subject=current_ticket["subject"],
            ticket_body=ticket_body,
            ticket_category=ticket["category"] if done else "",
            ticket_priority=current_ticket["priority"],
            ticket_sentiment=current_ticket["sentiment"],
            customer_response=customer_response,
            feedback=feedback,
            tickets_remaining=max(0, len(self._tickets) - self._current_ticket_idx - (1 if not done else 0)),
            current_task=self._task,
            steps_taken=self._ticket_step_count,
            max_steps=self.MAX_STEPS_PER_TICKET,
        )

    # ------------------------------------------------------------------
    # state property
    # ------------------------------------------------------------------

    @property
    def state(self) -> SupportState:
        return self._state

    # ------------------------------------------------------------------
    # GRADER — scores each ticket 0.0–1.0 with partial credit
    # ------------------------------------------------------------------

    def _grade_ticket(self, ticket: Dict, agent_action: str, agent_message: str) -> float:
        """
        Grade an agent's handling of a single ticket.

        Scoring breakdown (sums to 1.0):
          +0.30  Did the agent read the ticket first?
          +0.20  Did the agent pick the correct action (resolve vs escalate)?
          +0.20  Resolution/escalation message quality (keyword overlap)
          +0.15  Did the agent request info when it was needed? (hard tasks)
          +0.15  Efficiency bonus (fewer steps = higher)
        """
        score = 0.0

        # --- 1. Read bonus (0.30) ---
        if self._has_read:
            score += 0.30

        # --- 2. Correct action (0.20) ---
        if agent_action == ticket["correct_action"]:
            score += 0.20

        # --- 3. Message quality (0.20) ---
        keywords = ticket.get("resolution_keywords", [])
        if keywords and agent_message:
            msg_lower = agent_message.lower()
            matches = sum(1 for kw in keywords if kw.lower() in msg_lower)
            keyword_ratio = matches / len(keywords)
            score += 0.20 * keyword_ratio

        # --- 4. Info-gathering bonus (0.15) ---
        if ticket.get("needs_info", False):
            if self._has_requested_info:
                score += 0.15
            # No penalty if not needed
        else:
            # If info wasn't needed, give full marks for this criterion
            score += 0.15

        # --- 5. Efficiency bonus (0.15) ---
        # Fewer steps = better. 1 step = 0.15, 6 steps = ~0.025
        if self._ticket_step_count > 0:
            efficiency = max(0.0, 1.0 - (self._ticket_step_count - 1) / self.MAX_STEPS_PER_TICKET)
            score += 0.15 * efficiency

        return round(max(0.001, min(0.999, score)), 4)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _advance_to_next_ticket(self) -> bool:
        """Move to the next ticket. Returns True if all tickets are done."""
        self._current_ticket_idx += 1
        self._state.tickets_completed = self._current_ticket_idx
        self._ticket_step_count = 0
        self._has_read = False
        self._has_requested_info = False

        if self._current_ticket_idx >= len(self._tickets):
            self._current_ticket = None
            return True

        self._current_ticket = self._tickets[self._current_ticket_idx]
        return False

    def _done_observation(self, msg: str) -> SupportObservation:
        """Return a terminal observation."""
        final_score = (
            sum(self._ticket_scores) / len(self._ticket_scores)
            if self._ticket_scores
            else 0.001
        )
        final_score = max(0.001, min(0.999, final_score))
        return SupportObservation(
            done=True,
            reward=round(final_score, 4),
            feedback=msg,
            current_task=self._task,
            tickets_remaining=0,
            steps_taken=self._ticket_step_count,
            max_steps=self.MAX_STEPS_PER_TICKET,
        )
