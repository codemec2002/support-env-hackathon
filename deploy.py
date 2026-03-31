"""
Deploy support_env to Hugging Face Spaces.
This script uploads the environment as a Docker Space.
"""

import os
from huggingface_hub import HfApi, create_repo

REPO_ID = "Spark141/support-env"
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

api = HfApi()

# Step 1: Create the Space (Docker SDK)
print("Creating Hugging Face Space...")
try:
    create_repo(
        repo_id=REPO_ID,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
    )
    print(f"  Space created: https://huggingface.co/spaces/{REPO_ID}")
except Exception as e:
    print(f"  Space may already exist: {e}")

# Step 2: Upload all environment files
print("\nUploading files...")

# Files to upload (relative to support_env/)
files_to_upload = [
    "models.py",
    "client.py",
    "__init__.py",
    "openenv.yaml",
    "pyproject.toml",
    "README.md",
    "inference.py",
    "server/__init__.py",
    "server/app.py",
    "server/support_env_environment.py",
    "server/requirements.txt",
    "server/Dockerfile",
]

for filepath in files_to_upload:
    full_path = os.path.join(THIS_DIR, filepath)
    if os.path.exists(full_path):
        print(f"  Uploading {filepath}...")
        api.upload_file(
            path_or_fileobj=full_path,
            path_in_repo=filepath,
            repo_id=REPO_ID,
            repo_type="space",
        )
    else:
        print(f"  SKIPPED (not found): {filepath}")

# Step 3: Create a top-level Dockerfile that HF Spaces expects
# HF Spaces looks for Dockerfile at the root of the repo.
# We need to create one that works with the HF Spaces structure.
print("\nCreating root Dockerfile for HF Spaces...")
dockerfile_content = """\
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# HF Spaces expects port 7860
ENV PORT=7860
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \\
    CMD curl -f http://localhost:7860/health || exit 1

# Run the FastAPI server on port 7860 (HF Spaces requirement)
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
"""

# Upload the Dockerfile
api.upload_file(
    path_or_fileobj=dockerfile_content.encode("utf-8"),
    path_in_repo="Dockerfile",
    repo_id=REPO_ID,
    repo_type="space",
)

print(f"\n{'='*50}")
print(f"  DEPLOYMENT COMPLETE!")
print(f"  Space URL: https://huggingface.co/spaces/{REPO_ID}")
print(f"  App URL:   https://spark141-support-env.hf.space")
print(f"{'='*50}")
print(f"\nThe Space will take 2-5 minutes to build the Docker image.")
print(f"Check status at: https://huggingface.co/spaces/{REPO_ID}")
