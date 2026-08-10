from __future__ import annotations

from typing import Any


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Campaign Planning and Optimization Review",
        "",
        f"**Campaign:** {result['campaign_id']}",
        f"**Status:** {result['status']}",
        f"**Objective:** {result['objective']}",
        f"**Reporting period:** {result['trend_review']['reporting_period']}",
        "",
        "## Plan",
        "",
        f"- Product: {result['planning']['product']}",
        f"- Audience: {result['planning']['audience']}",
        f"- Total budget: {result['planning']['currency']} {result['planning']['total_budget']:,.2f}",
        f"- Experiment rule: {result['planning']['experiment_rule']}",
        "",
        "## Performance review",
        "",
    ]
    for cell in result["performance_review"]:
        cpa = "n/a" if cell["cpa"] is None else f"{cell['cpa']:.2f}"
        lines.append(
            f"- **{cell['cell_id']}** - CTR {cell['ctr']:.2%}, CVR {cell['conversion_rate']:.2%}, "
            f"CPA {cpa}, ROAS {cell['roas']:.2f} [{cell['source_id']}]"
        )
    if result["trend_review"]["comparable"]:
        lines.extend(["", "## Comparable period changes", ""])
        for item in result["trend_review"]["comparable"]:
            changes = item["changes"]
            cpa_change = "n/a" if changes["cpa_pct"] is None else f"{changes['cpa_pct']:+.2f}%"
            roas_change = "n/a" if changes["roas_pct"] is None else f"{changes['roas_pct']:+.2f}%"
            citations = " ".join(f"[{source}]" for source in item["evidence_ids"])
            lines.append(
                f"- **{item['cell_id']}** ({item['comparison_period']} to {item['current_period']}): "
                f"CTR {changes['ctr_percentage_points']:+.2f} pp, "
                f"CVR {changes['conversion_rate_percentage_points']:+.2f} pp, "
                f"CPA {cpa_change}, ROAS {roas_change}. {citations}"
            )
    if result["trend_review"]["warnings"]:
        lines.extend(["", "## Trend warnings", ""])
        for item in result["trend_review"]["warnings"]:
            citations = " ".join(f"[{source}]" for source in item["evidence_ids"])
            lines.append(f"- **{item['cell_id']} - {item['code']}**: {item['message']} {citations}")
    if result["creative_review"]["violations"]:
        lines.extend(["", "## Blocking creative claims", ""])
        for item in result["creative_review"]["violations"]:
            lines.append(f"- {item['creative_id']}: `{item['phrase']}`")
    if result["optimization_recommendations"]:
        lines.extend(["", "## Optimization recommendations", ""])
        for item in result["optimization_recommendations"]:
            citations = " ".join(f"[{source}]" for source in item["evidence_ids"])
            lines.append(
                f"- **{item['cell_id']} - {item['action']}**: {item['reason']} "
                f"Suggested budget change {item['recommended_budget_change_pct']:.1f}%. {citations}"
            )
    lines.extend([
        "",
        "## Governance",
        "",
        f"- Human owner: {result['governance']['human_owner']}",
        "- Human approval required: yes",
        "- Platform write executed: no",
        f"- Maximum reallocation: {result['governance']['max_reallocation_pct']:.1f}%",
        "",
        "_All inputs and performance values are synthetic; this is not a real campaign result._",
        "",
    ])
    return "\n".join(lines)
