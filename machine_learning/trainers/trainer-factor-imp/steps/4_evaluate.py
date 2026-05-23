import json
import os


REPORT_PATH = "models/factor_impact_report.json"
OUT_PATH = "models/factor_impact_validation.json"
VALID_FACTORS = {"temperature_celsius", "co2", "light"}


def probability_is_valid(value: float) -> bool:
    return 0 <= value <= 1


def main() -> None:
    if not os.path.exists(REPORT_PATH):
        raise FileNotFoundError("Missing factor-impact report. Run steps/3_analyze.py first.")

    with open(REPORT_PATH, encoding="utf-8") as f:
        report = json.load(f)

    errors = []
    examples = report.get("examples", [])
    if not examples:
        errors.append("Report must contain at least one example.")

    for example in examples:
        name = example.get("example_name", "<missing>")
        current_probability = example.get("current_win_probability")
        if current_probability is None or not probability_is_valid(current_probability):
            errors.append(f"{name}: current_win_probability must be between 0 and 1.")

        candidates = example.get("all_candidates", [])
        if not candidates:
            errors.append(f"{name}: all_candidates must not be empty.")

        recommended_factor = example.get("recommended_factor")
        if recommended_factor is not None and recommended_factor not in VALID_FACTORS:
            errors.append(f"{name}: invalid recommended_factor {recommended_factor}.")

        for candidate in candidates:
            factor = candidate.get("factor")
            if factor not in VALID_FACTORS:
                errors.append(f"{name}: invalid candidate factor {factor}.")

            win_probability = candidate.get("win_probability")
            if win_probability is None or not probability_is_valid(win_probability):
                errors.append(f"{name}: candidate {factor} win_probability must be between 0 and 1.")

    validation = {
        "report_path": REPORT_PATH,
        "valid": len(errors) == 0,
        "n_examples": len(examples),
        "errors": errors,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2)

    print("Evaluation step complete.")
    print(f"- Valid: {validation['valid']}")
    print(f"- Examples checked: {validation['n_examples']}")
    print(f"- Saved: {OUT_PATH}")

    if errors:
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
