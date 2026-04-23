import os
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- API KEY & BRIDGE SETUP ---
# रेंडर के Environment Variables से की उठाना सबसे सुरक्षित है
API_KEY = os.environ.get("GROQ_API_KEY", "gsk_your_default_here")

try:
    from main import SairaUltimateMachine
    # की (key) पास करना ज़रूरी है
    saira_core = SairaUltimateMachine(API_KEY)
    BRIDGE_ACTIVE = True
except Exception as e:
    BRIDGE_ACTIVE = False
    print(f"[!] Bridge Error: {e}")

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('login.html')

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
            # ध्यान दें: brain_engine को जवाब return करना चाहिए, सिर्फ बोलना नहीं
            response = saira_core.brain_engine(query)
            
            # अगर brain_engine कुछ return नहीं कर रहा, तो एक fallback मैसेज दें
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
    # रेंडर के लिए 0.0.0.0 और पोर्ट सेटिंग अनिवार्य है
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)