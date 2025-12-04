# src/agents/evaluator_agent.py
from typing import Any, Dict, List
from src.utils.logger import get_logger
import math

logger = get_logger("evaluator_agent_v3")

def _score_severity(sev: str) -> float:
    mapping = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
    return mapping.get(sev, 0.2)

def _combine_scores(*args):
    # simple weighted product/sum heuristic
    vals = [max(0.0, min(1.0, float(v))) for v in args]
    # average for now
    return sum(vals) / len(vals) if vals else 0.0

class EvaluatorAgent:
    """
    Evaluator v3:
      - Validates drivers (hypotheses) from InsightAgent.
      - Produces per-variant scoring and an overall evaluation JSON with:
          hypothesis, evidence, impact, confidence
    """

    def __init__(self, config: Dict[str, Any] = None):
        cfg = {"min_confidence": 0.2}
        if config:
            cfg.update(config)
        self.config = cfg

    def _validate_driver(self, driver: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given a driver (from InsightAgent), produce an evaluation block:
        { hypothesis, evidence: {...}, impact, confidence }
        """
        try:
            seg = driver.get("segment")
            metric = driver.get("metric", "ctr")
            delta = float(driver.get("delta_pct", 0.0))
            conf = float(driver.get("confidence", 0.0))
            sev = driver.get("severity", "low")
            hypothesis = driver.get("hypothesis", "unspecified")

            # severity score
            sev_score = _score_severity(sev)  # 0..1
            # confidence base -> clip
            conf = max(0.0, min(1.0, conf))
            # impact heuristic: larger delta & severity -> bigger impact
            impact_score = _combine_scores(min(1.0, abs(delta) / 100.0), sev_score)
            # final confidence mixes measured confidence and sample-size heuristic
            final_confidence = _combine_scores(conf, 0.5 + 0.5 * sev_score)  # simple heuristic

            evidence = {
                "segment": seg,
                "metric": metric,
                "delta_pct": delta,
                "baseline": driver.get("baseline"),
                "current": driver.get("current"),
                "z": driver.get("z"),
                "p_value": driver.get("p_value", driver.get("p", None))
            }

            result = {
                "hypothesis": hypothesis,
                "evidence": evidence,
                "impact": "high" if impact_score >= 0.5 else ("medium" if impact_score >= 0.25 else "low"),
                "impact_score": round(impact_score, 3),
                "confidence": round(final_confidence, 3),
                "raw": driver
            }
            return result
        except Exception as ex:
            logger.exception("Driver validation failed: %s", ex)
            return {"hypothesis": "error", "evidence": {}, "impact": "low", "confidence": 0.0, "raw": {}}

    def _score_variant(self, variant: Dict[str, Any], driver_eval: Dict[str, Any]) -> Dict[str, Any]:
        # variant expected_metric vs driver metric
        expected = variant.get("expected_metric")
        metric = driver_eval.get("evidence", {}).get("metric")
        # base match score
        match = 1.0 if expected == metric else 0.5
        # use impact & confidence to scale
        impact = driver_eval.get("impact_score", driver_eval.get("impact_score", 0.0))
        conf = driver_eval.get("confidence", 0.0)
        # variant score heuristic
        score = (0.6 * match) + (0.4 * impact) * conf
        # clamp
        score = max(0.0, min(100.0, score * 100))
        return {
            "variant_id": variant.get("id"),
            "score": round(score, 2),
            "explanation": f"match={match}, impact={impact}, confidence={conf}"
        }

    def evaluate(self, creative_output: Dict[str, Any], data_package: Dict[str, Any], insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a structured evaluation:
        {
          score: int,
          components: {...},
          hypothesis_evaluations: [ ... ],
          variant_analysis: [ ... ],
          recommendations: [ ... ]
        }
        """
        try:
            drivers = insights.get("drivers", [])
            driver_evals = [self._validate_driver(d) for d in drivers]

            # base score: presence of evidence and variants
            base_score = 40
            if drivers:
                base_score += 20
            n_variants = creative_output.get("meta", {}).get("n_variants", len(creative_output.get("variants", [])))
            base_score += min(40, n_variants * 2)  # up to +40

            # variant-level scoring
            variant_analysis = []
            variants = creative_output.get("variants", [])
            avg_variant = 0.0
            if drivers and variants:
                # evaluate each variant against first matching driver (simple)
                for v in variants:
                    # find first driver_eval matching the variant's target_segment or use top driver
                    matched = None
                    for de in driver_evals:
                        seg = de.get("evidence", {}).get("segment", "")
                        if seg and seg in v.get("target_segment", ""):
                            matched = de
                            break
                    if not matched and driver_evals:
                        matched = driver_evals[0]
                    if matched:
                        va = self._score_variant(v, matched)
                        variant_analysis.append(va)
                        avg_variant += va["score"]
                if variant_analysis:
                    avg_variant = avg_variant / len(variant_analysis)
            else:
                # fallback scoring: assign neutral scores to variants
                for v in variants:
                    variant_analysis.append({"variant_id": v.get("id"), "score": 25.0, "explanation": "no drivers"})
                avg_variant = 25.0

            # overall score mixing base and avg_variant
            final_score = int(round(min(100, base_score * 0.6 + avg_variant * 0.4)))
            # recommendations: pick top variant by score
            sorted_vars = sorted(variant_analysis, key=lambda x: x["score"], reverse=True)[:3]
            recommendations = []
            if sorted_vars:
                recommendations.append({
                    "action": "run_ab_test",
                    "variant_id": sorted_vars[0]["variant_id"],
                    "expected_score": sorted_vars[0]["score"],
                    "rationale": sorted_vars[0]["explanation"]
                })

            logger.info("Evaluator produced final_score=%s (base=%s avg_variant=%s)", final_score, base_score, avg_variant)
            return {
                "score": final_score,
                "components": {"base": base_score, "n_variants": n_variants},
                "hypothesis_evaluations": driver_evals,
                "variant_analysis": variant_analysis,
                "recommendations": recommendations
            }
        except Exception as ex:
            logger.exception("Evaluator failed: %s", ex)
            return {"score": 0, "components": {}, "messages": [str(ex)]}
