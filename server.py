import os
import random
import json
import hashlib
import urllib.request
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER_CSV = os.path.join(BASE_DIR, "ledger.csv")
FORUM_CSV = os.path.join(BASE_DIR, "forum.csv") # Local fallback

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

sb = None
if SUPABASE_URL and SUPABASE_KEY:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def init_ledger_csv():
    import csv
    if os.path.exists(LEDGER_CSV): return
    with open(LEDGER_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["batch_id", "crop_name", "data_hash", "status", "tx_id", "timestamp", "raw_payload"])
        writer.writeheader()

@app.route("/")
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")

# ---------------------------------------------------------------------------
# API — Retailer Dashboard (Supabase Auto-Pricing)
# ---------------------------------------------------------------------------
@app.route("/api/retailer/locations", methods=["GET"])
def get_locations_and_crops():
    """Fetches all WB districts and their specific crops from wb_crop_data."""
    if sb:
        try:
            res = sb.table("wb_crop_data").select("district, crop_name").execute()
            mapping = {}
            for item in res.data:
                d = item["district"]
                c = item["crop_name"]
                if d not in mapping: mapping[d] = []
                if c not in mapping[d]: mapping[d].append(c)
            return jsonify(mapping)
        except Exception as e:
            print("Supabase Error:", e)
            
    # Fallback if DB fails
    return jsonify({
        "Hooghly": ["Rice", "Wheat", "Potato", "Jute"],
        "Alipurduar": ["Rice", "Wheat", "Tea", "Jute"]
    })

@app.route("/api/retailer/crop_details", methods=["POST"])
def get_crop_details():
    """Auto-fetches prices from crop_prices table and simulates ML yield."""
    data = request.get_json(force=True)
    crop_name = data.get("crop", "")
    
    mandi_price = 0
    selling_price = 0
    margin = "0%"

    if sb and crop_name:
        try:
            res = sb.table("crop_prices").select("*").eq("crop_name", crop_name).execute()
            if res.data:
                mandi_price = res.data[0].get("mandi_price_qtl", 0)
                selling_price = res.data[0].get("selling_price_qtl", 0)
                margin = res.data[0].get("retailer_margin", "0%")
        except Exception as e:
            print("Supabase Error:", e)

    # If DB fails or crop not found, provide mock data so UI doesn't crash
    if mandi_price == 0:
        mandi_price = 2200
        selling_price = 3100
        margin = "40.9%"

    predicted_yield = round(random.uniform(36.0, 52.0), 1)
    ml_confidence = round(random.uniform(88.0, 96.5), 1)

    return jsonify({
        "mandi_price": mandi_price,
        "selling_price": selling_price,
        "margin": margin,
        "predicted_yield": predicted_yield,
        "ml_confidence": ml_confidence
    })

# ---------------------------------------------------------------------------
# API — Crop Recommendation (Supabase)
# ---------------------------------------------------------------------------
@app.route("/api/recommend", methods=["POST"])
def recommend_crops():
    data = request.get_json(force=True)
    location = data.get("location", "").strip()
    soil_type = data.get("soil_type", "").strip()

    if not location:
        return jsonify({"error": "Location required"}), 400

    if sb:
        try:
            district_res = sb.table("wb_crop_data").select("crop_name, soil_type").eq("district", location).execute()
            if not district_res.data:
                return jsonify({"location": location, "recommendations": []})

            crop_names = [item["crop_name"] for item in district_res.data]
            prices_res = sb.table("crop_prices").select("crop_name, risk_level").in_("crop_name", crop_names).execute()
            risk_map = {item["crop_name"]: item.get("risk_level", "Medium") for item in prices_res.data}

            recs = []
            for item in district_res.data:
                if not soil_type or soil_type.lower() in item.get("soil_type", "").lower() or soil_type == "Alluvial":
                    crop = item["crop_name"]
                    risk = risk_map.get(crop, "Medium")
                    reason = "Vulnerable to severe weather/price volatility." if risk == "High" else "Requires managed irrigation/temperature." if risk == "Medium" else "Stable local staple."
                    recs.append({"crop_name": crop, "soil_type": item["soil_type"], "risk_level": risk, "risk_reason": reason})
            
            return jsonify({"location": location, "soil_type": soil_type, "recommendations": recs})
        except Exception as e:
            print("Supabase Error:", e)

    return jsonify({"location": location, "recommendations": []})

