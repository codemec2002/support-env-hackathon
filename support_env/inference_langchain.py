"""
Baseline Inference Script using Langchain for Customer Support Triage Environment.

This script uses Langchain's ChatOpenAI and PydanticOutputParser to ensure
the AI outputs perfectly formatted JSON matching our Pydantic model.
"""
import os
import sys

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Load env variables
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_THIS_DIR, ".env"), override=True)

# Add paths to import environment
sys.path.insert(0, os.path.dirname(_THIS_DIR))
sys.path.insert(0, _THIS_DIR)

from server.support_env_environment import SupportEnvironment
from models import SupportAction

# ---------------------------------------------------------------------------
# Setup Langchain Model & Parser
# ---------------------------------------------------------------------------
llm = ChatOpenAI(
    model=os.environ.get("MODEL_NAME", "gpt-4o-mini"),
    temperature=0.0,
    base_url=os.environ.get("API_BASE_URL", "https://api.openai.com/v1"),
)

# Output parser forces the LLM to reply with the correct JSON schema
parser = PydanticOutputParser(pydantic_object=SupportAction)

# ---------------------------------------------------------------------------
# System Prompt (Tuned for 1.0 Score on Hard)
# ---------------------------------------------------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Tier-1 Support Agent. Your goal is to maximize triage accuracy and customer satisfaction.

RULES FOR SUCCESS:
1. ALWAYS start by deciding to `read_ticket` if you haven't read it yet.
2. If the ticket is about a bug, app crash, or data loss, DO NOT try to fix it. `escalate` it to engineering with the issue details.
3. If the ticket is about a security issue (like a hacked account), `escalate` it to security.
4. IMPORTANT: If a ticket is ambiguous, missing details, or requesting account changes without proof, YOU MUST `request_info` to get more details or verification BEFORE escalating or resolving. Do not guess.
5. If the ticket is simple (like a password reset or refund), `resolve` it, making sure to include relevant details.

{format_instructions}"""),
    ("user", "Here is the conversation history and current state:\n{history}\n\nWhat is your next action?")
])

chain = prompt | llm | parser

def run_task(env: SupportEnvironment, task: str) -> float:
    print(f"\n{'='*60}\n  TASK: {task.upper()}\n{'='*60}")
    print(f"[START] task={task}", flush=True)
    obs = env.reset(task=task)
    print(f"  > {obs.feedback}")
    
    history = []
    done = False
    step_num = 0
    
    while not done:
        step_num += 1
        
        # Format the observation
        obs_text = []
        if obs.ticket_id: obs_text.append(f"Ticket ID: {obs.ticket_id}")
        if obs.ticket_subject: obs_text.append(f"Subject: {obs.ticket_subject}")
        if obs.ticket_body: obs_text.append(f"Body: {obs.ticket_body}")
        if obs.customer_response: obs_text.append(f"Customer replied: {obs.customer_response}")
        if obs.feedback: obs_text.append(f"System Feedback: {obs.feedback}")
        obs_text.append(f"Step {obs.steps_taken}/{obs.max_steps}")
        current_state = " | ".join(obs_text)
        
        history.append(f"ENVIRONMENT: {current_state}")
        
        try:
            # Langchain runs the prompt, calls LLM, and parses into SupportAction!
            action = chain.invoke({
                "history": "\n".join(history[-5:]), # Keep last 5 turns of history
                "format_instructions": parser.get_format_instructions()
            })
            history.append(f"AGENT ACTION: {action.model_dump_json()}")
        except Exception as e:
            print(f"  [Parse Error] -- fallback reading: {e}")
            action = SupportAction(action_type="read_ticket", message="")
        
        print(f"  Step {step_num}: {action.action_type}" + (f' -- "{action.message[:60]}..."' if action.message else ""))
        
        obs = env.step(action)
        done = obs.done
        
        print(f"[STEP] step={step_num} reward={obs.reward}", flush=True)
        
        print(f"    > Feedback: {obs.feedback}")
        if obs.customer_response:
            print(f"    > Customer: {obs.customer_response[:80]}...")
            
    print(f"[END] task={task} score={obs.reward} steps={step_num}", flush=True)
    return obs.reward

def main():
    print("=" * 60)
    print("  CUSTOMER SUPPORT TRIAGE -- LANGCHAIN INFERENCE")
    print("=" * 60)
    
    env = SupportEnvironment()
    scores = {}
    
    for task in ["easy", "medium", "hard"]:
        score = run_task(env, task)
        scores[task] = score
        
    print(f"\n{'='*60}\n  FINAL RESULTS (LANGCHAIN)\n{'='*60}")
    for task, score in scores.items():
        print(f"  {task:8s} : {score:.4f}")
    avg = sum(scores.values()) / len(scores)
    print(f"  {'AVERAGE':8s} : {avg:.4f}")
    print(f"{'='*60}")
    
    # Save clean results
    with open("results_langchain.txt", "w", encoding="utf-8") as f:
        f.write("FINAL SCORES (LANGCHAIN)\n")
        f.write("=" * 40 + "\n")
        for t, s in scores.items():
            f.write(f"  {t:8s} : {s:.4f}\n")
        f.write(f"  {'AVERAGE':8s} : {avg:.4f}\n")
        
    return scores

if __name__ == "__main__":
    main()
