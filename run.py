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

    # ------------------------------
    # CLEAN OUTPUT MODE (Option A)
    # ------------------------------

    print("\n===============================")
    print(f"   TASK: {task}")
    print("===============================")

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

    # Creative summary
    creative = result["result"].get("creative_output", {})
    print("\n🎨 CREATIVE SUMMARY:")
    print(creative.get("summary", "No creative summary."))

    # Recommendations
    evaluator = result["result"].get("evaluation", {})
    print("\n✅ TOP RECOMMENDATION:")
    recs = evaluator.get("recommendations", [])
    if recs:
        best = recs[0]
        print(f" Run A/B test on: {best.get('variant_id')}")
        print(f" Expected score: {best.get('expected_score')}")
    else:
        print(" No recommendations.")

    # Final Score
    print("\n🏁 FINAL SCORE:", evaluator.get("score", "N/A"))

    print("\n(Use --debug to view complete JSON output.)\n")


if __name__ == "__main__":
    main()
