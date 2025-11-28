import os
import pandas as pd
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger("data_agent")

class DataAgent:
    """
    Loads real marketing dataset from data/sample_ads.csv.
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.getcwd(), "data")

    def collect_data(self, plan: list, task: str) -> Dict[str, Any]:
        csv_path = os.path.join(self.data_dir, "sample_ads.csv")

        if os.path.exists(csv_path):
            try:
                logger.info("Loading CSV dataset from: %s", csv_path)
                df = pd.read_csv(csv_path)
                logger.info("Loaded dataset with %d rows and %d columns", df.shape[0], df.shape[1])
                return {"source": "csv", "path": csv_path, "data": df}
            except Exception as e:
                logger.error("Failed to load CSV: %s", e)

        logger.warning("sample_ads.csv NOT FOUND — using synthetic fallback")
        fallback = [
            {"date": "2025-11-01", "product": "A", "units": 5, "revenue": 50}
        ]
        return {"source": "synthetic", "data": fallback}
