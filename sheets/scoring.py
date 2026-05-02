# sheets/scoring.py
# All scoring business logic lives here
# This module has no external dependencies

SCORE_MAP = {
    "Excellent" : 100,
    "Good With Enhancement" : 70,
    "Need Improvement" : 50,
    "Poor" : 0,
    "Yes" : 100,
    "No": 0,
}

WEIGHTS = {
    "ownership":         0.20,
    "handover":          0.05,
    "copyPaste":         0.05,
    "correctEmail":      0.10,
    "flow":              0.15,
    "clientApproach":    0.15,
    "supplierApproach":  0.10,
    "freshdesk":         0.05,
    "juniper":           0.15,
}
CRITERIA = [
    {"key": "ownership",         "label": "Ownership + Follow-up",            "weight": 20, "type": "rating"},
    {"key": "handover",          "label": "Handover",                         "weight": 5,  "type": "yesno"},
    {"key": "copyPaste",         "label": "Copy/Paste (no copy-paste)",        "weight": 5,  "type": "yesno"},
    {"key": "correctEmail",      "label": "Correct Email",                    "weight": 10, "type": "yesno"},
    {"key": "flow",              "label": "Flow (FCR)",                       "weight": 15, "type": "rating"},
    {"key": "clientApproach",    "label": "Client Approach + Acknowledgment", "weight": 15, "type": "rating"},
    {"key": "supplierApproach",  "label": "Supplier Approach",                "weight": 10, "type": "rating"},
    {"key": "freshdesk",         "label": "FreshDesk Updates",                "weight": 5,  "type": "rating"},
    {"key": "juniper",           "label": "Juniper Updates",                  "weight": 15, "type": "rating"},
]
CASE_TYPES = [
    "Confirmation", "Amendment", "Cancellation Waiver", "Name Amendment",
    "Date Amendment", "Complaint", "Relocation", "On-Spot", "Special Request",
    "Payment Issue", "Booking Failure", "Information", "Loading Error",
    "Mapping Error", "Adding Supplement",
]
def calculate_score(data: dict, auto_fail: bool = False) -> float:
    """
    Calculate weighted quality score from evaluation data.
    
    Args:
        data: dictionary where keys are criterion names and values are rating strings
              e.g. {"ownership": "Excellent", "handover": "Yes", ...}
        auto_fail: if True, returns 0.0 regardless of ratings
    
    Returns:
        float between 0.0 and 100.0
    """
    if auto_fail:
        return 0.0

    total = 0.0
    for criterion_key, weight in WEIGHTS.items():
        raw_value = data.get(criterion_key, "")
        numeric_score = SCORE_MAP.get(raw_value, 0)
        total += numeric_score * weight

    return round(total, 1)


def kpi_percent(score: float) -> int:
    """
    Return KPI bonus percentage based on monthly average score.
    This is applied to the AVERAGE of all published evals in a month,
    not to individual evaluations.
    
    Args:
        score: float between 0 and 100
    
    Returns:
        int: 0, 5, 10, 25, or 40
    """
    if score > 85:   return 40
    if score >= 75:  return 25
    if score >= 60:  return 10
    if score >= 50:  return 5
    return 0


def kpi_tier(score: float) -> str:
    """
    Return tier name for colour coding in the UI.
    
    Args:
        score: float between 0 and 100
    
    Returns:
        str: one of 'excellent', 'good', 'fair', 'low', 'poor'
    """
    if score > 85:   return "excellent"
    if score >= 75:  return "good"
    if score >= 60:  return "fair"
    if score >= 50:  return "low"
    return "poor"


def tier_color(tier: str) -> str:
    """Return hex color for a given KPI tier — used in email notifications."""
    colors = {
        "excellent": "#10B981",
        "good":      "#3B82F6",
        "fair":      "#F59E0B",
        "low":       "#F97316",
        "poor":      "#EF4444",
    }
    return colors.get(tier, "#888888")
