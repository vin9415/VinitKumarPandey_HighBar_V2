# src/agents/creative_agent.py

from typing import Dict, List, Any
from src.utils.logger import get_logger
import random
import html
import uuid

logger = get_logger("creative_agent_v3")

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

DEFAULT_FORMATS = [
    "image", "video_short", "carousel", "story",
    "testimonials", "ugc", "longform_video", "headline_experiments"
]

TEMPLATES = {
    "PAS": {
        "headline": "{problem}? Try {solution}.",
        "body": "Problem: {problem}. Agitation: {agitation}. Solution: {solution}. CTA: {cta}"
    },
    "AIDA": {
        "headline": "{attention} — {interest}",
        "body": "Desire: {desire}. Action: {cta}"
    },
    "FAB": {
        "headline": "Feature: {feature} — Benefit: {benefit}",
        "body": "{feature}. This means {benefit}. Try now: {cta}"
    },
    "SocialProof": {
        "headline": "{stat}% of users say {claim}",
        "body": "{claim}. See how others experienced it. CTA: {cta}"
    }
}

VISUAL_DIRECTIVES = {
    "image": "High-contrast lifestyle still showing product on model; single-frame CTA overlay.",
    "video_short": "15s demo with strong hook; end with CTA card. Optimized for reels.",
    "carousel": "4-slide carousel: benefit → feature → proof → CTA.",
    "story": "Vertical format, quick demo, swipe CTA.",
    "testimonials": "Customer testimonials with trust badges.",
    "ugc": "Raw-feel UGC clip, minimal editing, authentic tone.",
    "longform_video": "Narrative-style longer demo with deeper storytelling.",
    "headline_experiments": "6 headline variants for rapid A/B testing."
}

# ---------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------

def _clean_text(s: str) -> str:
    if s is None:
        return ""
    s = html.unescape(str(s))
    s = s.replace("â€", "'").replace("â€™", "'").replace("â€“", "-").replace("â€‘", "-")
    return s

def _short_cta():
    return random.choice(["Shop now", "Learn more", "Get 20% off", "Try now", "Upgrade today"])

# ---------------------------------------------------------------------
# CREATIVE AGENT
# ---------------------------------------------------------------------

