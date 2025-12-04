# src/schema.py
from typing import Dict, Any, Tuple
import pandas as pd

class SchemaError(Exception):
    pass

# Expected production-grade data schema (extended)
EXPECTED_SCHEMA: Dict[str, str] = {
    "date": "datetime",
    "campaign": "string",
    "impressions": "int",
    "clicks": "int",
    "spend": "float",
    "conversions": "int",
    # optional fields often in your dataset:
    "revenue": "float",
    "ctr": "float",
    "roas": "float",
    "purchases": "int",
    "creative_type": "string",
    "platform": "string",
    "country": "string",
    "audience_type": "string",
    "adset_name": "string",
}

def validate_schema(df: pd.DataFrame, schema: Dict[str, str] = EXPECTED_SCHEMA
                   ) -> Dict[str, Any]:
    """
    Validate that `df` matches required columns and can be coerced to the
    expected types. Returns a dict with keys:
      - valid: bool
      - missing: list
      - coerced_columns: list
      - problems: list of messages
    Raises SchemaError for missing required columns (fail-fast).
    """
    result = {"valid": False, "missing": [], "coerced_columns": [], "problems": []}

    # 1. Check missing required columns (only enforce a small set as strictly required)
    required_cols = ["date", "impressions", "clicks", "spend"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise SchemaError(f"Missing required columns: {missing}")

    # 2. Try to coerce available schema columns to expected types, record problems
    for col, dtype in schema.items():
        if col not in df.columns:
            continue
        try:
            if dtype == "datetime":
                coerced = pd.to_datetime(df[col], errors="coerce")
                nulls = coerced.isna().sum()
                if nulls > 0:
                    result["problems"].append(f"Column '{col}' has {nulls} unparsable datetime(s).")
                df[col] = coerced
            elif dtype == "int":
                coerced = pd.to_numeric(df[col], errors="coerce")
                nulls = coerced.isna().sum()
                if nulls > 0:
                    result["problems"].append(f"Column '{col}' has {nulls} non-numeric values coerced to NaN.")
                df[col] = coerced.fillna(0).astype(int)
            elif dtype == "float":
                coerced = pd.to_numeric(df[col], errors="coerce")
                nulls = coerced.isna().sum()
                if nulls > 0:
                    result["problems"].append(f"Column '{col}' has {nulls} non-numeric values coerced to NaN.")
                df[col] = coerced.fillna(0.0).astype(float)
            elif dtype == "string":
                df[col] = df[col].astype(str)
            result["coerced_columns"].append(col)
        except Exception as e:
            result["problems"].append(f"Failed to coerce column '{col}': {e}")

    # 3. A final quick sanity check
    if "date" in df.columns and df["date"].isna().any():
        result["problems"].append("Some date values could not be parsed to datetime.")

    result["valid"] = len(result["problems"]) == 0
    return result
