from typing import Any, Dict
from src.utils.logger import get_logger
import pandas as pd

logger = get_logger("evaluator_agent")

class EvaluatorAgent:
    """
    Evaluates the final output and data quality.
    """

    def evaluate(self, creative_output: str, data_package: Dict[str, Any], insights: Dict[str, Any]) -> Dict[str, Any]:
        score = 0
        messages = []

        # 1. Check creative output quality
        if creative_output and len(creative_output) > 50:
            score += 40
        else:
            messages.append("Creative output is too short or empty.")

        # 2. Validate data
        if isinstance(data_package, dict) and "data" in data_package:
            data = data_package["data"]

            if isinstance(data, pd.DataFrame):
                if not data.empty:
                    score += 30
                else:
                    messages.append("Dataset is empty.")
            elif isinstance(data, list):
                if len(data) > 0:
                    score += 30
                else:
                    messages.append("Synthetic list data is empty.")
            else:
                messages.append("Unrecognized data format.")
        else:
            messages.append("Data missing in package.")

        # 3. Insight completeness
        required_keys = ["total_revenue", "total_spend", "total_purchases"]
        satisfied = sum(1 for k in required_keys if k in insights)
        score += int(30 * (satisfied / len(required_keys)))
        messages.append(f"Satisfied {satisfied}/{len(required_keys)} insight metrics.")

        # Bound score between 0 and 100
        score = max(0, min(100, score))

        result = {"score": score, "messages": messages}
        logger.info("Evaluation result: %s", result)

        return result
