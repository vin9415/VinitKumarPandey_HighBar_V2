# src/utils/response_formatter.py

def format_human_response(task: str, plan: dict, insights: dict,
                          creative_output: dict, evaluation: dict) -> str:
    """
    Hybrid Smart Response Formatter
    Turns agent outputs into a business-friendly summary.
    """

    intent = plan.get("intent", "analysis")
    steps = plan.get("steps", [])

    lines = []

    # Header
    lines.append(f"🎯 Task: {task}")
    lines.append(f"🧠 Intent: {intent.capitalize()}\n")

    # Show steps
    if steps:
        lines.append("📝 Plan:")
        for step in steps:
            lines.append(f" • {step}")
        lines.append("")

    # Show insights only if present
    if insights.get("drivers"):
        drivers = insights["drivers"]
        top_drivers = drivers[:3]  # best 3 only

        lines.append("📉 Performance Drivers Found:")
        for d in top_drivers:
            metric = d.get("metric", "")
            delta = d.get("delta_str", "")
            segment = d.get("segment", "")
            severity = d.get("severity", "")
            lines.append(f" • {metric} {delta} in {segment} ({severity})")
        lines.append("")

    # Show top creatives (if exist)
    variants = creative_output.get("variants", [])
    if variants:
        lines.append("✨ Top Creative Ideas:")
        for i, v in enumerate(variants[:3], 1):
            lines.append(f"{i}. {v.get('text', '').strip()}")
        lines.append("")

    score = evaluation.get("score", "N/A")
    lines.append(f"🏁 Confidence Score: {score}/100")

    return "\n".join(lines)
