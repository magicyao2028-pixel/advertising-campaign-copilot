from __future__ import annotations

import argparse
import json
from pathlib import Path

from .copilot import CampaignCopilot
from .models import load_campaign
from .report import render_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a reviewable synthetic campaign optimization report.")
    parser.add_argument("campaign", type=Path, help="Campaign brief and performance JSON")
    parser.add_argument("--json-output", type=Path, default=Path("output/campaign_review.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("output/campaign_review.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = CampaignCopilot().review(load_campaign(args.campaign))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(f"Campaign review written to {args.json_output} and {args.markdown_output}")


if __name__ == "__main__":
    main()
