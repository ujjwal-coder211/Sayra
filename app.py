import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import requests # लोकेशन डेटा फेच करने के लिए

app = Flask(__name__)

# --- API KEY & BRIDGE SETUP ---
API_KEY = os.environ.get("GROQ_API_KEY", "gsk_your_default_here")

# ग्लोबल वेरिएबल्स
BRIDGE_ACTIVE = False
saira_core = None
error_msg = "None"

def initialize_saira():
    global saira_core, BRIDGE_ACTIVE, error_msg
    try:
        from main import SairaUltimateMachine
        # सायरा कोर को इनिशियलाइज़ करना
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
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
    # मास्टर पासवर्ड चेक
    if password == "UJJWAL_SAIRA": 
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "एक्सेस डिनाइड: मास्टर की गलत है!"})

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

    return jsonify({"reply": f"सायरा ऑफलाइन है। एरर: {error_msg}"})

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
        "master_location": location_info, # मास्टर अभी कहाँ हैं
        "live_stats": current_stats 
    })

if __name__ == "__main__":
    # पोर्ट मैनेजमेंट (Render या स्थानीय सर्वर के लिए)
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port, debug=False)