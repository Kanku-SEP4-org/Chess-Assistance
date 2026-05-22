import os
import subprocess
import sys
import platform

def run_cmd(cmd, cwd=None):
    print(f"\n========================================")
    print(f"Running: {cmd}")
    print(f"Directory: {cwd or os.getcwd()}")
    print(f"========================================")
    subprocess.check_call(cmd, shell=True, cwd=cwd)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.normpath(os.path.join(script_dir, "..", ".."))
    ml_dir = os.path.join(project_root, "machine_learning")
    trainer_dir = os.path.join(ml_dir, "trainer")
    api_dir = os.path.join(ml_dir, "api")

    venv_dir = os.path.join(ml_dir, ".venv")
    is_windows = platform.system() == "Windows"
    print("Detected OS:", "Windows" if is_windows else "Unix-like")

    # --- 1. Setup single virtual environment ---
    if not os.path.exists(venv_dir):
        print(f"\n--- Creating single virtual environment at {venv_dir} ---")
        run_cmd(f'"{sys.executable}" -m venv .venv', cwd=ml_dir)
    else:
        print(f"\n--- Virtual environment already exists at {venv_dir} ---")

    if is_windows:
        activate_cmd = "source .venv/Scripts/activate"
    else:
        activate_cmd = "source .venv/bin/activate"
    print(f"\nTo activate the venv manually, run from machine_learning/:")
    print(f"  {activate_cmd}\n")

    python_exe = os.path.join(venv_dir, "Scripts", "python") if is_windows else os.path.join(venv_dir, "bin", "python")
    pip_exe = os.path.join(venv_dir, "Scripts", "pip") if is_windows else os.path.join(venv_dir, "bin", "pip")
    uvicorn_exe = os.path.join(venv_dir, "Scripts", "uvicorn") if is_windows else os.path.join(venv_dir, "bin", "uvicorn")

    # --- 2. Install dependencies for both Trainer and API ---
    print("\n--- Installing all requirements ---")
    run_cmd(f'"{pip_exe}" install -r trainer/requirements.txt', cwd=ml_dir)
    run_cmd(f'"{pip_exe}" install -r api/requirements.txt', cwd=ml_dir)

    # --- 3. Clean up old training artifacts ---
    print("\n--- Cleaning up old training artifacts ---")
    run_cmd(f'"{python_exe}" clean_data.py', cwd=script_dir)
    run_cmd(f'"{python_exe}" clean_models.py', cwd=script_dir)

    # --- 4. Run Trainer Pipeline ---
    print("\n--- Running Trainer Pipeline ---")
    run_cmd(f'"{python_exe}" run_pipeline.py', cwd=trainer_dir)

    # --- 5. Run FastAPI Server ---
    print("\n========================================")
    print("Starting Uvicorn server (Press Ctrl+C to stop)...")
    print("========================================")
    run_cmd(f'"{uvicorn_exe}" main:app --reload', cwd=api_dir)

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nError: A command failed with exit code {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(0)
