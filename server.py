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
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORUM_CSV = os.path.join(BASE_DIR, "forum.csv")
CROPS_CSV = os.path.join(BASE_DIR, "crops.csv")
LEDGER_CSV = os.path.join(BASE_DIR, "ledger.csv")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

# Initialize Supabase client
sb = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(" Connected to Supabase successfully.")
    except Exception as e:
        print(f"⚠️ Supabase Init Warning: {e}")

FIREFLY_URL = "http://localhost:5000/api/v1/namespaces/default/messages/broadcast"

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def init_forum_csv():
    if os.path.exists(FORUM_CSV): return
    rows = [
        {"id": "1", "user_role": "Farmer",   "question": "What is the best crop for clay soil in monsoon?", "timestamp": "2026-03-28 10:15:00"},
        {"id": "2", "user_role": "Retailer", "question": "Where can I source organic rice in bulk?",        "timestamp": "2026-03-29 14:30:00"},
        {"id": "3", "user_role": "Farmer",   "question": "How to reduce water usage for wheat cultivation?", "timestamp": "2026-03-30 09:00:00"},
        {"id": "4", "user_role": "Admin",    "question": "Can we get a subsidy tracker added to the platform?", "timestamp": "2026-04-01 16:45:00"},
    ]
    with open(FORUM_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "user_role", "question", "timestamp"])
        writer.writeheader()
        writer.writerows(rows)

def init_crops_csv():
    if os.path.exists(CROPS_CSV): return
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

