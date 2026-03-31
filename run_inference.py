"""Quick wrapper to run inference and save results to a text file."""
import sys
import os
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Run the inference
from inference import main
scores = main()

# Also write to file
with open("results_clean.txt", "w", encoding="utf-8") as f:
    f.write("FINAL SCORES\n")
    f.write("=" * 40 + "\n")
    for task, score in scores.items():
        f.write(f"  {task:8s} : {score:.4f}\n")
    avg = sum(scores.values()) / len(scores)
    f.write(f"  {'AVERAGE':8s} : {avg:.4f}\n")

print("\nResults saved to results_clean.txt")
