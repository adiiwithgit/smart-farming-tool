"""
Irrigation advice and climate-risk assessment.

Both are rule-based on live weather data (see main.py's /api/weather proxy).
This is intentional — a farmer needs a decision NOW, and simple, explainable
thresholds are more trustworthy and faster than an ML model here. If your
team later trains a model for irrigation timing specifically, swap
irrigation_advice() the same way vision_model.py's stubs work.
"""

from typing import Dict, Any, List


def irrigation_advice(
    soil_moisture_pct: float,
    forecast_precip_mm_next_3d: float,
    current_temp_c: float,
) -> Dict[str, Any]:
    reasons: List[str] = []

    if soil_moisture_pct < 20:
        urgency = "high"
        reasons.append(f"Soil moisture is critically low ({soil_moisture_pct}%).")
    elif soil_moisture_pct < 40:
        urgency = "medium"
        reasons.append(f"Soil moisture is below optimal ({soil_moisture_pct}%).")
    else:
        urgency = "low"
        reasons.append(f"Soil moisture is adequate ({soil_moisture_pct}%).")

    if forecast_precip_mm_next_3d > 15:
        if urgency != "low":
            urgency = "low"
        reasons.append(f"Rain expected soon ({forecast_precip_mm_next_3d}mm over next 3 days) — irrigation can likely wait.")
    else:
        reasons.append("Little to no rain expected in the next 3 days.")

    if current_temp_c > 38 and urgency != "low":
        urgency = "high"
        reasons.append(f"High temperature ({current_temp_c}°C) increases water loss — act sooner.")

    action = {
        "high": "Irrigate within the next 24 hours.",
        "medium": "Plan to irrigate in the next 2-3 days; monitor soil moisture daily.",
        "low": "No irrigation needed right now.",
    }[urgency]

    return {"urgency": urgency, "action": action, "reasons": reasons}


def climate_risk_assessment(
    max_temp_forecast_c: float,
    total_precip_next_7d_mm: float,
    avg_precip_last_30d_mm: float,
) -> Dict[str, Any]:
    risks = []

    if max_temp_forecast_c >= 42:
        risks.append({
            "type": "Heatwave",
            "severity": "high",
            "detail": f"Forecast max temperature of {max_temp_forecast_c}°C — crop heat stress likely.",
            "action": "Irrigate early morning/evening, consider shade netting for sensitive crops.",
        })
    elif max_temp_forecast_c >= 38:
        risks.append({
            "type": "Heatwave",
            "severity": "moderate",
            "detail": f"Forecast max temperature of {max_temp_forecast_c}°C.",
            "action": "Monitor crops for wilting during peak afternoon hours.",
        })

    if total_precip_next_7d_mm >= 100:
        risks.append({
            "type": "Flood risk",
            "severity": "high",
            "detail": f"{total_precip_next_7d_mm}mm of rain expected in the next 7 days.",
            "action": "Ensure field drainage channels are clear; delay fertilizer application.",
        })

    if avg_precip_last_30d_mm < 20 and total_precip_next_7d_mm < 10:
        risks.append({
            "type": "Drought risk",
            "severity": "moderate" if avg_precip_last_30d_mm > 5 else "high",
            "detail": f"Only {avg_precip_last_30d_mm}mm average rainfall over the last 30 days, little relief forecast.",
            "action": "Prioritize water-efficient irrigation (drip); consider drought-tolerant crop varieties next season.",
        })

    if not risks:
        risks.append({
            "type": "Normal conditions",
            "severity": "none",
            "detail": "No major climate risks detected in current forecast data.",
            "action": "Continue standard crop management.",
        })

    return {"risks": risks}