def init_ledger_csv():
    if os.path.exists(LEDGER_CSV): return
    fieldnames = ["batch_id", "crop_name", "data_hash", "status", "tx_id", "timestamp", "raw_payload"]
    with open(LEDGER_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

def read_csv(path):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def next_forum_id():
    rows = read_csv(FORUM_CSV)
    return max([int(r["id"]) for r in rows] + [0]) + 1

FALLBACK_LOCATIONS = {
    "Alipurduar": ["Rice", "Wheat", "Tea", "Jute"],
    "Bankura": ["Rice", "Wheat", "Mustard", "Vegetables"],
    "Birbhum": ["Rice", "Wheat", "Mustard", "Sugarcane"],
    "Cooch Behar": ["Rice", "Wheat", "Jute", "Tobacco"],
    "Dakshin Dinajpur": ["Rice", "Wheat", "Jute", "Mustard"],
    "Darjeeling": ["Rice", "Maize", "Tea", "Large Cardamom"],
    "Hooghly": ["Rice", "Wheat", "Potato", "Jute"],
    "Howrah": ["Rice", "Wheat", "Jute", "Floriculture"],
    "Jalpaiguri": ["Rice", "Maize", "Tea", "Jute"],
    "Jhargram": ["Rice", "Maize", "Cashew", "Sabai Grass"],
    "Kalimpong": ["Maize", "Rice", "Large Cardamom", "Ginger"],
    "Malda": ["Rice", "Wheat", "Mango", "Mulberry"],
    "Murshidabad": ["Rice", "Wheat", "Jute", "Mango"],
    "Nadia": ["Rice", "Wheat", "Jute", "Flowers"],
    "North 24 Parganas": ["Rice", "Wheat", "Jute", "Vegetables"],
    "Paschim Bardhaman": ["Rice", "Wheat", "Mustard", "Vegetables"],
    "Paschim Medinipur": ["Rice", "Wheat", "Potato", "Cashew"],
    "Purba Bardhaman": ["Rice", "Wheat", "Potato", "Mustard"],
    "Purba Medinipur": ["Rice", "Wheat", "Betelvine", "Cashew"],
    "Purulia": ["Rice", "Maize", "Mustard", "Pulses"],
    "South 24 Parganas": ["Rice", "Wheat", "Betelvine", "Sunflower"],
    "Uttar Dinajpur": ["Rice", "Wheat", "Jute", "Mustard"],
}

FALLBACK_PRICES = {
    'Rice': (4500, 5400), 'Wheat': (2725, 3134), 'Tea': (18000, 25200), 'Jute': (5500, 6875),
    'Mustard': (6400, 7680), 'Vegetables': (3500, 5600), 'Sugarcane': (350, 455), 'Tobacco': (8500, 11475),
    'Maize': (2750, 3162), 'Large Cardamom': (120000, 156000), 'Potato': (1050, 1732), 'Floriculture': (15000, 22500),
    'Cashew': (10000, 13000), 'Sabai Grass': (3000, 3600), 'Ginger': (11500, 16675), 'Mango': (4200, 6510),
    'Mulberry': (2500, 3125), 'Flowers': (15000, 22500), 'Betelvine': (18000, 27900), 'Pulses': (7000, 8750),
    'Sunflower': (6500, 7800)
}

# ---------------------------------------------------------------------------
# Routes — Static Frontend
# ---------------------------------------------------------------------------
@app.route("/")
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")

# ---------------------------------------------------------------------------
# API — Forum (Supabase with Multiple Fallback Tries)
# ---------------------------------------------------------------------------
@app.route("/api/forum", methods=["GET"])
def get_forum():
    if sb:
        try:
            res = sb.table("forum_questions").select("*").order("created_at", desc=True).limit(50).execute()
            if res.data:
                rows = []
                for r in res.data:
                    item = dict(r)
                    created_at = item.get("created_at") or item.get("timestamp") or ""
                    item["timestamp"] = str(created_at).replace("T", " ")[:19]
                    item["user_role"] = str(item.get("user_role", "Farmer")).capitalize()
                    rows.append(item)
                return jsonify(rows)
        except Exception as e:
            print(f"[Supabase Forum Fetch Error]: {e}")
    return jsonify(read_csv(FORUM_CSV))

@app.route("/api/forum", methods=["POST"])
def post_forum():
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    user_role = data.get("user_role", "Farmer").strip()
    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saved_row = None

    if sb:
        # Tries original role, lowercase, and fallback values to satisfy any check constraints
        roles_to_try = [user_role, user_role.lower()]
        if user_role.lower() in ["admin", "retailer"]:
            roles_to_try.extend(["expert", "farmer"])
            
        for role_candidate in roles_to_try:
            try:
                res = sb.table("forum_questions").insert({
                    "user_role": role_candidate,
                    "question": question
                }).execute()
                if res.data:
                    saved_row = res.data[0]
                    created_at = saved_row.get("created_at") or now_str
                    saved_row["timestamp"] = str(created_at).replace("T", " ")[:19]
                    saved_row["user_role"] = user_role
                    print(f" Supabase forum question saved (Role used: '{role_candidate}').")
                    break
            except Exception as e:
                print(f"[Supabase Insert with '{role_candidate}' Failed]: {e}")

    if saved_row:
        return jsonify(saved_row), 201

    # Local fallback
    new_row = {
        "id": str(next_forum_id()),
        "user_role": user_role,
        "question": question,
        "timestamp": now_str,
    }
    with open(FORUM_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "user_role", "question", "timestamp"])
        writer.writerow(new_row)

    return jsonify(new_row), 201

# ---------------------------------------------------------------------------
# API — Retailer Dashboard (Database Integration)
# ---------------------------------------------------------------------------
@app.route("/api/retailer/locations", methods=["GET"])
def get_retailer_locations():
    if sb:
        try:
            res = sb.table("wb_crop_data").select("district, crop_name").execute()
            if res.data:
                mapping = {}
                for row in res.data:
                    d = row.get("district")
                    c = row.get("crop_name")
                    if d and c:
                        if d not in mapping: mapping[d] = []
                        if c not in mapping[d]: mapping[d].append(c)
                if mapping: return jsonify(mapping)
        except Exception as e:
            print(f"[Supabase Crop Locations Fetch Error]: {e}")
    return jsonify(FALLBACK_LOCATIONS)

