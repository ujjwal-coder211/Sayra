import os
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- API KEY & BRIDGE SETUP ---
API_KEY = os.environ.get("GROQ_API_KEY", "gsk_your_default_here")

try:
    from main import SairaUltimateMachine
    saira_core = SairaUltimateMachine(API_KEY)
    BRIDGE_ACTIVE = True
except Exception as e:
    BRIDGE_ACTIVE = False
    print(f"[!] Bridge Error: {e}")

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('login.html')

# --- ये रहा तुम्हारा नया लॉगिन लॉजिक ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
    
    # यहाँ तुम अपनी पसंद का पासवर्ड बदल सकते हो
    if password == "UJJWAL_SAIRA": 
        return jsonify({"success": True})
    else:
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

    if BRIDGE_ACTIVE:
        try:
            response = saira_core.brain_engine(query)
            if not response:
                response = "निर्देश प्रोसेस कर लिया गया है, मास्टर उज्ज्वल।"
            return jsonify({"reply": response})
        except Exception as e:
            return jsonify({"reply": f"Neural Bridge Error: {str(e)}"})
            
    return jsonify({"reply": "सायरा का कोर इंजन अभी ऑफलाइन है।"})

@app.route('/status')
def status():
    return jsonify({
        "system": "Saira V17.5 Sovereign",
        "bridge": "Active" if BRIDGE_ACTIVE else "Offline",
        "server_time": str(datetime.now())
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)