from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename
import os

from logic import combined_decision, train_default_model, train_model_from_csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)

STATE = {
    "model": None,
    "samples": 0,
    "accuracy": 0.0,
    "source": "",
    "loss": [],
}

def ensure_model():
    if STATE["model"] is None:
        trained = train_default_model()
        STATE.update(trained)

@app.route("/")
def home():
    ensure_model()
    demo = combined_decision(usage=80, availability=35, model=STATE["model"])
    return render_template(
        "index.html",
        default_usage=80,
        default_availability=35,
        dataset_source=STATE["source"],
        dataset_samples=STATE["samples"],
        dataset_accuracy=f"{STATE['accuracy']*100:.1f}%",
        demo_overall=demo["overall_label"],
        demo_summary=demo["overall_summary"],
        demo_harmony=demo["harmony"],
        demo_fuzzy=demo["fuzzy"]["label"],
        demo_nn=demo["nn"]["label"],
    )

@app.route("/analyze", methods=["POST"])
def analyze():
    ensure_model()
    data = request.get_json(force=True)

    usage = float(data.get("usage", 0))
    availability = float(data.get("availability", 0))

    result = combined_decision(usage=usage, availability=availability, model=STATE["model"])

    payload = {
        "overall_label": result["overall_label"],
        "overall_summary": result["overall_summary"],
        "harmony": result["harmony"],
        "fuzzy_label": result["fuzzy"]["label"],
        "fuzzy_explanation": result["fuzzy"]["explanation"],
        "fuzzy_score": result["fuzzy"]["score"],
        "nn_label": result["nn"]["label"],
        "nn_confidence": round(result["nn"]["confidence"] * 100, 1),
        "usage_text": _usage_text(usage),
        "availability_text": _availability_text(availability),
        "dataset_source": STATE["source"],
        "dataset_samples": STATE["samples"],
        "dataset_accuracy": f"{STATE['accuracy']*100:.1f}%",
    }
    return jsonify(payload)

@app.route("/upload-dataset", methods=["POST"])
def upload_dataset():
    ensure_model()

    if "dataset" not in request.files:
        return jsonify({"ok": False, "message": "No file selected."}), 400

    file = request.files["dataset"]
    if not file.filename:
        return jsonify({"ok": False, "message": "No file selected."}), 400

    filename = secure_filename(file.filename)
    tmp_path = os.path.join(UPLOAD_DIR, filename)
    file.save(tmp_path)

    try:
        trained = train_model_from_csv(tmp_path)
        STATE.update(trained)
        return jsonify({
            "ok": True,
            "message": f"Dataset loaded successfully from {filename}. Neural network retrained.",
            "samples": STATE["samples"],
            "accuracy": f"{STATE['accuracy']*100:.1f}%",
            "source": STATE["source"],
        })
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

def _usage_text(usage: float) -> str:
    if usage < 50:
        return "low"
    if usage < 100:
        return "moderate"
    return "high"

def _availability_text(avail: float) -> str:
    if avail < 40:
        return "scarce"
    if avail < 70:
        return "moderate"
    return "abundant"

if __name__ == "__main__":
    ensure_model()
    app.run(debug=True)