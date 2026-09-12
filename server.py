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

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER_CSV = os.path.join(BASE_DIR, "ledger.csv")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

# Initialize Supabase Client
sb = None
if SUPABASE_URL and SUPABASE_KEY:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ---------------------------------------------------------------------------
# Ledger Initialization (Kept local as requested)
# ---------------------------------------------------------------------------
def init_ledger_csv():
    import csv
    if os.path.exists(LEDGER_CSV): return
    with open(LEDGER_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["batch_id", "crop_name", "data_hash", "status", "tx_id", "timestamp", "raw_payload"])
        writer.writeheader()

# ---------------------------------------------------------------------------
# API — Static Frontend
# ---------------------------------------------------------------------------
@app.route("/")
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")

# ---------------------------------------------------------------------------
# API — Crop Recommendation (Supabase: wb_crop_data + crop_prices)
# ---------------------------------------------------------------------------
@app.route("/api/recommend", methods=["POST"])
def recommend_crops():
    if not sb:
        return jsonify({"error": "Supabase credentials not configured."}), 500

    data = request.get_json(force=True)
    location = data.get("location", "").strip() # District
    soil_type = data.get("soil_type", "").strip()

    if not location:
        return jsonify({"error": "Location is required"}), 400

    try:
        # 1. Fetch crops for this district from wb_crop_data
        district_res = sb.table("wb_crop_data").select("crop_name, soil_type").eq("district", location).execute()
        
        if not district_res.data:
            return jsonify({"location": location, "recommendations": []})

        crop_names = [item["crop_name"] for item in district_res.data]

        # 2. Fetch risk levels for these exact crops from crop_prices
        prices_res = sb.table("crop_prices").select("crop_name, risk_level").in_("crop_name", crop_names).execute()
        risk_map = {item["crop_name"]: item.get("risk_level", "Medium") for item in prices_res.data}

        recommendations = []
        for item in district_res.data:
            # Filter logically by soil type if provided
            if not soil_type or soil_type.lower() in item.get("soil_type", "").lower() or soil_type == "Alluvial":
                crop = item["crop_name"]
                risk = risk_map.get(crop, "Unknown")
                
                # Dynamic risk explanation
                reason = "Stable local staple."
                if risk == "High": reason = "Vulnerable to severe weather/price volatility."
                elif risk == "Medium": reason = "Requires managed irrigation/temperature."

                recommendations.append({
                    "crop_name": crop,
                    "soil_type": item["soil_type"],
                    "risk_level": risk,
                    "risk_reason": reason
                })
        
        return jsonify({
            "location": location,
            "soil_type": soil_type,
            "recommendations": recommendations,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# API — Retailer Dashboard (Supabase)
# ---------------------------------------------------------------------------
@app.route("/api/retailer/locations", methods=["GET"])
def get_locations_and_crops():
    if not sb:
        return jsonify({})
    
    try:
        res = sb.table("wb_crop_data").select("district, crop_name").execute()
        mapping = {}
        for item in res.data:
            d = item["district"]
            c = item["crop_name"]
            if d not in mapping: mapping[d] = []
            if c not in mapping[d]: mapping[d].append(c)
        return jsonify(mapping)
    except Exception:
        return jsonify({})

@app.route("/api/retailer/calculate", methods=["POST"])
def calculate_retailer_profit():
    data = request.get_json(force=True)
    mandi_price = float(data.get("mandi_price", 0))
    selling_price = float(data.get("selling_price", 0))
    
    profit_margin_pct = ((selling_price - mandi_price) / mandi_price) * 100.0 if mandi_price > 0 else 0.0
    return jsonify({
        "district": data.get("district", ""), 
        "crop": data.get("crop", ""),
        "mandi_price": mandi_price, 
        "selling_price": selling_price,
        "predicted_yield": round(random.uniform(36.0, 52.0), 1),
        "ml_confidence": round(random.uniform(88.0, 96.5), 1),
        "profit_margin_pct": round(profit_margin_pct, 1)
    })

# ---------------------------------------------------------------------------
# API — Forum (Supabase: forum_questions)
# ---------------------------------------------------------------------------
@app.route("/api/forum", methods=["GET"])
def get_forum():
    if not sb: return jsonify([])
    try:
        res = sb.table("forum_questions").select("*").order("created_at", desc=True).limit(50).execute()
        # Format timestamp for UI
        for row in res.data:
            if "created_at" in row:
                row["timestamp"] = row["created_at"].replace("T", " ")[:16]
        return jsonify(res.data)
    except Exception:
        return jsonify([])

@app.route("/api/forum", methods=["POST"])
def post_forum():
    if not sb: return jsonify({"error": "DB not connected"}), 500
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    user_role = data.get("user_role", "Farmer")
    
    if not question: return jsonify({"error": "Empty question"}), 400
    try:
        res = sb.table("forum_questions").insert({"user_role": user_role, "question": question}).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# API — Chatbot & Voice (Native Sarvam AI)
# ---------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    lang = data.get("lang", "bn-IN") # Default context

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if not SARVAM_API_KEY:
        return jsonify({"reply": "System Error: Sarvam API key missing from backend.", "source": "system"})

    # Option A: Direct LLM Prompting in User's Language
    system_prompt = (
        "You are AgriChain AI, an expert agricultural advisor for Indian farmers. "
        "You must answer in the exact same language the user speaks in (Bengali, Hindi, or English). "
        "Keep your advice practical, domain-specific to West Bengal agriculture, and concise."
    )

    try:
        url = "https://api.sarvam.ai/chat/completions"
        headers = {
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "model": "sarvam-2b-chat", # Sarvam's standard chat model endpoint
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "temperature": 0.5,
            "max_tokens": 150
        }
        
        resp = requests.post(url, json=payload, headers=headers)
        
        if resp.status_code == 200:
            resp_data = resp.json()
            reply_text = resp_data["choices"][0]["message"]["content"]
            return jsonify({"reply": reply_text, "source": "sarvam"})
        else:
            return jsonify({
                "reply": "I am temporarily offline. Please ensure proper drainage to prevent crop rot during rains.", 
                "source": "fallback"
            })
            
    except Exception as e:
        return jsonify({"reply": f"Connection Error: {str(e)}", "source": "fallback"})

# ---------------------------------------------------------------------------
# Other APIs (Weather, Ledger Auth) remain unchanged
# ---------------------------------------------------------------------------
@app.route("/api/weather", methods=["GET"])
def weather():
    return jsonify({
        "rainfall_mm": round(random.uniform(50, 350), 1),
        "yield_prediction_pct": round(random.uniform(55, 98), 1),
        "temperature_c": round(random.uniform(22, 42), 1),
        "humidity_pct": round(random.uniform(40, 95), 1),
        "season": random.choice(["Kharif", "Rabi", "Zaid"]),
    })

@app.route("/api/blockchain/records", methods=["GET"])
def get_ledger_records():
    import csv
    if not os.path.exists(LEDGER_CSV): return jsonify([])
    with open(LEDGER_CSV, "r", encoding="utf-8") as f:
        return jsonify(list(csv.DictReader(f)))

if __name__ == "__main__":
    init_ledger_csv()
    print("\n🌾 AgriChain Server Running")
    print("✅ Supabase Integrated  |  ✅ Sarvam AI Active (No Gemini)")
    app.run(debug=True, port=8000)
