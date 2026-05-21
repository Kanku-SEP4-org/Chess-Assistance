import subprocess
import sys
import time

STEPS = [
    ("Gathering data", "steps/1_gather.py"),
    ("Feature engineering", "steps/2_features.py"),
    ("Training model", "steps/3_train.py"),
    ("Evaluating model", "steps/4_evaluate.py"),
]


def run_step(name: str, path: str) -> None:
    print(f"\n{'=' * 40}")
    print(f"  {name}")
    print(f"{'=' * 40}")
    start = time.time()
    subprocess.run([sys.executable, path], check=True)
    elapsed = time.time() - start
    print(f"  Done in {elapsed:.1f}s")


if __name__ == "__main__":
    for name, path in STEPS:
        run_step(name, path)
    print("\nPipeline complete.")

