import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- API KEY & BRIDGE SETUP ---
API_KEY = os.environ.get("GROQ_API_KEY", "gsk_your_default_here")

# ग्लोबल वेरिएबल ताकि स्टेटस चेक हो सके
BRIDGE_ACTIVE = False
saira_core = None
error_msg = "None"

try:
    from main import SairaUltimateMachine
    # यहाँ मॉडल लोड करने की कोशिश
    saira_core = SairaUltimateMachine(API_KEY)
    BRIDGE_ACTIVE = True
    print("✅ Saira Neural Bridge: ACTIVE")
except Exception as e:
    BRIDGE_ACTIVE = False
    error_msg = str(e)
    print(f"[!] Bridge Error: {e}")

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
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
            response = saira_core.brain_engine(query)
            return jsonify({"reply": response or "निर्देश प्रोसेस कर लिया गया है।"})
        except Exception as e:
            return jsonify({"reply": f"Neural Bridge Error: {str(e)}"})
            
    return jsonify({"reply": f"सायरा ऑफलाइन है। एरर: {error_msg}"})

@app.route('/status')
def status():
    return jsonify({
        "system": "Saira V17.5 Sovereign",
        "bridge": "Active" if BRIDGE_ACTIVE else "Offline",
        "error_details": error_msg, # ये हमें बताएगा कि क्यों ऑफलाइन है
        "server_time": str(datetime.now())
    })

if __name__ == "__main__":
    # Render के लिए पोर्ट 10000 या एनवायरमेंट पोर्ट सबसे बेस्ट है
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)