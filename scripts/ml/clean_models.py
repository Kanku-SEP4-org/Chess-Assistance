import os


def main():
    project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    models_dir = os.path.join(project_root, "machine_learning", "trainer", "models")

    targets = ["eval_metrics.json", "metrics.json", "model.pkl", "scaler.pkl"]

    print("Cleaning trainer model files...")
    for name in targets:
        path = os.path.join(models_dir, name)
        if os.path.exists(path):
            os.remove(path)
            print(f"  Removed {name}")
        else:
            print(f"  Skipped {name} (not found)")


if __name__ == "__main__":
    main()
