import os
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import io
import requests

import speech_service
import groq_config
import enterprise

app = Flask(__name__)

# Groq key — sirf env se; placeholder se connect mat karo
API_KEY = groq_config.get_groq_api_key()

# ग्लोबल वेरिएबल्स
BRIDGE_ACTIVE = False
saira_core = None
error_msg = "None"

def initialize_saira():
    global saira_core, BRIDGE_ACTIVE, error_msg
    if not API_KEY:
        BRIDGE_ACTIVE = False
        error_msg = (
            "GROQ_API_KEY set nahi hai. Railway → Sayra service → Variables → "
            "GROQ_API_KEY=gsk_... daalo, phir Redeploy."
        )
        print(f"[!] {error_msg}")
        return
    try:
        from main import SairaUltimateMachine
        saira_core = SairaUltimateMachine(API_KEY)
        BRIDGE_ACTIVE = True
        print("✅ Saira Neural Bridge: ACTIVE")
    except Exception as e:
        BRIDGE_ACTIVE = False
        error_msg = str(e)
        print(f"[!] Bridge Error: {e}")

# सर्वर शुरू होते ही सायरा को जगाओ
initialize_saira()

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({"reply": "मास्टर, कृपया कुछ निर्देश दें।"})

    if BRIDGE_ACTIVE and saira_core:
        try:
            # --- [NEW] DEVICE CONTEXT LOGIC ---
            # यूजर की आईपी एड्रेस पकड़ना (फोन या लैपटॉप)
            user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            
            # सायरा के ब्रेन इंजन से जवाब लें
            # नोट: main.py का brain_engine अब डिवाइस की लोकेशन खुद मैनेज करेगा
            response = saira_core.brain_engine(query)
            
            # सिस्टम स्टैट्स भी भेजें ताकि डैशबोर्ड अपडेट हो सके
            stats = saira_core.get_system_stats()
            
            return jsonify({
                "reply": response or "निर्देश प्रोसेस कर लिया गया है।",
                "stats": stats,
                "master_ip": user_ip # ट्रैकिंग के लिए
            })
        except Exception as e:
            return jsonify({"reply": f"Neural Bridge Error: {str(e)}"})

    return jsonify({"reply": f"⚠️ {error_msg}"})

@app.route('/status')
def status():
    # डैशबोर्ड के लिए असली सिस्टम हेल्थ डेटा
    current_stats = {}
    location_info = "Syncing..."
    
    if saira_core:
        current_stats = saira_core.get_system_stats()
        # [NEW] लाइव लोकेशन को स्टेटस में भी दिखाना
        location_info = saira_core.get_device_context()

    return jsonify({
        "system": "Saira V17.5 Sovereign",
        "bridge": "Active" if BRIDGE_ACTIVE else "Offline",
        "error_details": error_msg,
        "server_time": str(datetime.now()),
        "master_location": location_info,
        "live_stats": current_stats,
        "brain": saira_core.get_brain_status() if saira_core else {},
        "speech": speech_service.speech_capabilities(),
        "groq": groq_config.test_groq_connection(),
    })


@app.route("/health/groq")
def health_groq():
    return jsonify(groq_config.test_groq_connection())


# --- Command Center (Aitotech company) — dashboard COMPANY tab ke liye ---
@app.route("/enterprise/overview")
def enterprise_overview():
    """Workflow + profit + advice + opportunities — sab ek call me."""
    return jsonify(enterprise.get_overview())


@app.route("/enterprise/advice/<advice_id>/answer", methods=["POST"])
def enterprise_answer_advice(advice_id):
    """Master ki advice agents tak (human -> agents)."""
    data = request.get_json(silent=True) or {}
    decision = (data.get("decision") or "").strip()
    response = (data.get("response") or "").strip()
    if not decision:
        return jsonify({"ok": False, "message": "Decision chahiye."}), 400
    return jsonify(enterprise.answer_advice(advice_id, decision, response))


@app.route("/enterprise/pipeline", methods=["POST"])
def enterprise_start_pipeline():
    """Naya autonomous pipeline shuru karo."""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "message": "Idea/title chahiye."}), 400
    return jsonify(
        enterprise.start_pipeline(
            title,
            market=data.get("market") or None,
            region=data.get("region") or None,
            notes=data.get("notes") or None,
        )
    )


@app.route("/enterprise/tick", methods=["POST"])
def enterprise_tick():
    """Orchestrator ko ek batch chalao (agents aage badhein)।"""
    return jsonify(enterprise.run_tick())


@app.route("/enterprise/growth", methods=["POST"])
def enterprise_growth():
    """Autonomous prospecting cycle shuru karo (company khud client dhoondhe)।"""
    data = request.get_json(silent=True) or {}
    return jsonify(enterprise.start_growth(market=data.get("market") or None))


@app.route("/enterprise/fulfillment", methods=["POST"])
def enterprise_fulfillment():
    """Client agree — fulfillment pipeline (requirements → ... → delivery) shuru।"""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "message": "Client/deal title chahiye."}), 400
    try:
        amount = float(data.get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0
    return jsonify(
        enterprise.start_fulfillment(
            title,
            client_name=data.get("client_name") or None,
            client_email=data.get("client_email") or None,
            amount=amount,
            notes=data.get("notes") or None,
        )
    )


@app.route("/speech/status")
def speech_status():
    return jsonify(speech_service.speech_capabilities())


@app.route("/speech/transcribe", methods=["POST"])
def speech_transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400
    lang = request.form.get("language") or "hi"
    text, err = speech_service.transcribe_file(request.files["audio"], language=lang)
    if err:
        return jsonify({"error": err}), 502
    if not text:
        return jsonify({"error": "Kuch sunai nahi diya"}), 422
    return jsonify({"text": text})


@app.route("/speech/speak", methods=["POST"])
def speech_speak():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    lang = data.get("lang") or "hi"
    if not text:
        return jsonify({"error": "Empty text"}), 400
    mp3, err = speech_service.synthesize_mp3(text, lang=lang)
    if err or not mp3:
        return jsonify({"error": err or "TTS failed"}), 502
    return send_file(io.BytesIO(mp3), mimetype="audio/mpeg", download_name="saira.mp3")

if __name__ == "__main__":
    # पोर्ट मैनेजमेंट (Render या स्थानीय सर्वर के लिए)
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port, debug=False)