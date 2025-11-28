import pandas as pd
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger("insight_agent")

class InsightAgent:
    """
    Extracts advanced insights from marketing dataset:
    CTR, ROAS, spend, revenue, purchases, best platform, etc.
    """

    def generate_insights(self, package: Dict[str, Any]) -> Dict[str, Any]:
        data = package.get("data")

        if not isinstance(data, pd.DataFrame):
            return {"error": "Data is not a pandas DataFrame"}

        df = data.copy()

        # Handle missing values safely
        df = df.fillna(0)

        insights = {
            "total_spend": float(df["spend"].sum()),
            "total_revenue": float(df["revenue"].sum()),
            "total_purchases": int(df["purchases"].sum()),
            "avg_ctr": round(float(df["ctr"].mean()), 4),
            "avg_roas": round(float(df["roas"].mean()), 4),

            "best_creative_type": df.groupby("creative_type")["roas"].mean().idxmax(),
            "best_platform": df.groupby("platform")["purchases"].sum().idxmax(),
            "best_country": df.groupby("country")["revenue"].sum().idxmax(),

            "max_revenue_day": df.loc[df["revenue"].idxmax(), "date"],
            "max_roas_day": df.loc[df["roas"].idxmax(), "date"],

            "top_audience_type": df.groupby("audience_type")["revenue"].sum().idxmax(),
            "top_adset": df.groupby("adset_name")["roas"].mean().idxmax(),
        }

        logger.info("Marketing insights created: %s", insights)

        return insights
