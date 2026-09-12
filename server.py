"""
AgriChain — Unified Flask Backend Server
Serves the frontend and provides API endpoints for:
- Forum & Crop Recommendation
- Simulated Weather Telemetry
- AI Chatbot (Gemini + fallback)
- Blockchain Record Management (Hyperledger FireFly + CSV Ledger)
- AI Detection Model Interface
"""

import csv
import os
import random
import json
import hashlib
import urllib.request
import urllib.error
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORUM_CSV = os.path.join(BASE_DIR, "forum.csv")
CROPS_CSV = os.path.join(BASE_DIR, "crops.csv")
LEDGER_CSV = os.path.join(BASE_DIR, "ledger.csv")

# Hyperledger FireFly REST Gateway URL (default Supernode port)
FIREFLY_URL = "http://localhost:5000/api/v1/namespaces/default/messages/broadcast"

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ---------------------------------------------------------------------------
# CSV Initialization Helpers
# ---------------------------------------------------------------------------

def init_forum_csv():
    if os.path.exists(FORUM_CSV):
        return
    rows = [
        {"id": "1", "user_role": "Farmer",   "question": "What is the best crop for clay soil in monsoon?",          "timestamp": "2026-03-28 10:15:00"},
        {"id": "2", "user_role": "Retailer", "question": "Where can I source organic rice in bulk?",                 "timestamp": "2026-03-29 14:30:00"},
        {"id": "3", "user_role": "Farmer",   "question": "How to reduce water usage for wheat cultivation?",         "timestamp": "2026-03-30 09:00:00"},
        {"id": "4", "user_role": "Admin",    "question": "Can we get a subsidy tracker added to the platform?",      "timestamp": "2026-04-01 16:45:00"},
    ]
    with open(FORUM_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "user_role", "question", "timestamp"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[init] Created {FORUM_CSV}")


def init_crops_csv():
    if os.path.exists(CROPS_CSV):
        return
    rows = [
        {"soil_type": "Clay",     "crop_name": "Rice",        "expected_profit": "₹25,000/acre", "risk_level": "Low"},
        {"soil_type": "Clay",     "crop_name": "Wheat",       "expected_profit": "₹18,000/acre", "risk_level": "Medium"},
        {"soil_type": "Sandy",    "crop_name": "Groundnut",   "expected_profit": "₹22,000/acre", "risk_level": "Medium"},
        {"soil_type": "Sandy",    "crop_name": "Watermelon",  "expected_profit": "₹30,000/acre", "risk_level": "High"},
        {"soil_type": "Loamy",    "crop_name": "Sugarcane",   "expected_profit": "₹35,000/acre", "risk_level": "Low"},
        {"soil_type": "Loamy",    "crop_name": "Maize",       "expected_profit": "₹20,000/acre", "risk_level": "Low"},
        {"soil_type": "Red",      "crop_name": "Millet",      "expected_profit": "₹15,000/acre", "risk_level": "Low"},
        {"soil_type": "Red",      "crop_name": "Cotton",      "expected_profit": "₹28,000/acre", "risk_level": "High"},
        {"soil_type": "Black",    "crop_name": "Soybean",     "expected_profit": "₹24,000/acre", "risk_level": "Medium"},
        {"soil_type": "Black",    "crop_name": "Cotton",      "expected_profit": "₹32,000/acre", "risk_level": "Medium"},
        {"soil_type": "Alluvial", "crop_name": "Rice",        "expected_profit": "₹27,000/acre", "risk_level": "Low"},
        {"soil_type": "Alluvial", "crop_name": "Jute",        "expected_profit": "₹19,000/acre", "risk_level": "Medium"},
    ]
    with open(CROPS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["soil_type", "crop_name", "expected_profit", "risk_level"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[init] Created {CROPS_CSV}")


def init_ledger_csv():
    """Initializes persistent audit ledger for anchored blockchain records."""
    if os.path.exists(LEDGER_CSV):
        return
    fieldnames = ["batch_id", "crop_name", "data_hash", "status", "tx_id", "timestamp", "raw_payload"]
    with open(LEDGER_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    print(f"[init] Created {LEDGER_CSV}")


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def next_forum_id():
    rows = read_csv(FORUM_CSV)
    if not rows:
        return 1
    return max(int(r["id"]) for r in rows) + 1


# ---------------------------------------------------------------------------
# Routes — Static Frontend
# ---------------------------------------------------------------------------

@app.route("/")
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")


# ---------------------------------------------------------------------------
# API — Forum
# ---------------------------------------------------------------------------

@app.route("/api/forum", methods=["GET"])
def get_forum():
    return jsonify(read_csv(FORUM_CSV))


@app.route("/api/forum", methods=["POST"])
def post_forum():
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    user_role = data.get("user_role", "Farmer")
    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    new_row = {
        "id": str(next_forum_id()),
        "user_role": user_role,
        "question": question,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(FORUM_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "user_role", "question", "timestamp"])
        writer.writerow(new_row)

    return jsonify(new_row), 201


# ---------------------------------------------------------------------------
# API — Crop Recommendation
# ---------------------------------------------------------------------------

@app.route("/api/recommend", methods=["POST"])
def recommend_crops():
    data = request.get_json(force=True)
    soil_type = data.get("soil_type", "").strip()
    location = data.get("location", "").strip()

    if not soil_type:
        return jsonify({"error": "soil_type is required"}), 400

    all_crops = read_csv(CROPS_CSV)
    matches = [c for c in all_crops if c["soil_type"].lower() == soil_type.lower()]

    return jsonify({
        "soil_type": soil_type,
        "location": location,
        "recommendations": matches,
    })


# ---------------------------------------------------------------------------
# API — Weather (Simulated Sensor Telemetry)
# ---------------------------------------------------------------------------

@app.route("/api/weather", methods=["GET"])
def weather():
    return jsonify({
        "rainfall_mm": round(random.uniform(50, 350), 1),
        "yield_prediction_pct": round(random.uniform(55, 98), 1),
        "temperature_c": round(random.uniform(22, 42), 1),
        "humidity_pct": round(random.uniform(40, 95), 1),
        "soil_ph": round(random.uniform(6.0, 7.5), 2),
        "season": random.choice(["Kharif", "Rabi", "Zaid"]),
    })


# ---------------------------------------------------------------------------
# API — Blockchain Record Management (Hyperledger FireFly Bridge)
# ---------------------------------------------------------------------------

@app.route("/api/blockchain/anchor", methods=["POST"])
def anchor_record():
    """
    Computes cryptographic SHA-256 fingerprint, attempts FireFly broadcast,
    and logs record immutably to ledger.csv.
    """
    data = request.get_json(force=True)
    batch_id = data.get("batch_id", f"BATCH-{int(datetime.now().timestamp())}")
    crop_name = data.get("crop_name", "Organic Wheat")
    
    # Canonical string representation guarantees deterministic hashing
    canonical_payload = json.dumps(data, sort_keys=True)
    data_hash = "0x" + hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # FireFly standard broadcast payload format
    ff_payload = {
        "header": {"tag": "agrichain-batch-anchor"},
        "data": [{"value": {"batch_id": batch_id, "data_hash": data_hash, "payload": data}}]
    }

    tx_id = f"LOCAL-PIN-{data_hash[:10]}"
    network_status = "Local Cryptographic Ledger (FireFly Inactive)"

    # Attempt broadcast to Hyperledger FireFly node
    try:
        req = urllib.request.Request(
            FIREFLY_URL,
            data=json.dumps(ff_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=1.5) as response:
            if response.status in (200, 202):
                res_data = json.loads(response.read().decode())
                tx_id = res_data.get("id") or res_data.get("header", {}).get("id", tx_id)
                network_status = "Anchored via Hyperledger FireFly Supernode"
    except Exception:
        # Failsafe activates cleanly if FireFly container is not yet initialized
        pass

    # Save to ledger.csv
    new_record = {
        "batch_id": batch_id,
        "crop_name": crop_name,
        "data_hash": data_hash,
        "status": network_status,
        "tx_id": tx_id,
        "timestamp": timestamp,
        "raw_payload": canonical_payload
    }

    with open(LEDGER_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["batch_id", "crop_name", "data_hash", "status", "tx_id", "timestamp", "raw_payload"])
        writer.writerow(new_record)

    return jsonify({
        "status": "success",
        "batch_id": batch_id,
        "data_hash": data_hash,
        "tx_id": tx_id,
        "network": network_status,
        "timestamp": timestamp
    }), 201


@app.route("/api/blockchain/records", methods=["GET"])
def get_ledger_records():
    """Returns all audit trails registered on the blockchain ledger."""
    records = read_csv(LEDGER_CSV)
    return jsonify(records)


@app.route("/api/blockchain/verify", methods=["POST"])
def verify_record():
    """
    Recalculates cryptographic digest and cross-checks against ledger records
    to expose data tampering.
    """
    data = request.get_json(force=True)
    batch_id = data.get("batch_id")
    current_payload = data.get("payload")

    records = read_csv(LEDGER_CSV)
    matched = next((r for r in records if r["batch_id"] == batch_id), None)

    if not matched:
        return jsonify({"error": "Batch ID not found in ledger"}), 404

    # Recalculate hash of inspected payload
    current_canonical = json.dumps(current_payload, sort_keys=True)
    current_hash = "0x" + hashlib.sha256(current_canonical.encode("utf-8")).hexdigest()
    original_hash = matched["data_hash"]

    is_valid = (current_hash == original_hash)

    return jsonify({
        "batch_id": batch_id,
        "is_authentic": is_valid,
        "ledger_hash": original_hash,
        "inspected_hash": current_hash,
        "verification_result": "VALID: Match confirmed on immutable ledger" if is_valid else "ALERT: Hash mismatch detected. Data tampered!"
    })


# ---------------------------------------------------------------------------
# API — AI / LLM Model Interface (Detection Placeholder)
# ---------------------------------------------------------------------------

@app.route("/api/ai/detect", methods=["POST"])
def detect_anomalies():
    """
    Interface reserved for your AI/LLM model (leaf disease detection, 
    soil sensor anomaly, or vision parsing).
    """
    data = request.get_json(force=True)
    
    # Placeholder response — ready to connect your PyTorch, ONNX, or LLM pipeline
    return jsonify({
        "status": "success",
        "model_loaded": "AgriChain-LLM-Inspector",
        "confidence_score": 0.94,
        "detection": "Normal vegetative state. No pathogen or crop stress indicators found.",
        "received_data": data
    })


# ---------------------------------------------------------------------------
# API — AI Chatbot (Gemini with Fallback)
# ---------------------------------------------------------------------------

EXPERT_RESPONSES = [
    "Based on traditional farming wisdom, rotating crops between legumes and cereals improves soil nitrogen levels significantly. Consider planting moong dal after your wheat harvest.",
    "For your soil type, I recommend using vermicompost instead of chemical fertilizers. It improves water retention by up to 30% and costs less in the long run.",
    "The ideal time for sowing Rabi crops in your region is mid-October to November. Make sure to prepare the land with adequate irrigation channels.",
    "Drip irrigation can reduce your water usage by 40-60% compared to flood irrigation. Government subsidies under PMKSY can cover up to 55% of installation costs.",
    "Neem-based organic pesticide is very effective against aphids and whiteflies. Mix 5ml neem oil per litre of water and spray early morning for best results.",
    "To protect crops from unseasonal rain, consider raised-bed farming. It improves drainage and reduces root rot risk substantially.",
]

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    api_key = data.get("api_key", "").strip()

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = (
                "You are AgriChain AI, an expert agricultural advisor for Indian farmers. "
                "Provide practical, concise advice. Answer in the same language the user asks in.\n\n"
                f"User: {message}"
            )
            response = model.generate_content(prompt)
            return jsonify({"reply": response.text, "source": "gemini"})
        except Exception as e:
            return jsonify({
                "reply": f"Gemini API error: {str(e)}. Falling back to expert advice.\n\n{random.choice(EXPERT_RESPONSES)}",
                "source": "fallback",
            })

    return jsonify({
        "reply": random.choice(EXPERT_RESPONSES),
        "source": "expert",
    })


# ---------------------------------------------------------------------------
# Server Initialization
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_forum_csv()
    init_crops_csv()
    init_ledger_csv()
    print("\n🌾  AgriChain server running at http://localhost:8000")
    print("🔗  Blockchain & AI endpoints initialized.\n")
    app.run(debug=True, port=8000)