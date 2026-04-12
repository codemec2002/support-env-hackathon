"""Test all live endpoints on HF Spaces."""
import requests

base = "https://spark141-support-env.hf.space"

print("1. /health")
r = requests.get(f"{base}/health")
print(f"   Status: {r.status_code} | Response: {r.json()}")

print()
print("2. /reset (POST with task=easy)")
r = requests.post(f"{base}/reset", json={"task": "easy"})
print(f"   Status: {r.status_code}")
obs = r.json().get("observation", {})
print(f"   Ticket ID: {obs.get('ticket_id')}")
print(f"   Subject: {obs.get('ticket_subject')}")
feedback = obs.get("feedback", "")
print(f"   Feedback: {feedback[:80]}")

print()
print("3. /state (GET)")
r = requests.get(f"{base}/state")
print(f"   Status: {r.status_code} | Response: {r.json()}")

print()
print("4. /docs (Swagger UI - open this in browser!)")
r = requests.get(f"{base}/docs")
print(f"   Status: {r.status_code} | Has HTML: {len(r.text) > 100}")
print(f"   TRY IT: {base}/docs")
