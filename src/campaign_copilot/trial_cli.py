from pathlib import Path
from .trial import write_trial_report


def main() -> None:
    root = Path.cwd()
    report = write_trial_report(root, root / "reports/trial_report.json", root / "reports/trial_report.md")
    print(f"Trial readiness: {'PASS' if report['overall_passed'] else 'FAIL'}")


if __name__ == "__main__":
    main()
