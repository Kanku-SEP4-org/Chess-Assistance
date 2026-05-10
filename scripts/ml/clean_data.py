import os


def main():
    project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    data_dir = os.path.join(project_root, "machine_learning", "trainer", "data")

    targets = ["features.csv", "mock_data.csv"]

    print("Cleaning trainer data files...")
    for name in targets:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            os.remove(path)
            print(f"  Removed {name}")
        else:
            print(f"  Skipped {name} (not found)")


if __name__ == "__main__":
    main()