class CreativeAgent:
    """
    CreativeAgent v3 — production-style:
    • Generates *driver-tied* creatives
    • Produces *executive summary* aligned with insight drivers
    • Ensures NO generic creatives
    """

    def __init__(self, config: Dict[str, Any] = None):
        cfg = {"formats": DEFAULT_FORMATS, "variants_per_segment": 3, "max_variants": 30}
        if config:
            cfg.update(config)

        self.config = cfg
        self.formats = cfg["formats"]
        self.variants_per_segment = cfg["variants_per_segment"]
        self.max_variants = cfg["max_variants"]

    # -----------------------------------------------------------------
    # EXECUTIVE SUMMARY — COMPLETELY FIXED VERSION
    # -----------------------------------------------------------------
    def _exec_summary(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        observations = []
        opportunities = []
        risks = []

        # Observations
        if insights.get("avg_ctr"):
            observations.append(f"Global CTR: {insights['avg_ctr']:.4f}")
        if insights.get("avg_roas"):
            observations.append(f"Global ROAS: {insights['avg_roas']:.2f}")

        # Drivers
        drivers = insights.get("drivers", [])
        if drivers:
            opportunities.append(f"{len(drivers)} performance drivers detected:")
            for d in drivers[:3]:
                opportunities.append(
                    f"{d['segment']} — {d['metric']} changed {d['delta_pct']}% (severity: {d['severity']})"
                )
        else:
            opportunities.append("No clear metric-driven issues — run exploratory UGC + video testing.")

        # Risks
        if insights.get("trend", {}).get("roas_trend_slope", 0) < 0:
            risks.append("ROAS trend decreasing — avoid aggressive scaling.")
        if not risks:
            risks.append("Low statistical confidence in smaller segments — use rolling windows.")

        # Build SAFE summary (no star-unpacking)
        summary_lines = ["EXECUTIVE SUMMARY", "", "Observations:"]
        for o in observations:
            summary_lines.append(f"- {o}")

        summary_lines.append("")
        summary_lines.append("Opportunities:")
        for o in opportunities:
            summary_lines.append(f"- {o}")

        summary_lines.append("")
        summary_lines.append("Risks & Considerations:")
        for r in risks:
            summary_lines.append(f"- {r}")

        return {
            "text": "\n".join(summary_lines),
            "observations": observations,
            "opportunities": opportunities,
            "risks": risks,
        }

    # -----------------------------------------------------------------
    # VARIANT CREATION
    # -----------------------------------------------------------------
    def _build_headline_body(self, template_key: str, driver: Dict[str, Any]):
        tpl = TEMPLATES.get(template_key, TEMPLATES["PAS"])

        headline = tpl["headline"].format(
            problem=driver.get("issue", "low performance"),
            solution=driver.get("solution", "test new creative direction"),
            attention=driver.get("issue", "low engagement"),
            interest=driver.get("solution", "improved creative concept"),
            feature=driver.get("feature", "clear product value"),
            benefit=driver.get("benefit", "higher engagement"),
            stat=driver.get("stat", "80"),
            claim=driver.get("claim", "customers prefer this product")
        )[:140]

        body = tpl["body"].format(
            problem=driver.get("issue", ""),
            agitation=driver.get("agitation", "current creatives are not resonating"),
            solution=driver.get("solution", ""),
            desire=driver.get("benefit", "improved funnel performance"),
            feature=driver.get("feature", "value-led messaging"),
            benefit=driver.get("benefit", ""),
            claim=driver.get("claim", ""),
            cta=_short_cta()
        )

        return headline, _clean_text(body)

    def _make_variant(self, segment: str, driver: Dict[str, Any], idx: int):
        fmt = self.formats[idx % len(self.formats)]
        template_key = random.choice(list(TEMPLATES.keys()))
        headline, body = self._build_headline_body(template_key, driver)

        variant = {
            "id": f"{segment.replace(':', '_')}_v{idx+1}_{uuid.uuid4().hex[:6]}",
            "target_segment": segment,
            "angle": template_key,
            "format": fmt,
            "headline": headline,
            "body": body,
            "visual_direction": VISUAL_DIRECTIVES.get(fmt, "Use strong product-first creative"),
            "expected_metric": driver.get("expected_metric", "ctr"),
            "rationale": driver
        }
        return variant

    # -----------------------------------------------------------------
    # MAIN OUTPUT FUNCTION
    # -----------------------------------------------------------------
    def create_output(self, insights: Dict[str, Any], plan: List[str]):
        if "error" in insights:
            return {"status": "error", "message": insights["error"], "variants": []}

        summary = self._exec_summary(insights)
        variants = []

        # Drivers (low_ctr, low_roas)
        drivers = {}

        for d in insights.get("low_ctr_segments", []):
            drivers[d["segment"]] = {
                "issue": "low_ctr",
                "ctr": d.get("ctr"),
                "solution": "UGC/video/testimonial to improve attention",
                "severity": "medium"
            }

        for d in insights.get("low_roas_segments", []):
            drivers[d["segment"]] = {
                "issue": "low_roas",
                "roas": d.get("roas"),
                "solution": "offer + landing page test",
                "severity": "high"
            }

        if not drivers:
            # fallback driver
            drivers["audience:general"] = {
                "issue": "exploratory",
                "solution": "run fast A/B tests with high-performing creative formats",
                "severity": "low"
            }

        # generate variants
        idx = 0
        for seg, drv in drivers.items():
            for _ in range(self.variants_per_segment):
                if len(variants) >= self.max_variants:
                    break
                variants.append(self._make_variant(seg, drv, idx))
                idx += 1

        logger.info("CreativeAgent v3 produced %d variants", len(variants))

        return {
            "status": "ok",
            "summary": summary["text"],
            "summary_structured": summary,
            "variants": variants,
            "plan_reference": plan,
            "meta": {"n_variants": len(variants)},
        }
