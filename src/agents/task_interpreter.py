from typing import Dict, Any
import re
from datetime import datetime


# A small rule-based TaskInterpreter. Add rules as needed.
class TaskInterpreter:
def __init__(self, now=None):
self.now = now


def parse(self, task: str) -> Dict[str, Any]:
t = task.lower()
intent: Dict[str, Any] = {"metric": None, "mode": "diagnostic", "time_window": None, "segment": None}


# metric detection
if "roas" in t or "return on ad" in t:
intent["metric"] = "roas"
elif "ctr" in t or "click" in t:
intent["metric"] = "ctr"
elif "spend" in t or "cpa" in t or "cost" in t:
intent["metric"] = "spend"
else:
intent["metric"] = "roas"


# mode
if any(x in t for x in ["improve", "increase", "optimize"]):
intent["mode"] = "optimization"
elif any(x in t for x in ["why", "why did", "drop", "decrease", "fall"]):
intent["mode"] = "diagnostic"


# time window detection: numbers + days/weeks/months
m = re.search(r"last (\d+) days", t)
if m:
intent["time_window"] = int(m.group(1))
elif "last 7 days" in t or "7 days" in t:
intent["time_window"] = 7
elif "yesterday" in t:
intent["time_window"] = 1
elif "last 30 days" in t or "30 days" in t:
intent["time_window"] = 30
else:
# default window for diagnostics
intent["time_window"] = 14


# segment extraction (simple heuristics)
if "broad" in t:
intent["segment"] = "Broad"
elif "lookalike" in t or "lal" in t:
intent["segment"] = "Lookalike"
elif "retarget" in t or "retargeting" in t:
intent["segment"] = "Retarget"


return intent