from src.utils.logger import get_logger
from src.agents.planner import PlannerAgent
from src.agents.data_agent import DataAgent
from src.agents.insight_agent import InsightAgent
from src.agents.creative_agent import CreativeAgent
from src.agents.evaluator_agent import EvaluatorAgent

logger = get_logger("orchestrator")

class Orchestrator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.data_agent = DataAgent()
        self.insight_agent = InsightAgent()
        self.creative_agent = CreativeAgent()
        self.evaluator = EvaluatorAgent()

    def run(self, user_task: str):
        logger.info("Starting orchestration for task: %s", user_task)

        # 1. Planner creates steps
        plan = self.planner.create_plan(user_task)
        logger.info("Plan created: %s", plan)

        # 2. DataAgent collects / loads data per plan
        data = self.data_agent.collect_data(plan, user_task)
        logger.info("Data collected: %s", data if isinstance(data, dict) else str(type(data)))

        # 3. InsightAgent analyzes the data and returns insights
        insights = self.insight_agent.generate_insights(data)
        logger.info("Insights generated: %s", insights)

        # 4. CreativeAgent produces a human-friendly output from insights
        creative_output = self.creative_agent.create_output(insights, plan)
        logger.info("Creative output prepared.")

        # 5. EvaluatorAgent evaluates the final output
        evaluation = self.evaluator.evaluate(creative_output, data, insights)
        logger.info("Evaluation: %s", evaluation)

        return {
            "task": user_task,
            "plan": plan,
            "data_summary": data,
            "insights": insights,
            "creative_output": creative_output,
            "evaluation": evaluation
        }
