# src/agents/data_agent.py
import os
import pandas as pd
import numpy as np
from typing import Dict, Any
from time import time
from src.utils.logger import get_logger
from src.schema import validate_schema, SchemaError, EXPECTED_SCHEMA

logger = get_logger("data_agent")

DEFAULT_CONFIG = {
    "data_dir": None,
    "csv_name": "sample_ads.csv",
    "low_ctr_threshold": 0.01,   # example: CTR lower than 1% flagged
    "low_roas_threshold": 0.5,   # example: ROAS lower than 0.5 flagged
}

class DataAgent:
    """
    Loads dataset, validates schema, and returns a structured data package.
    """

    def __init__(self, data_dir: str = None, config: Dict[str, Any] = None):
        cfg = DEFAULT_CONFIG.copy()
        if config:
            cfg.update(config)
        self.config = cfg
        self.data_dir = data_dir or cfg["data_dir"] or os.path.join(os.getcwd(), "data")

    def collect_data(self, plan: list, task: str) -> Dict[str, Any]:
        start = time()
        csv_path = os.path.join(self.data_dir, self.config["csv_name"])
        package: Dict[str, Any] = {
            "status": "failed",
            "source": None,
            "path": None,
            "data": None,
            "errors": [],
            "schema_check": None,
            "meta": {}
        }

        # Try to read CSV if exists
        if os.path.exists(csv_path):
            package["path"] = csv_path
            try:
                logger.info("Loading CSV dataset from: %s", csv_path)
                df = pd.read_csv(csv_path)
                package["source"] = "csv"
                package["data"] = df
                # Validate schema
                try:
                    schema_check = validate_schema(df, EXPECTED_SCHEMA)
                    package["schema_check"] = schema_check
                    if not schema_check.get("valid", False):
                        package["errors"].append({"type": "schema_warnings", "details": schema_check["problems"]})
                        logger.warning("Schema validation produced warnings: %s", schema_check["problems"])
                    else:
                        logger.info("Schema validation passed.")
                    package["status"] = "loaded"
                except SchemaError as se:
                    package["errors"].append({"type": "schema_error", "details": str(se)})
                    package["status"] = "schema_error"
                    logger.error("SchemaError: %s", se)
                except Exception as e:
                    package["errors"].append({"type": "schema_exception", "details": str(e)})
                    package["status"] = "schema_exception"
                    logger.exception("Schema validation exception.")
                finally:
                    package["meta"]["rows"] = int(df.shape[0])
                    package["meta"]["cols"] = int(df.shape[1])
            except Exception as e:
                logger.exception("Failed to load CSV")
                package["errors"].append({"type": "io_error", "details": str(e)})
                package["status"] = "io_error"
        else:
            logger.warning("CSV not found at %s — using synthetic fallback", csv_path)
            fallback_df = pd.DataFrame([
                {"date": pd.to_datetime("2025-11-01"), "campaign": "demo", "impressions": 1000, "clicks": 10,
                 "spend": 50.0, "conversions": 1, "revenue": 50.0, "ctr": 0.01, "roas": 1.0, "purchases": 1,
                 "creative_type": "image", "platform": "facebook", "country": "IN", "audience_type": "broad",
                 "adset_name": "demo_adset"}
            ])
            package["source"] = "synthetic"
            package["data"] = fallback_df
            package["status"] = "synthetic"
            package["meta"]["rows"] = 1
            package["meta"]["cols"] = fallback_df.shape[1]

        package["meta"]["load_time_seconds"] = round(time() - start, 3)
        logger.info("DataAgent collect_data finished with status=%s meta=%s", package["status"], package["meta"])
        return package