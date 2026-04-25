import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- API KEY & BRIDGE SETUP ---
# अपनी असली API Key यहाँ डालें या Environment Variable का उपयोग करें
API_KEY = os.environ.get("GROQ_API_KEY", "gsk_your_default_here")

# ग्लोबल वेरिएबल्स
BRIDGE_ACTIVE = False
saira_core = None
error_msg = "None"

def initialize_saira():
    global saira_core, BRIDGE_ACTIVE, error_msg
    try:
        from main import SairaUltimateMachine
        # सयारा कोर को इनिशियलाइज़ करना
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
            # सायरा के ब्रेन इंजन से जवाब लें
            response = saira_core.brain_engine(query)
            # साथ ही सिस्टम स्टैट्स भी भेजें ताकि डैशबोर्ड अपडेट हो सके
            stats = saira_core.get_system_stats()
            
            return jsonify({
                "reply": response or "निर्देश प्रोसेस कर लिया गया है।",
                "stats": stats # यह HTML में प्रोग्रेस बार अपडेट करेगा
            })
        except Exception as e:
            return jsonify({"reply": f"Neural Bridge Error: {str(e)}"})

    return jsonify({"reply": f"सायरा ऑफलाइन है। एरर: {error_msg}"})

@app.route('/status')
def status():
    # डैशबोर्ड के लिए असली सिस्टम हेल्थ डेटा
    current_stats = {}
    if saira_core:
        current_stats = saira_core.get_system_stats()

    return jsonify({
        "system": "Saira V17.5 Sovereign",
        "bridge": "Active" if BRIDGE_ACTIVE else "Offline",
        "error_details": error_msg,
        "server_time": str(datetime.now()),
        "live_stats": current_stats # CPU, RAM, Temp का असली डेटा
    })

if __name__ == "__main__":
    # पोर्ट मैनेजमेंट (Render या स्थानीय सर्वर के लिए)
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port, debug=False)