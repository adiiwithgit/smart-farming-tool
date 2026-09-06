"""
Soil Health prediction — pure Python, no scikit-learn/pandas/joblib needed
at runtime. This is a multinomial logistic regression that WAS trained
using scikit-learn (see train_logreg_export_v2.py for the full training
code and methodology), but its learned weights are hardcoded below so it
runs anywhere with zero ML library dependencies — useful here since
scikit-learn has no 32-bit Windows wheels and needs a C++ compiler to
build from source.

TRAINING DATA DISCLOSURE: trained on synthetic data generated from
documented agronomic thresholds (ideal moisture/humidity/temperature/
rainfall ranges), not real-world sensor logs — see train_logreg_export_v2.py
docstring for full reasoning. Retrain on real data once your team starts
collecting field sensor readings.
"""

import math

CLASSES = ['Fair', 'Good', 'Poor']
SCALER_MEAN = [0.7445751041795934, 0.7281043804435939, 0.6530748846251871, 0.961896456603411]
SCALER_SCALE = [0.2635296092468306, 0.297819124102297, 0.33845418022827145, 0.08981432996546854]
COEF = [
    [0.05440813262721146, 0.029791468353630786, 0.021353199995765598, 0.04062791109273012],
    [1.9559001245572172, 1.8485758744709773, 2.5156188645855253, 0.276583193813975],
    [-2.0103082571844073, -1.878367342824621, -2.536972064581285, -0.3172111049067055],
]
INTERCEPT = [1.7634020547060205, 0.021587785301940516, -1.784989840008116]


def _score_temperature(t: float) -> float:
    if 20 <= t <= 32:
        return 1.0
    distance = min(abs(t - 20), abs(t - 32))
    return max(0.0, 1.0 - distance / 15)


def _score_humidity(h: float) -> float:
    if 50 <= h <= 80:
        return 1.0
    distance = min(abs(h - 50), abs(h - 80))
    return max(0.0, 1.0 - distance / 30)


def _score_moisture(m: float) -> float:
    if 40 <= m <= 70:
        return 1.0
    distance = min(abs(m - 40), abs(m - 70))
    return max(0.0, 1.0 - distance / 35)


def _score_rainfall(r: float) -> float:
    if 5 <= r <= 25:
        return 1.0
    distance = min(abs(r - 5), abs(r - 25))
    return max(0.0, 1.0 - distance / 20)


def _softmax(scores):
    max_score = max(scores)
    exp_scores = [math.exp(s - max_score) for s in scores]
    total = sum(exp_scores)
    return [e / total for e in exp_scores]


def predict_soil_health(temperature: float, humidity: float, moisture: float, rainfall: float) -> dict:
    raw_features = [
        _score_temperature(temperature),
        _score_humidity(humidity),
        _score_moisture(moisture),
        _score_rainfall(rainfall),
    ]

    # standardize using the training set's mean/scale
    scaled = [(raw_features[i] - SCALER_MEAN[i]) / SCALER_SCALE[i] for i in range(4)]

    # linear combination for each class
    class_scores = []
    for class_idx in range(len(CLASSES)):
        score = INTERCEPT[class_idx] + sum(
            COEF[class_idx][j] * scaled[j] for j in range(4)
        )
        class_scores.append(score)

    probabilities = _softmax(class_scores)
    best_idx = probabilities.index(max(probabilities))
    label = CLASSES[best_idx]
    confidence = round(probabilities[best_idx] * 100, 1)

    advice = {
        "Good": "Soil conditions are favorable. Maintain current irrigation and monitoring schedule.",
        "Fair": "Soil conditions are workable but not optimal — check moisture and consider adjusting irrigation timing.",
        "Poor": "Soil conditions are stressed. Investigate moisture, temperature extremes, or drainage issues promptly.",
    }.get(label, "Monitor conditions closely.")

    return {
        "status": "ok",
        "soil_health": label,
        "confidence": confidence,
        "advice": advice,
    }