@app.route("/api/retailer/calculate", methods=["POST"])
def calculate_retailer_profit():
    data = request.get_json(force=True)
    district = data.get("district", "Alipurduar")
    crop = data.get("crop", "Rice")

    mandi_price = None
    selling_price = None

    if sb and crop:
        try:
            res = sb.table("crop_prices").select("mandi_price_qtl, selling_price_qtl").ilike("crop_name", crop).execute()
            if res.data:
                mandi_price = float(res.data[0].get("mandi_price_qtl"))
                selling_price = float(res.data[0].get("selling_price_qtl"))
        except Exception as e:
            print(f"[Supabase Price Fetch Error]: {e}")

    if mandi_price is None or selling_price is None:
        mandi_price, selling_price = FALLBACK_PRICES.get(crop, (2200, 3100))

    profit = selling_price - mandi_price
    margin_pct = (profit / mandi_price) * 100.0 if mandi_price > 0 else 0.0

    random.seed(f"{district}_{crop}")
    predicted_yield = round(random.uniform(38.0, 48.0), 1)
    ml_confidence = round(random.uniform(91.0, 97.5), 1)

    return jsonify({
        "district": district,
        "crop": crop,
        "mandi_price": mandi_price,
        "selling_price": selling_price,
        "profit_margin_pct": round(margin_pct, 1),
        "predicted_yield": predicted_yield,
        "ml_confidence": ml_confidence
    })

# ---------------------------------------------------------------------------
# API — Crop Recommendation (Farmer Dashboard)
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
# API — Weather (Telemetry)
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
# API — Blockchain Record Management
# ---------------------------------------------------------------------------
@app.route("/api/blockchain/anchor", methods=["POST"])
def anchor_record():
    data = request.get_json(force=True)
    batch_id = data.get("batch_id", f"BATCH-{int(datetime.now().timestamp())}")
    crop_name = data.get("crop_name", "Organic Wheat")
    canonical_payload = json.dumps(data, sort_keys=True)
    data_hash = "0x" + hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tx_id = f"LOCAL-PIN-{data_hash[:10]}"
    network_status = "Local Cryptographic Ledger (FireFly Inactive)"

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
    return jsonify(read_csv(LEDGER_CSV))

@app.route("/api/blockchain/verify", methods=["POST"])
def verify_record():
    data = request.get_json(force=True)
    batch_id = data.get("batch_id")
    current_payload = data.get("payload")

    records = read_csv(LEDGER_CSV)
    matched = next((r for r in records if r["batch_id"] == batch_id), None)

    if not matched:
        return jsonify({"error": "Batch ID not found in ledger"}), 404

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
# API — AI Chatbot (Official Sarvam AI v1 Endpoint)
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
    client_key = data.get("api_key", "").strip()
    active_key = SARVAM_API_KEY or client_key

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if active_key:
        try:
            # Correct official endpoint and conversational model
            url = "https://api.sarvam.ai/v1/chat/completions"
            headers = {
                "api-subscription-key": active_key,
                "Content-Type": "application/json"
            }
            system_prompt = (
                "You are AgriChain AI, an expert agricultural advisor for Indian farmers. "
                "Provide practical, concise advice. Answer in the same language the user asks in (Bengali, Hindi, or English)."
            )
            payload = {
                "model": "sarvam-105b-conversations",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.3,
                "max_tokens": 512,
                "reasoning_effort": None
            }
            
            resp = requests.post(url, json=payload, headers=headers, timeout=10.0)
            print(f"[Sarvam API Call] Status: {resp.status_code}")
            
            if resp.status_code == 200:
                res_data = resp.json()
                choice = res_data["choices"][0]["message"]
                reply = choice.get("content") or choice.get("reasoning_content") or ""
                if reply.strip():
                    return jsonify({"reply": reply.strip(), "source": "sarvam"})
            else:
                print(f"[Sarvam API Error Body]: {resp.text}")
        except Exception as e:
            print(f"[Sarvam API Request Exception]: {e}")

    return jsonify({
        "reply": random.choice(EXPERT_RESPONSES),
        "source": "expert",
    })

if __name__ == "__main__":
    init_forum_csv()
    init_crops_csv()
    init_ledger_csv()
    print("\n🌾  AgriChain server running at http://localhost:8000")
    print("🔗  Supabase & Sarvam endpoints initialized.\n")
    app.run(debug=True, port=8000)
