from __future__ import annotations

import argparse
from pathlib import Path

from .creative_feedback import replay_creative_feedback, write_feedback_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay governed synthetic creative feedback.")
    parser.add_argument("campaign", type=Path, nargs="?", default=Path("data/sample_campaign.json"))
    parser.add_argument("feedback", type=Path, nargs="?", default=Path("data/creative_feedback.json"))
    parser.add_argument("--json-output", type=Path, default=Path("examples/creative_feedback_report.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("examples/creative_feedback_report.md"))
    args = parser.parse_args()
    report = replay_creative_feedback(args.campaign, args.feedback)
    write_feedback_report(report, args.json_output, args.markdown_output)
    print(f"Creative feedback replay: {report['summary']['passed']}/{report['summary']['replayed']} passed")


if __name__ == "__main__":
    main()
