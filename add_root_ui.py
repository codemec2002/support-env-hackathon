"""Make the root URL of the HF Space look pretty instead of 'Not Found'."""
from huggingface_hub import HfApi

api = HfApi()
REPO_ID = "Spark141/support-env"

# We'll re-upload the app.py but add an HTML response for the root ("/") URL
app_py = """\
import os

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError("openenv is required. pip install openenv-core") from e

try:
    from ..models import SupportAction, SupportObservation
    from .support_env_environment import SupportEnvironment
except (ImportError, ModuleNotFoundError):
    try:
        from models import SupportAction, SupportObservation
        from server.support_env_environment import SupportEnvironment
    except (ImportError, ModuleNotFoundError):
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from models import SupportAction, SupportObservation
        from server.support_env_environment import SupportEnvironment

from fastapi.responses import HTMLResponse

app = create_app(
    SupportEnvironment,
    SupportAction,
    SupportObservation,
    env_name="support_env",
    max_concurrent_envs=10,
)

# === ADD A BEAUTIFUL LANDING PAGE FOR THE ROOT URL ===
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Customer Support Triage API</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; color: #111827; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .container { background-color: white; padding: 3rem; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); max-width: 32rem; text-align: center; }
            h1 { font-size: 1.875rem; font-weight: bold; margin-bottom: 1rem; color: #2563EB; }
            p { font-size: 1.125rem; color: #4B5563; margin-bottom: 2rem; line-height: 1.5; }
            .button-group { display: flex; gap: 1rem; justify-content: center; }
            a.button { display: inline-block; padding: 0.75rem 1.5rem; font-weight: 600; text-decoration: none; border-radius: 0.5rem; transition: background-color 0.2s; }
            .btn-primary { background-color: #2563EB; color: white; }
            .btn-primary:hover { background-color: #1D4ED8; }
            .btn-secondary { background-color: #E5E7EB; color: #4B5563; }
            .btn-secondary:hover { background-color: #D1D5DB; }
            .status { margin-top: 2rem; font-size: 0.875rem; color: #059669; font-weight: 500; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
            .dot { height: 8px; width: 8px; background-color: #10B981; border-radius: 50%; display: inline-block; animation: pulse 2s infinite; }
            @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); } 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="display:flex; align-items:center; justify-content:center; gap:0.5rem;">🎧 Support Triage Env</h1>
            <p>You have successfully deployed the <strong>Customer Support Triage OpenEnv framework</strong> for the Meta PyTorch Hackathon.</p>
            <p>This is an AI Agent Environment API, so there is no website interface. Agents connect programmatically.</p>
            <div class="button-group">
                <a href="/docs" class="button btn-primary">📖 View API Docs</a>
                <a href="/health" class="button btn-secondary">❤️ Health Check</a>
            </div>
            <div class="status">
                <span class="dot"></span> Environment Online & Ready
            </div>
        </div>
    </body>
    </html>
    '''

def main(host="0.0.0.0", port=None):
    import uvicorn
    if port is None:
        port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
"""

print("Uploading updated app.py with a beautiful root webpage...")
api.upload_file(
    path_or_fileobj=app_py.encode("utf-8"),
    path_in_repo="server/app.py",
    repo_id=REPO_ID,
    repo_type="space",
)
print("Done! The Space will rebuild in ~60 seconds.")
