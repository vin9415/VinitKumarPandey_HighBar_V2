# run.py
import sys
import json
import argparse
from src.orchestrator.orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(description="AI Marketing Analyst")
    parser.add_argument("task", nargs="*", help="Task to run")
    parser.add_argument("--debug", action="store_true", help="Print full JSON output")

    args = parser.parse_args()

    # If no task supplied → default task
    task = " ".join(args.task) if args.task else "Analyze recent sales and propose improvements"

    orch = Orchestrator()
    result = orch.run(task)

    if args.debug:
        # Full JSON dump
        print(json.dumps(result, indent=2))
        return

    # Detect creative tasks
    is_creative_task = any(keyword in task.lower() for keyword in [
        "write", "ad copy", "creative", "generate"
    ])

    print("\n===============================")
    print(f"   TASK: {task}")
    print("===============================")

    # Print Creative Ad Copies if creative task
    if is_creative_task:
        creative_output = result["result"].get("creative_output", {})
        variants = creative_output.get("variants", [])

        print("\n🎯 GENERATED AD COPIES:\n")

        if variants:
            for i, v in enumerate(variants[:3], start=1):
                print(f"Ad Copy #{i}:")
                print(f"Headline: {v.get('headline')}")
                print(f"Body: {v.get('body')}")
                print(f"Format: {v.get('format')}")
                print("-" * 40)
        else:
            print("⚠️ No creative content generated.")

    else:
        # ------------------------------
        # ANALYTICS MODE (default)
        # ------------------------------

        # Planner summary
        plan = result["result"].get("plan", [])
        print("\n📝 PLAN OVERVIEW:")
        for step in plan:
            print(f" - {step}")

        # Insight summary
        insights = result["result"].get("insights", {})
        print("\n📊 KEY METRICS:")
        print(f" Total Spend: {insights.get('total_spend')}")
        print(f" Total Revenue: {insights.get('total_revenue')}")
        print(f" Total Purchases: {insights.get('total_purchases')}")
        print(f" Avg CTR: {insights.get('avg_ctr')}")
        print(f" Avg ROAS: {insights.get('avg_roas')}")

    # Recommendations (for all tasks — optional)
    evaluator = result["result"].get("evaluation", {})
    print("\n📌 RECOMMENDATION:")
    recs = evaluator.get("recommendations", [])
    if recs:
        best = recs[0]
        print(f" Best Variant: {best.get('variant_id')}")
        print(f" Expected Score: {best.get('expected_score')}")
    else:
        print(" No recommendations available.")

    # Final Score
    print("\n🏁 FINAL SCORE:", evaluator.get("score", "N/A"))

    print("\n✔ Task Completed! (Use --debug for full JSON)\n")


if __name__ == "__main__":
    main()