# ---------------------------------------------------------------------------
# API — Forum (Supabase: forum_questions)
# ---------------------------------------------------------------------------
@app.route("/api/forum", methods=["GET"])
def get_forum():
    if sb:
        try:
            res = sb.table("forum_questions").select("*").order("created_at", desc=True).limit(50).execute()
            for row in res.data:
                if "created_at" in row: row["timestamp"] = row["created_at"].replace("T", " ")[:16]
            return jsonify(res.data)
        except Exception as e:
            print("Supabase Error:", e)
    return jsonify([])

@app.route("/api/forum", methods=["POST"])
def post_forum():
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    user_role = data.get("user_role", "Farmer")
    
    if not question: return jsonify({"error": "Empty question"}), 400
    
    if sb:
        try:
            res = sb.table("forum_questions").insert({"user_role": user_role, "question": question}).execute()
            if res.data:
                row = res.data[0]
                if "created_at" in row: row["timestamp"] = row["created_at"].replace("T", " ")[:16]
                return jsonify(row), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"error": "DB not connected"}), 500

# ---------------------------------------------------------------------------
# API — Chatbot & Voice (Native Sarvam AI)
# ---------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "").strip()

    if not SARVAM_API_KEY:
        return jsonify({"reply": "System Error: Sarvam API key missing from backend.", "source": "system"})

    system_prompt = "You are AgriChain AI, an expert agricultural advisor for Indian farmers. Answer in the same language the user speaks in (Bengali, Hindi, or English). Be concise."

    try:
        url = "https://api.sarvam.ai/chat/completions"
        headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
        payload = {
            "model": "sarvam-2b-chat",
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
            "temperature": 0.5, "max_tokens": 150
        }
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            return jsonify({"reply": resp.json()["choices"][0]["message"]["content"], "source": "sarvam"})
        else:
            return jsonify({"reply": "I am temporarily offline. Please ensure proper drainage during rains.", "source": "fallback"})
    except Exception as e:
        return jsonify({"reply": f"Connection Error: {str(e)}", "source": "fallback"})

# ---------------------------------------------------------------------------
# API — Blockchain & Predictor (Original Logic Restored)
# ---------------------------------------------------------------------------
@app.route("/api/blockchain/records", methods=["GET"])
def get_ledger_records():
    import csv
    if not os.path.exists(LEDGER_CSV): return jsonify([])
    with open(LEDGER_CSV, "r", encoding="utf-8") as f:
        return jsonify(list(csv.DictReader(f)))

@app.route("/api/blockchain/anchor", methods=["POST"])
def anchor_record():
    import csv
    data = request.get_json(force=True)
    batch_id = data.get("batch_id", f"BATCH-{int(datetime.now().timestamp())}")
    data_hash = "0x" + hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_record = {"batch_id": batch_id, "crop_name": data.get("crop_name", "Crop"), "data_hash": data_hash, "status": "Local Ledger", "tx_id": f"LOCAL-{data_hash[:8]}", "timestamp": timestamp, "raw_payload": json.dumps(data)}
    with open(LEDGER_CSV, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=["batch_id", "crop_name", "data_hash", "status", "tx_id", "timestamp", "raw_payload"]).writerow(new_record)
    return jsonify({"status": "success", "batch_id": batch_id, "data_hash": data_hash, "tx_id": new_record["tx_id"], "network": new_record["status"]})

@app.route("/api/weather", methods=["GET"])
def weather():
    return jsonify({
        "rainfall_mm": round(random.uniform(50, 350), 1),
        "yield_prediction_pct": round(random.uniform(55, 98), 1),
        "temperature_c": round(random.uniform(22, 42), 1),
        "humidity_pct": round(random.uniform(40, 95), 1),
        "season": random.choice(["Kharif", "Rabi", "Zaid"]),
    })

if __name__ == "__main__":
    init_ledger_csv()
    print("🌾 AgriChain Server Running")
    app.run(debug=True, port=8000)
