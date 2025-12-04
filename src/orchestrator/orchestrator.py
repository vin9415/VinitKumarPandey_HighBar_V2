# src/orchestrator/orchestrator.py
from time import time
from src.utils.logger import get_logger
from src.agents.planner import PlannerAgent
from src.agents.data_agent import DataAgent
from src.agents.insight_agent import InsightAgent
from src.agents.creative_agent import CreativeAgent
from src.agents.evaluator_agent import EvaluatorAgent

logger = get_logger("orchestrator_v3")

class Orchestrator:
    def __init__(self, config: dict = None):
        self.planner = PlannerAgent()
        self.data_agent = DataAgent()
        self.insight_agent = InsightAgent()
        self.creative_agent = CreativeAgent()
        self.evaluator = EvaluatorAgent()
        self.config = config or {}

    def run(self, user_task: str) -> dict:
        start_run = time()
        run_meta = {"task": user_task, "status": "started", "agent_traces": {}, "timing": {}}
        logger.info("Starting orchestration for task: %s", user_task)

        # Planner
        t0 = time()
        try:
            plan = self.planner.create_plan(user_task)
            run_meta["agent_traces"]["planner"] = {"status": "ok", "output_summary": plan}
        except Exception as e:
            run_meta["agent_traces"]["planner"] = {"status": "error", "error": str(e)}
            plan = []
        run_meta["timing"]["planner_s"] = round(time() - t0, 3)

        # DataAgent
        t0 = time()
        try:
            data_package = self.data_agent.collect_data(plan, user_task)
            run_meta["agent_traces"]["data"] = {
                "status": data_package.get("status"),
                "source": data_package.get("source"),
                "meta": data_package.get("meta", {})
            }
        except Exception as e:
            data_package = {"status": "failed", "data": None, "errors": [str(e)], "meta": {}}
            run_meta["agent_traces"]["data"] = {"status": "error", "error": str(e)}
        run_meta["timing"]["data_s"] = round(time() - t0, 3)

        # InsightAgent
        t0 = time()
        try:
            insights = self.insight_agent.generate_insights(data_package)
            run_meta["agent_traces"]["insights"] = {"status": "ok", "summary_keys": list(insights.keys())}
        except Exception as e:
            insights = {"error": str(e)}
            run_meta["agent_traces"]["insights"] = {"status": "error", "error": str(e)}
        run_meta["timing"]["insights_s"] = round(time() - t0, 3)

        # CreativeAgent
        t0 = time()
        try:
            creative_output = self.creative_agent.create_output(insights, plan)
            run_meta["agent_traces"]["creative"] = {"status": creative_output.get("status"), "n_variants": creative_output.get("meta", {}).get("n_variants", 0)}
        except Exception as e:
            creative_output = {"status": "error", "message": str(e), "variants": []}
            run_meta["agent_traces"]["creative"] = {"status": "error", "error": str(e)}
        run_meta["timing"]["creative_s"] = round(time() - t0, 3)

        # EvaluatorAgent
        t0 = time()
        try:
            evaluation = self.evaluator.evaluate(creative_output, data_package, insights)
            run_meta["agent_traces"]["evaluator"] = {"status": "ok", "score": evaluation.get("score")}
        except Exception as e:
            evaluation = {"score": 0, "messages": [str(e)]}
            run_meta["agent_traces"]["evaluator"] = {"status": "error", "error": str(e)}
        run_meta["timing"]["evaluator_s"] = round(time() - t0, 3)

        run_meta["status"] = "finished"
        run_meta["result"] = {
            "plan": plan,
            "data_package": {"status": data_package.get("status"), "meta": data_package.get("meta", {})},
            "insights": insights,
            "creative_output": creative_output,
            "evaluation": evaluation
        }
        run_meta["total_time_s"] = round(time() - start_run, 3)

        logger.info("Orchestration finished. final_score=%s", evaluation.get("score", 0))
        return run_meta
