---
title: Support Env
emoji: 🏢
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---
# Customer Support Triage Environment

A real-world OpenEnv environment that simulates Tier-1 customer support triage. An AI agent receives customer tickets and must read, categorise, and handle them through resolution or escalation — following company policy.

## Why This Environment?

Customer support triage is a task millions of humans do every day. It requires:
- **Reading comprehension** — understanding what the customer needs
- **Decision-making** — resolve it yourself or escalate to a specialist?
- **Policy adherence** — following refund windows, security protocols
- **Information gathering** — asking the right questions before acting

This environment tests whether an LLM agent can perform this real-world workflow reliably.

## Action Space

The agent has 4 possible actions per step:

| Action | Description | `message` field |
|--------|-------------|-----------------|
| `read_ticket` | View the full ticket body | Not required |
| `request_info` | Ask the customer a clarifying question | Your question |
| `resolve` | Close the ticket with a resolution | Resolution summary |
| `escalate` | Pass the ticket to a senior agent | Reason for escalation |

```json
{"action_type": "resolve", "message": "Your refund for Order #88421 has been processed."}
```

## Observation Space

After each action, the agent receives:

| Field | Type | Description |
|-------|------|-------------|
| `ticket_id` | str | Unique ticket identifier |
| `ticket_subject` | str | Short subject line |
| `ticket_body` | str | Full message (visible after `read_ticket`) |
| `ticket_priority` | str | `low` / `medium` / `high` |
| `ticket_sentiment` | str | `positive` / `neutral` / `negative` |
| `customer_response` | str | Customer's reply (after `request_info`) |
| `feedback` | str | System feedback on the last action |
| `tickets_remaining` | int | Tickets left in queue |
| `steps_taken` | int | Steps used on current ticket |
| `max_steps` | int | Maximum steps allowed (6) |
| `done` | bool | Whether the episode is complete |
| `reward` | float | Score for the current action (0.0–1.0) |

## Tasks & Grading

| Task | Tickets | Difficulty | Focus |
|------|---------|-----------|-------|
| `easy` | 3 | 🟢 | Categorise clear-cut tickets |
| `medium` | 3 | 🟡 | Resolve refund/billing tickets per policy |
| `hard` | 3 | 🔴 | Gather info, then resolve or escalate |

### Scoring Breakdown (per ticket, sums to 1.0)

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Read ticket | 0.30 | Did the agent read the ticket before acting? |
| Correct action | 0.20 | Did it pick resolve vs escalate correctly? |
| Message quality | 0.20 | Keyword overlap with expected resolution |
| Info gathering | 0.15 | Requested info when it was needed (hard tasks) |
| Efficiency | 0.15 | Fewer steps = higher bonus |

Final score per task = average score across all 3 tickets (0.0–1.0).

## Setup & Run

### Prerequisites

- Python 3.10+
- Docker (for containerised testing)

### Local Development

```bash
# Clone and install
git clone <your-repo-url>
cd support_env

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install dependencies
pip install openenv-core

# Run the server
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Run the Inference Script

```bash
# Set environment variables
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your-token-here"

# Run
python inference.py
```

### Docker

```bash
docker build -t support_env:latest -f server/Dockerfile .
docker run -p 8000:8000 support_env:latest
```

### Deploy to Hugging Face Spaces

```bash
openenv push --repo-id your-username/support-env
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Reset environment (pass `{"task": "easy"}`) |
| `/step` | POST | Send an action |
| `/state` | GET | Get current state |
| `/health` | GET | Health check |
| `/ws` | WS | WebSocket for persistent sessions |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `API_BASE_URL` | The API endpoint for the LLM |
| `MODEL_NAME` | The model identifier to use for inference |
| `HF_TOKEN` | Your Hugging Face / API key |

## License

BSD-style license. See LICENSE file.
