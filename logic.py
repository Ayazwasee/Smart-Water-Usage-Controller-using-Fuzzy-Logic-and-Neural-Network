import csv
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

LABELS = [
    "Critical conservation mode",
    "High conservation needed",
    "Balanced usage recommended",
    "Moderate usage allowed",
    "Normal flow allowed",
]

SEVERITY_ORDER = {label: i for i, label in enumerate(LABELS)}

def label_from_index(idx: int) -> str:
    return LABELS[int(max(0, min(len(LABELS) - 1, idx)))]

def severity_score(label: str) -> int:
    return SEVERITY_ORDER.get(label, 2)

def triangular(x: float, a: float, b: float, c: float) -> float:
    # Robust triangular membership function
    if a == b == c:
        return 1.0 if x == a else 0.0
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if b == a:
        left = 1.0
    else:
        left = (x - a) / (b - a)
    if c == b:
        right = 1.0
    else:
        right = (c - x) / (c - b)
    return float(max(0.0, min(left, right)))

def membership_usage(usage: float) -> Dict[str, float]:
    return {
        "low": triangular(usage, 0, 0, 50),
        "medium": triangular(usage, 30, 75, 120),
        "high": triangular(usage, 80, 150, 150),
    }

def membership_availability(availability: float) -> Dict[str, float]:
    return {
        "scarce": triangular(availability, 0, 0, 40),
        "moderate": triangular(availability, 30, 60, 90),
        "abundant": triangular(availability, 70, 100, 100),
    }

def fuzzy_recommendation(usage: float, availability: float) -> Dict[str, object]:
    u = membership_usage(usage)
    a = membership_availability(availability)

    # Rule strengths
    rules = {
        "Critical conservation mode": min(u["high"], a["scarce"]),
        "High conservation needed": max(
            min(u["high"], a["moderate"]),
            min(u["medium"], a["scarce"])
        ),
        "Balanced usage recommended": min(u["medium"], a["moderate"]),
        "Moderate usage allowed": max(
            min(u["low"], a["moderate"]),
            min(u["medium"], a["abundant"])
        ),
        "Normal flow allowed": min(u["low"], a["abundant"]),
    }

    # Weighted crisp score (more conservative labels weighted lower)
    weights = {
        "Critical conservation mode": 0,
        "High conservation needed": 25,
        "Balanced usage recommended": 50,
        "Moderate usage allowed": 75,
        "Normal flow allowed": 100,
    }

    numerator = sum(rules[label] * weights[label] for label in LABELS)
    denominator = sum(rules.values())

    if denominator == 0:
        # fallback: pick the most conservative based on inputs
        score = 50.0
        chosen = "Balanced usage recommended"
    else:
        score = numerator / denominator
        if score < 12.5:
            chosen = "Critical conservation mode"
        elif score < 37.5:
            chosen = "High conservation needed"
        elif score < 62.5:
            chosen = "Balanced usage recommended"
        elif score < 85:
            chosen = "Moderate usage allowed"
        else:
            chosen = "Normal flow allowed"

    explanation = explain_fuzzy_choice(chosen, usage, availability, u, a)
    return {
        "label": chosen,
        "score": round(score, 2),
        "rules": rules,
        "usage_membership": u,
        "availability_membership": a,
        "explanation": explanation,
    }

def explain_fuzzy_choice(label: str, usage: float, availability: float, u: Dict[str, float], a: Dict[str, float]) -> str:
    if label == "Critical conservation mode":
        return "Usage is very high while availability is scarce, so the system should strongly conserve water."
    if label == "High conservation needed":
        return "Usage is on the high side and availability is not comfortable, so the system should reduce flow."
    if label == "Balanced usage recommended":
        return "The system is in a middle zone, so a balanced flow is the safest choice."
    if label == "Moderate usage allowed":
        return "Usage is not excessive and availability is acceptable, so moderate flow can continue."
    return "Usage is low and availability is abundant, so normal flow is allowed."

def summary_sentence(label: str) -> str:
    mapping = {
        "Critical conservation mode": "Emergency-level water saving is recommended.",
        "High conservation needed": "Reduce water flow immediately to avoid unnecessary consumption.",
        "Balanced usage recommended": "Keep water use controlled and balanced.",
        "Moderate usage allowed": "Water use can continue with a gentle level of caution.",
        "Normal flow allowed": "Conditions are comfortable and regular flow is suitable.",
    }
    return mapping[label]

def load_dataset(csv_path: str) -> Tuple[np.ndarray, np.ndarray]:
    X = []
    y = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [c.strip() for c in (reader.fieldnames or [])]
        lower_map = {c.lower().strip(): c for c in fieldnames}

        usage_key = lower_map.get("usage_liters") or lower_map.get("usage") or lower_map.get("water_usage")
        availability_key = lower_map.get("availability_percent") or lower_map.get("availability") or lower_map.get("water_availability")
        label_key = lower_map.get("recommendation_index") or lower_map.get("label") or lower_map.get("recommendation_label")

        if not usage_key or not availability_key or not label_key:
            raise ValueError(
                "CSV must include usage_liters, availability_percent, and recommendation_index or recommendation_label columns."
            )

        for row in reader:
            try:
                usage = float(row[usage_key])
                availability = float(row[availability_key])

                label_val = row[label_key]
                if label_key.lower() in ("recommendation_label", "label"):
                    # convert text to index
                    label_idx = SEVERITY_ORDER.get(str(label_val).strip(), 2)
                else:
                    label_idx = int(float(label_val))
                X.append([usage, availability])
                y.append(label_idx)
            except Exception:
                continue

    if not X:
        raise ValueError("No valid rows found in CSV.")
    return np.array(X, dtype=float), np.array(y, dtype=int)

