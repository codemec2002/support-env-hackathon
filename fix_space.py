"""Fix the build errors on HF Space and redeploy."""
from huggingface_hub import HfApi

api = HfApi()
REPO_ID = "Spark141/support-env"

# Fix 1: requirements.txt — wrong package name
print("Fix 1: Uploading corrected requirements.txt...")
reqs = "openenv-core[core]>=0.2.0\nfastapi>=0.115.0\nuvicorn>=0.24.0\n"
api.upload_file(
    path_or_fileobj=reqs.encode("utf-8"),
    path_in_repo="server/requirements.txt",
    repo_id=REPO_ID,
    repo_type="space",
)
print("  Done!")

# Fix 2: openenv.yaml — port should be 7860 for HF Spaces
print("Fix 2: Uploading corrected openenv.yaml...")
yaml_content = (
    "spec_version: 1\n"
    "name: support_env\n"
    "type: space\n"
    "runtime: fastapi\n"
    "app: server.app:app\n"
    "port: 7860\n"
    "\n"
    "tasks:\n"
    "  - name: easy\n"
    '    description: "Categorise 3 simple, clear-cut customer support tickets"\n'
    "    difficulty: easy\n"
    "  - name: medium\n"
    '    description: "Resolve 3 straightforward refund/replacement tickets following company policy"\n'
    "    difficulty: medium\n"
    "  - name: hard\n"
    '    description: "Handle 3 ambiguous tickets requiring info-gathering before deciding"\n'
    "    difficulty: hard\n"
)
api.upload_file(
    path_or_fileobj=yaml_content.encode("utf-8"),
    path_in_repo="openenv.yaml",
    repo_id=REPO_ID,
    repo_type="space",
)
print("  Done!")

# Fix 3: Delete the redundant server/Dockerfile (HF uses root Dockerfile)
print("Fix 3: Removing redundant server/Dockerfile...")
try:
    api.delete_file(
        path_in_repo="server/Dockerfile",
        repo_id=REPO_ID,
        repo_type="space",
    )
    print("  Done!")
except Exception as e:
    print(f"  Skipped: {e}")

# Check status
info = api.space_info(REPO_ID)
stage = info.runtime.stage if info.runtime else "unknown"
print(f"\nSpace stage: {stage}")
print(f"URL: https://huggingface.co/spaces/{REPO_ID}")
