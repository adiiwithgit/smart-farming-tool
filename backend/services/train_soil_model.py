"""
Soil Health Model - Dataset Generation + Training

WHY SYNTHETIC DATA:
There's no real-world labeled dataset available for (temperature, humidity,
moisture, rainfall) -> soil health category. Rather than leave this feature
unbuilt, we generate a synthetic dataset using well-established agronomic
thresholds (ideal moisture ranges, humidity comfort bands for most crops,
temperature stress ranges, and rainfall adequacy). This is a legitimate and
common approach for prototyping an ML pipeline when no real sensor dataset
exists yet — but it should be described honestly as synthetic/heuristic-based
training data, not real-world calibrated agricultural data, if asked during
judging. It demonstrates a genuinely working, trained ML classifier (not a
hardcoded if/else), which your team can later retrain on real sensor logs
once you start collecting them from the field.

WHAT THIS SCRIPT DOES:
1. Generates 8,000 synthetic samples of (temperature, humidity, moisture, rainfall)
2. Labels each sample Good/Fair/Poor using a scored combination of how close
   each reading is to its agronomic ideal range, plus randomness so the
   classes aren't trivially separable (forces the model to actually learn
   patterns, not just memorize a threshold rule)
3. Trains a RandomForestClassifier
4. Evaluates accuracy on a held-out test set
5. Saves the trained model + a label encoder to soil_health_model.joblib
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import joblib

np.random.seed(42)
N_SAMPLES = 8000


def generate_synthetic_data(n=N_SAMPLES):
    # Sample each feature from a realistic range for Indian agricultural conditions
    temperature = np.random.uniform(10, 45, n)      # Celsius
    humidity = np.random.uniform(20, 100, n)         # %
    moisture = np.random.uniform(0, 100, n)          # % soil moisture
    rainfall = np.random.gamma(2, 5, n)  # mm, right-skewed like real rainfall
    rainfall = np.clip(rainfall, 0, 60)

    def score_temperature(t):
        # Ideal range roughly 20-32C for most crops; penalize distance from it
        if 20 <= t <= 32:
            return 1.0
        distance = min(abs(t - 20), abs(t - 32))
        return max(0.0, 1.0 - distance / 15)

    def score_humidity(h):
        if 50 <= h <= 80:
            return 1.0
        distance = min(abs(h - 50), abs(h - 80))
        return max(0.0, 1.0 - distance / 30)

    def score_moisture(m):
        if 40 <= m <= 70:
            return 1.0
        distance = min(abs(m - 40), abs(m - 70))
        return max(0.0, 1.0 - distance / 35)

    def score_rainfall(r):
        if 5 <= r <= 25:
            return 1.0
        distance = min(abs(r - 5), abs(r - 25))
        return max(0.0, 1.0 - distance / 20)

    composite_scores = []
    for t, h, m, r in zip(temperature, humidity, moisture, rainfall):
        composite = (
            0.30 * score_temperature(t)
            + 0.25 * score_humidity(h)
            + 0.30 * score_moisture(m)
            + 0.15 * score_rainfall(r)
        )
        # add noise so classes overlap realistically, forcing real learning
        composite += np.random.normal(0, 0.07)
        composite_scores.append(np.clip(composite, 0, 1))

    composite_scores = np.array(composite_scores)
    # Quantile-based cutoffs guarantee a sensible, balanced class split
    # regardless of how the raw composite score happens to distribute:
    # bottom 20% -> Poor, middle 45% -> Fair, top 35% -> Good
    poor_cutoff = np.quantile(composite_scores, 0.20)
    good_cutoff = np.quantile(composite_scores, 0.65)

    labels = []
    for score in composite_scores:
        if score >= good_cutoff:
            labels.append("Good")
        elif score >= poor_cutoff:
            labels.append("Fair")
        else:
            labels.append("Poor")

    df = pd.DataFrame({
        "temperature": temperature,
        "humidity": humidity,
        "moisture": moisture,
        "rainfall": rainfall,
        "soil_health": labels,
    })
    return df


def main():
    print("Generating synthetic dataset...")
    df = generate_synthetic_data()
    print(f"Class distribution:\n{df['soil_health'].value_counts()}\n")

    X = df[["temperature", "humidity", "moisture", "rainfall"]]
    y = df["soil_health"]

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    print("Training RandomForestClassifier...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nTest accuracy: {acc:.3f}\n")
    print(classification_report(y_test, y_pred, target_names=encoder.classes_))

    print("Feature importances:")
    for feat, imp in zip(X.columns, model.feature_importances_):
        print(f"  {feat}: {imp:.3f}")

    joblib.dump({"model": model, "encoder": encoder}, "soil_health_model.joblib")
    print("\nSaved model to soil_health_model.joblib")


if __name__ == "__main__":
    main()
