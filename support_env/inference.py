"""
Baseline Inference Script for Customer Support Triage Environment.

This script demonstrates an LLM agent solving the support triage tasks.
It uses the OpenAI client as required by the hackathon rules.

Required environment variables:
    API_BASE_URL  — The API endpoint for the LLM
    MODEL_NAME    — The model identifier (e.g., "meta-llama/Llama-3-8B-Instruct")
    HF_TOKEN      — Your Hugging Face / API key

Usage:
    python inference.py
"""

import os
import json
import sys

from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Load .env file — reads API keys from the .env file in the same directory
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_THIS_DIR, ".env"), override=True)

# ---------------------------------------------------------------------------
# Add PARENT directory to path so 'support_env' is importable as a package
# Also add THIS directory so direct imports work when run from here
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(_THIS_DIR))  # parent → finds support_env/
sys.path.insert(0, _THIS_DIR)                    # this dir → fallback

from server.support_env_environment import SupportEnvironment
from models import SupportAction

# ---------------------------------------------------------------------------
# Configuration from environment variables (loaded from .env file)
# ---------------------------------------------------------------------------

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# ---------------------------------------------------------------------------
# LLM client setup
# ---------------------------------------------------------------------------

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or os.environ.get("OPENAI_API_KEY", ""),
)

# ---------------------------------------------------------------------------
# System prompt — tells the LLM how to act as a support agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a Tier-1 customer support agent. You handle support tickets by taking
actions in a structured environment.

Available actions (respond ONLY with valid JSON):
  {"action_type": "read_ticket", "message": ""}
  {"action_type": "request_info", "message": "<your question to the customer>"}
  {"action_type": "resolve", "message": "<your resolution summary>"}
  {"action_type": "escalate", "message": "<reason for escalation>"}

Strategy:
1. ALWAYS start by reading the ticket with read_ticket.
2. For simple tickets, resolve or escalate based on the issue.
3. For complex tickets (security issues, data loss, unclear problems),
   use request_info first to gather details, THEN resolve or escalate.
4. Resolve tickets you can fix (refunds, billing, how-to questions).
5. Escalate tickets that need engineering or security team involvement
   (crashes, data loss, account compromise).
6. Include relevant keywords in your resolution message (order numbers,
   account details, specific actions taken).

Respond with ONLY the JSON action. No explanation, no markdown, no extra text.
"""


def call_llm(conversation_history: list) -> dict:
    """
    Send conversation to LLM, parse JSON action from response.

    Returns a dict like {"action_type": "resolve", "message": "..."}
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=conversation_history,
            temperature=0.1,  # low temperature for deterministic behaviour
            max_tokens=300,
        )
        content = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            content = content.rsplit("```", 1)[0]
            content = content.strip()

        return json.loads(content)

    except (json.JSONDecodeError, Exception) as e:
        print(f"  [LLM parse error: {e}] -- falling back to read_ticket")
        return {"action_type": "read_ticket", "message": ""}


def run_task(env: SupportEnvironment, task: str) -> float:
    """
    Run a single task (easy/medium/hard) and return the final score.
    """
    print(f"\n{'='*60}")
    print(f"  TASK: {task.upper()}")
    print(f"{'='*60}")

    print(f"[START] task={task}", flush=True)

    obs = env.reset(task=task)
    print(f"  > {obs.feedback}")

    done = False
    step_num = 0
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

    while not done:
        step_num += 1

        # Build the user prompt from the current observation
        user_msg = build_observation_prompt(obs)
        conversation.append({"role": "user", "content": user_msg})

        # Ask the LLM what to do
        action_dict = call_llm(conversation)
        action_type = action_dict.get("action_type", "read_ticket")
        message = action_dict.get("message", "")

        print(f"  Step {step_num}: {action_type}" + (f' -- "{message[:60]}..."' if message else ""))

        # Record LLM's response in conversation
        conversation.append({"role": "assistant", "content": json.dumps(action_dict)})

        # Send action to environment
        action = SupportAction(action_type=action_type, message=message)
        obs = env.step(action)
        done = obs.done

        print(f"[STEP] step={step_num} reward={obs.reward}", flush=True)

        print(f"    > Feedback: {obs.feedback}")
        if obs.customer_response:
            print(f"    > Customer: {obs.customer_response[:80]}...")

    final_score = obs.reward
    print(f"[END] task={task} score={final_score} steps={step_num}", flush=True)
    print(f"\n  [OK] Task '{task}' complete -- Final Score: {final_score:.4f}")
    return final_score


def build_observation_prompt(obs) -> str:
    """
    Convert a SupportObservation into a natural-language prompt for the LLM.
    """
    parts = []

    if obs.ticket_id:
        parts.append(f"Ticket ID: {obs.ticket_id}")
    if obs.ticket_subject:
        parts.append(f"Subject: {obs.ticket_subject}")
    if obs.ticket_body:
        parts.append(f"Body: {obs.ticket_body}")
    if obs.ticket_priority:
        parts.append(f"Priority: {obs.ticket_priority}")
    if obs.ticket_sentiment:
        parts.append(f"Sentiment: {obs.ticket_sentiment}")
    if obs.customer_response:
        parts.append(f"Customer Response: {obs.customer_response}")
    if obs.feedback:
        parts.append(f"System: {obs.feedback}")

    parts.append(f"Steps used: {obs.steps_taken}/{obs.max_steps}")
    parts.append(f"Tickets remaining: {obs.tickets_remaining}")
    parts.append("\nWhat action do you take? Respond with JSON only.")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main — run all 3 tasks and report scores
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  CUSTOMER SUPPORT TRIAGE -- BASELINE INFERENCE")
    print("=" * 60)
    print(f"  Model: {MODEL_NAME}")
    print(f"  API:   {API_BASE_URL}")

    env = SupportEnvironment()
    scores = {}

    for task in ["easy", "medium", "hard"]:
        score = run_task(env, task)
        scores[task] = score

    print(f"\n{'='*60}")
    print("  FINAL RESULTS")
    print(f"{'='*60}")
    for task, score in scores.items():
        print(f"  {task:8s} : {score:.4f}")
    avg = sum(scores.values()) / len(scores)
    print(f"  {'AVERAGE':8s} : {avg:.4f}")
    print(f"{'='*60}")

    return scores


if __name__ == "__main__":
    main()