def build_sample_dataset(n: int = 260, seed: int = 7) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = np.zeros((n, 2), dtype=float)
    y = np.zeros(n, dtype=int)
    for i in range(n):
        usage = float(rng.uniform(0, 150))
        availability = float(rng.uniform(0, 100))
        # heuristic teacher-data style labels
        score = 100 - (0.7 * usage + 0.3 * (100 - availability))
        if score < 25:
            label = 0
        elif score < 45:
            label = 1
        elif score < 60:
            label = 2
        elif score < 78:
            label = 3
        else:
            label = 4
        if rng.random() < 0.08:
            label = int(np.clip(label + rng.choice([-1, 1]), 0, 4))
        X[i] = [usage, availability]
        y[i] = label
    return X, y

class SimpleMLPClassifier:
    def __init__(self, input_dim: int = 2, hidden_dim: int = 10, output_dim: int = 5, seed: int = 42):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, 0.6, size=(input_dim, hidden_dim))
        self.b1 = np.zeros((1, hidden_dim))
        self.W2 = rng.normal(0, 0.6, size=(hidden_dim, output_dim))
        self.b2 = np.zeros((1, output_dim))
        self.mean_ = None
        self.std_ = None
        self.loss_history: List[float] = []

    def _standardize_fit(self, X: np.ndarray):
        self.mean_ = X.mean(axis=0, keepdims=True)
        self.std_ = X.std(axis=0, keepdims=True) + 1e-8

    def _standardize(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mean_) / self.std_

    @staticmethod
    def _relu(z):
        return np.maximum(0, z)

    @staticmethod
    def _relu_grad(z):
        return (z > 0).astype(float)

    @staticmethod
    def _softmax(z):
        z = z - np.max(z, axis=1, keepdims=True)
        exp_z = np.exp(z)
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    @staticmethod
    def _one_hot(y: np.ndarray, num_classes: int):
        out = np.zeros((len(y), num_classes), dtype=float)
        out[np.arange(len(y)), y] = 1.0
        return out

    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 900, lr: float = 0.04):
        X = np.array(X, dtype=float)
        y = np.array(y, dtype=int)
        self._standardize_fit(X)
        Xn = self._standardize(X)
        Y = self._one_hot(y, 5)

        n = Xn.shape[0]
        for epoch in range(epochs):
            z1 = Xn @ self.W1 + self.b1
            a1 = self._relu(z1)
            z2 = a1 @ self.W2 + self.b2
            a2 = self._softmax(z2)

            eps = 1e-9
            loss = -np.mean(np.sum(Y * np.log(a2 + eps), axis=1))
            self.loss_history.append(float(loss))

            dz2 = (a2 - Y) / n
            dW2 = a1.T @ dz2
            db2 = np.sum(dz2, axis=0, keepdims=True)

            da1 = dz2 @ self.W2.T
            dz1 = da1 * self._relu_grad(z1)
            dW1 = Xn.T @ dz1
            db1 = np.sum(dz1, axis=0, keepdims=True)

            self.W2 -= lr * dW2
            self.b2 -= lr * db2
            self.W1 -= lr * dW1
            self.b1 -= lr * db1

            # small learning-rate decay
            if epoch in {400, 700}:
                lr *= 0.7

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X = np.array(X, dtype=float)
        Xn = self._standardize(X)
        z1 = Xn @ self.W1 + self.b1
        a1 = self._relu(z1)
        z2 = a1 @ self.W2 + self.b2
        return self._softmax(z2)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

    def predict_single(self, usage: float, availability: float) -> Dict[str, object]:
        proba = self.predict_proba(np.array([[usage, availability]], dtype=float))[0]
        idx = int(np.argmax(proba))
        return {
            "label": label_from_index(idx),
            "confidence": float(np.max(proba)),
            "distribution": {label_from_index(i): float(proba[i]) for i in range(len(LABELS))}
        }

def train_model_from_csv(csv_path: str) -> Dict[str, object]:
    X, y = load_dataset(csv_path)
    model = SimpleMLPClassifier()
    model.fit(X, y)
    preds = model.predict(X)
    acc = float(np.mean(preds == y))
    return {
        "model": model,
        "samples": int(len(X)),
        "accuracy": acc,
        "source": os.path.basename(csv_path),
        "loss": model.loss_history,
    }

def train_default_model() -> Dict[str, object]:
    X, y = build_sample_dataset()
    model = SimpleMLPClassifier()
    model.fit(X, y)
    preds = model.predict(X)
    acc = float(np.mean(preds == y))
    return {
        "model": model,
        "samples": int(len(X)),
        "accuracy": acc,
        "source": "bundled sample dataset",
        "loss": model.loss_history,
    }

def combined_decision(usage: float, availability: float, model: Optional[SimpleMLPClassifier] = None) -> Dict[str, object]:
    fuzzy = fuzzy_recommendation(usage, availability)
    nn = None
    if model is not None:
        nn = model.predict_single(usage, availability)
    else:
        nn = {"label": "Model not loaded", "confidence": 0.0, "distribution": {}}

    # Conservative overall decision: take the more conservative of fuzzy and nn
    fuzzy_idx = severity_score(fuzzy["label"])
    nn_idx = severity_score(nn["label"]) if nn["label"] in SEVERITY_ORDER else fuzzy_idx
    overall_idx = min(fuzzy_idx, nn_idx)
    overall = label_from_index(overall_idx)

    if fuzzy["label"] == nn["label"]:
        harmony = "Both the fuzzy logic and neural network agree."
    else:
        harmony = "The two engines differ slightly, so the system keeps the safer recommendation."

    return {
        "fuzzy": fuzzy,
        "nn": nn,
        "overall_label": overall,
        "overall_summary": summary_sentence(overall),
        "harmony": harmony,
    }
