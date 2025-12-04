# src/agents/insight_agent.py
import math
import logging
from typing import Dict, Any, List
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger("insight_agent_v3")

# Helpers for basic statistics
def proportion_z_test(clicks1, impr1, clicks2, impr2):
    """Return z, p two-sided for difference in proportions (p2 - p1)."""
    # protect division by zero
    if impr1 <= 0 or impr2 <= 0:
        return 0.0, 1.0
    p1 = clicks1 / impr1
    p2 = clicks2 / impr2
    p_pool = (clicks1 + clicks2) / (impr1 + impr2) if (impr1 + impr2) > 0 else 0.0
    se = math.sqrt(max(1e-9, p_pool * (1 - p_pool) * (1.0 / impr1 + 1.0 / impr2)))
    z = (p2 - p1) / se if se > 0 else 0.0
    # two-sided p-value from z
    phi = 0.5 * (1 + math.erf(abs(z) / math.sqrt(2)))
    p = 2 * (1 - phi)
    return z, p

def pct_change(a, b):
    # percent change from a to b
    if a == 0:
        return float("inf") if b != 0 else 0.0
    return (b - a) / abs(a) * 100.0

def confidence_from_p(p):
    # map p-value to a 0..1 confidence (simple)
    # small p -> high confidence. Bound and invert.
    if p <= 0:
        return 1.0
    conf = max(0.0, 1.0 - min(1.0, p * 10))  # heuristic: p=0.05 -> conf=0.5
    return conf

def severity_label(pct):
    a = abs(pct)
    if a >= 50:
        return "critical"
    if a >= 25:
        return "high"
    if a >= 10:
        return "medium"
    return "low"

