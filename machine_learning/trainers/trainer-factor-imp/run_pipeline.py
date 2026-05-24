import subprocess
import sys
import time


STEPS = [
    ("Gathering factor examples", "steps/1_gather.py"),
    ("Generating factor candidates", "steps/2_features.py"),
    ("Analyzing factor impact", "steps/3_analyze.py"),
    ("Validating factor-impact report", "steps/4_evaluate.py"),
]


def run_step(name: str, path: str) -> None:
    print(f"\n{'=' * 40}")
    print(f"  {name}")
    print(f"{'=' * 40}", flush=True)
    start = time.time()
    subprocess.run([sys.executable, path], check=True)
    elapsed = time.time() - start
    print(f"  Done in {elapsed:.1f}s")


if __name__ == "__main__":
    for name, path in STEPS:
        run_step(name, path)
    print("\nFactor-impact pipeline complete.")
