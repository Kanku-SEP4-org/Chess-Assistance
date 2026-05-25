import shutil
import subprocess
import sys
import time
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")

STEPS = [
    ("Tilt Predictor: Gathering data", "steps/1_gather.py"),
    ("Tilt Predictor: Feature engineering", "steps/2_features.py"),
    ("Tilt Predictor: Training model", "steps/3_train.py"),
    ("Tilt Predictor: Evaluating model", "steps/4_evaluate.py"),
]


def clean():
    for d in [PROCESSED_DIR, MODELS_DIR]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
    print("Cleaned data/processed/ and models/")


def run_step(name, path):
    print(f"\n{'='*40}")
    print(f"  {name}")
    print(f"{'='*40}")
    start = time.time()
    subprocess.run([sys.executable, path], check=True)
    elapsed = time.time() - start
    print(f"  Done in {elapsed:.1f}s")


if __name__ == "__main__":
    clean()
    for name, path in STEPS:
        run_step(name, path)
    print("\nPipeline complete.")