class InsightAgent:
    """
    InsightAgent v3:
      - Produces baseline vs current diagnostics per segment.
      - Returns drivers/hypotheses with evidence, impact, and confidence.
      - Keeps original summary outputs for creatives.
    """

    def __init__(self, baseline_frac: float = 0.3):
        """
        baseline_frac: fraction of earliest time to treat as baseline (0..1).
                       default 0.3 => first 30% of chronological data is baseline,
                       last 30% is current (for comparison).
        """
        self.baseline_frac = baseline_frac

    def _safe_to_numeric(self, df: pd.DataFrame, col: str):
        if col not in df.columns:
            return None
        return pd.to_numeric(df[col], errors="coerce").fillna(0)

    def generate_insights(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input package: {"data": pandas.DataFrame, ...}
        Returns: insights dict + "drivers" list with evidence and hypothesis fields.
        """
        data = package.get("data")
        if not isinstance(data, pd.DataFrame):
            logger.error("InsightAgent: data is not a DataFrame")
            return {"error": "Data is not a pandas DataFrame"}

        df = data.copy()
        # Basic cleaning and safety
        for col in ["impressions", "clicks", "spend", "revenue", "purchases", "roas", "ctr"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Parse date if present
        if "date" in df.columns:
            try:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
            except Exception as e:
                logger.warning("Failed to parse date column: %s", e)

        # Compute basic totals
        meta = {"rows": df.shape[0], "cols": df.shape[1]}
        totals = {
            "total_spend": float(df["spend"].sum()) if "spend" in df.columns else 0.0,
            "total_revenue": float(df["revenue"].sum()) if "revenue" in df.columns else 0.0,
            "total_purchases": int(df["purchases"].sum()) if "purchases" in df.columns else 0,
            "avg_ctr": float(df["ctr"].mean()) if "ctr" in df.columns else None,
            "avg_roas": float(df["roas"].mean()) if "roas" in df.columns else None
        }

        result = {"meta": meta}
        result.update(totals)

        # 1) Per-segment aggregates (by adset_name)
        grouping = "adset_name" if "adset_name" in df.columns else None

        if grouping:
            grp = df.groupby(grouping).agg({
                "impressions": "sum",
                "clicks": "sum",
                "spend": "sum",
                "revenue": "sum",
                "purchases": "sum"
            }).reset_index()
            # compute ctr, roas
            grp["ctr"] = grp.apply(lambda r: (r["clicks"] / r["impressions"]) if r["impressions"] > 0 else 0.0, axis=1)
            grp["roas"] = grp.apply(lambda r: (r["revenue"] / r["spend"]) if r["spend"] > 0 else 0.0, axis=1)
            # sort
            top_adsets = grp.sort_values(by="roas", ascending=False).head(10).to_dict(orient="records")
            result["top_adsets"] = [{"key": r[grouping], "roas": r["roas"]} for r in top_adsets]
        else:
            result["top_adsets"] = []

        # 2) Trend analysis & diagnostics: baseline vs current (time split)
        drivers: List[Dict[str, Any]] = []
        try:
            if "date" in df.columns and not df["date"].isna().all():
                df_sorted = df.sort_values("date")
                n = len(df_sorted)
                b = max(1, int(n * self.baseline_frac))
                e = max(1, int(n * self.baseline_frac))
                baseline_df = df_sorted.iloc[:b]
                current_df = df_sorted.iloc[-e:]
                logger.info("Using baseline rows=%d current rows=%d for diagnostics", b, e)

                # global CTR / ROAS comparison
                base_impr = int(baseline_df["impressions"].sum()) if "impressions" in baseline_df.columns else 0
                base_clicks = int(baseline_df["clicks"].sum()) if "clicks" in baseline_df.columns else 0
                curr_impr = int(current_df["impressions"].sum()) if "impressions" in current_df.columns else 0
                curr_clicks = int(current_df["clicks"].sum()) if "clicks" in current_df.columns else 0

                base_ctr = (base_clicks / base_impr) if base_impr > 0 else 0.0
                curr_ctr = (curr_clicks / curr_impr) if curr_impr > 0 else 0.0
                z_ctr, p_ctr = proportion_z_test(base_clicks, base_impr, curr_clicks, curr_impr)
                ctr_delta = pct_change(base_ctr, curr_ctr)

                base_spend = float(baseline_df["spend"].sum()) if "spend" in baseline_df.columns else 0.0
                base_revenue = float(baseline_df["revenue"].sum()) if "revenue" in baseline_df.columns else 0.0
                curr_spend = float(current_df["spend"].sum()) if "spend" in current_df.columns else 0.0
                curr_revenue = float(current_df["revenue"].sum()) if "revenue" in current_df.columns else 0.0
                base_roas = (base_revenue / base_spend) if base_spend > 0 else 0.0
                curr_roas = (curr_revenue / curr_spend) if curr_spend > 0 else 0.0
                roas_delta = pct_change(base_roas, curr_roas)
                # confidence for ROAS: crude mapping using sample sizes
                roas_conf = confidence_from_p(p_ctr)  # reuse CTR p as proxy; stronger tests could be added

                trend = {
                    "ctr_baseline": base_ctr,
                    "ctr_current": curr_ctr,
                    "ctr_delta_pct": round(ctr_delta, 3),
                    "ctr_z": z_ctr,
                    "ctr_p": p_ctr,
                    "roas_baseline": base_roas,
                    "roas_current": curr_roas,
                    "roas_delta_pct": round(roas_delta, 3),
                    "roas_confidence": round(roas_conf, 3)
                }
                result["trend"] = trend

                # 3) Per-segment baseline vs current for adsets (if available)
                if grouping:
                    # we'll compare baseline vs current within each adset
                    baseline_grp = baseline_df.groupby(grouping).agg({"impressions": "sum", "clicks": "sum", "spend": "sum", "revenue": "sum"}).reset_index()
                    current_grp = current_df.groupby(grouping).agg({"impressions": "sum", "clicks": "sum", "spend": "sum", "revenue": "sum"}).reset_index()
                    merged = pd.merge(baseline_grp, current_grp, on=grouping, how="outer", suffixes=("_base", "_curr")).fillna(0)

                    low_ctr_segments = []
                    low_roas_segments = []
                    drivers = []
                    for _, r in merged.iterrows():
                        seg = r[grouping]
                        base_impr = int(r.get("impressions_base", 0))
                        base_clicks = int(r.get("clicks_base", 0))
                        curr_impr = int(r.get("impressions_curr", 0))
                        curr_clicks = int(r.get("clicks_curr", 0))

                        base_ctr_seg = (base_clicks / base_impr) if base_impr > 0 else 0.0
                        curr_ctr_seg = (curr_clicks / curr_impr) if curr_impr > 0 else 0.0
                        z_seg, p_seg = proportion_z_test(base_clicks, base_impr, curr_clicks, curr_impr)
                        ctr_pct = pct_change(base_ctr_seg, curr_ctr_seg)

                        base_spend_seg = float(r.get("spend_base", 0.0))
                        curr_spend_seg = float(r.get("spend_curr", 0.0))
                        base_rev_seg = float(r.get("revenue_base", 0.0))
                        curr_rev_seg = float(r.get("revenue_curr", 0.0))
                        base_roas_seg = (base_rev_seg / base_spend_seg) if base_spend_seg > 0 else 0.0
                        curr_roas_seg = (curr_rev_seg / curr_spend_seg) if curr_spend_seg > 0 else 0.0
                        roas_pct = pct_change(base_roas_seg, curr_roas_seg)

                        # classify low CTR candidates
                        if base_impr + curr_impr > 0:
                            if ctr_pct < -5:  # at least 5% drop
                                low_ctr_segments.append({"segment": f"adset:{seg}", "ctr": curr_ctr_seg, "ctr_delta_pct": round(ctr_pct, 3), "z": z_seg, "p": p_seg})
                                drivers.append({
                                    "segment": f"adset:{seg}",
                                    "metric": "ctr",
                                    "baseline": round(base_ctr_seg, 6),
                                    "current": round(curr_ctr_seg, 6),
                                    "delta_pct": round(ctr_pct, 3),
                                    "z": z_seg,
                                    "p_value": p_seg,
                                    "severity": severity_label(ctr_pct),
                                    "confidence": round(confidence_from_p(p_seg), 3),
                                    "hypothesis": "creative_performance_or_hook_issue" if ctr_pct < -15 else "creative_attention_drop",
                                    "evidence_note": f"CTR changed {round(ctr_pct,1)}% (z={round(z_seg,2)})"
                                })

                        # low roas detection
                        if base_spend_seg + curr_spend_seg > 0:
                            if roas_pct < -10:  # 10% drop in ROAS
                                low_roas_segments.append({"segment": f"adset:{seg}", "roas": curr_roas_seg, "roas_delta_pct": round(roas_pct, 3)})
                                drivers.append({
                                    "segment": f"adset:{seg}",
                                    "metric": "roas",
                                    "baseline": round(base_roas_seg, 3),
                                    "current": round(curr_roas_seg, 3),
                                    "delta_pct": round(roas_pct, 3),
                                    "severity": severity_label(roas_pct),
                                    "confidence": round(roas_conf, 3),
                                    "hypothesis": "landing_or_offer_issue" if roas_pct < -30 else "creative_positioning_or_offer",
                                    "evidence_note": f"ROAS changed {round(roas_pct,1)}%"
                                })

                    result["low_ctr_segments"] = low_ctr_segments
                    result["low_roas_segments"] = low_roas_segments
                    result["drivers"] = drivers
                else:
                    result["low_ctr_segments"] = []
                    result["low_roas_segments"] = []
                    result["drivers"] = []
            else:
                # no date column -> fallback: use entire data to find weak adsets by absolute CTR and ROAS
                logger.info("No date available — running static segmentation checks")
                if grouping:
                    grp = df.groupby(grouping).agg({"impressions": "sum", "clicks": "sum", "spend": "sum", "revenue": "sum"}).reset_index()
                    grp["ctr"] = grp.apply(lambda r: (r["clicks"]/r["impressions"]) if r["impressions"]>0 else 0.0, axis=1)
                    low_ctrs = grp.sort_values("ctr").head(5)
                    result["low_ctr_segments"] = [{"segment": f"adset:{r[grouping]}", "ctr": r["ctr"]} for _, r in low_ctrs.iterrows()]
                    result["drivers"] = []
                else:
                    result["low_ctr_segments"] = []
                    result["low_roas_segments"] = []
                    result["drivers"] = []
        except Exception as ex:
            logger.exception("Insight diagnostics failed: %s", ex)
            # safe fallback
            result["drivers"] = []
            result["warnings"] = [{"message": f"diagnostics_failed: {ex}"}]

        # Add creative performance + top creatives (existing)
        if "creative_type" in df.columns:
            creative_perf = df.groupby("creative_type").agg({"spend": "sum", "revenue": "sum", "purchases": "sum"}).reset_index()
            creative_perf["roas"] = creative_perf.apply(lambda r: (r["revenue"]/r["spend"]) if r["spend"]>0 else 0.0, axis=1)
            creative_perf = creative_perf.sort_values("roas", ascending=False).to_dict(orient="records")
            result["creative_performance"] = creative_perf
            result["top_creatives"] = [{"key": r["creative_type"], "roas": r["roas"]} for r in creative_perf[:5]]
        else:
            result["creative_performance"] = []
            result["top_creatives"] = []

        logger.info("InsightAgent produced %d drivers; low_ctr=%d low_roas=%d", len(result.get("drivers", [])), len(result.get("low_ctr_segments", [])), len(result.get("low_roas_segments", [])))
        return result
