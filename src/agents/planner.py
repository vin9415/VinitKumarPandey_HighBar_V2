from typing import List

class PlannerAgent:
    """
    Create a simple ordered plan of steps from a natural language task.
    """

    def __init__(self):
        pass

    def create_plan(self, task: str) -> List[str]:
        # Minimal heuristic planner — break the task into stages.
        plan = [
            "1. Understand task and define subgoals",
            "2. Collect and load relevant data",
            "3. Clean and preprocess data",
            "4. Analyze data and compute metrics",
            "5. Generate insights and recommendations",
            "6. Create final deliverable (summary/report)"
        ]
        # If the task mentions 'sales' add a sales-specific step
        if "sales" in task.lower():
            plan.insert(3, "3b. Segment sales by product, time and region")
        return plan