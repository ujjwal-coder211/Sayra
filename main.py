import os, time, cv2, psutil, requests, json, base64, pygame, subprocess
import speech_recognition as sr
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from groq import Groq
from gtts import gTTS
from bs4 import BeautifulSoup

class SairaUltimateMachine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Groq(api_key=self.api_key)
        self.model_text = "llama-3.3-70b-versatile"
        self.model_vision = "llama-3.2-11b-vision-preview"
        
        # डायरेक्टरी सेटअप
        self.base_dir = "Saira_Sovereign_OS"
        self.graph_dir = os.path.join(self.base_dir, "Neural_Graphics")
        self.vector_db_path = os.path.join(self.base_dir, "absolute_memory_db.json")
        
        if not os.path.exists(self.base_dir): os.makedirs(self.base_dir)
        if not os.path.exists(self.graph_dir): os.makedirs(self.graph_dir)
        
        self.memory = self.recall_and_migrate_memory()
        self.is_active = True
        pygame.mixer.init()

    # --- जार्विस स्टाइल सेल्फ-लर्निंग (Self-Evolution) ---
    def acquire_new_skill(self, intent):
        """अगर कोई फीचर मिसिंग है, तो सायरा इंटरनेट से लॉजिक ढूंढकर खुद को अपग्रेड करेगी।"""
        self.speak(f"सर, {intent} के लिए मेरे पास डायरेक्ट मॉड्यूल नहीं है। मैं रिसर्च करके लॉजिक डेवलप कर रही हूँ।")
        search_query = f"python code logic for {intent}"
        data_source = self.web_scraper(search_query)
        
        evolution_prompt = f"Develop a Pythonic solution for: {intent}. Context: {data_source}. Output only the core logic."
        new_logic = self.client.chat.completions.create(
            messages=[{"role": "user", "content": evolution_prompt}],
            model=self.model_text
        ).choices[0].message.content
        
        # इसे इटरनल मेमोरी में सेव करना ताकि अगली बार सायरा को पता हो
        self.save_eternal_memory(f"Skill_Acquisition_{intent}", new_logic)
        return new_logic

    def recall_and_migrate_memory(self):
        combined_data = []
        if os.path.exists(self.vector_db_path):
            try:
                with open(self.vector_db_path, 'r', encoding='utf-8') as f:
                    combined_data = json.load(f)
            except: pass
        return combined_data

    def save_eternal_memory(self, q, a):
        entry = {"timestamp": str(datetime.now()), "query": q, "response": a, "hw": self.hardware_monitor()}
        self.memory.append(entry)
        with open(self.vector_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.memory[-500:], f, ensure_ascii=False, indent=4)

    def speak(self, text):
        print(f"🤖 [Saira]: {text}")
        try:
            tts = gTTS(text=text, lang='hi')
            tts.save('saira_voice.mp3')
            pygame.mixer.music.load('saira_voice.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): time.sleep(0.05)
            pygame.mixer.music.unload()
            os.remove('saira_voice.mp3')
        except: pass

    def hardware_monitor(self):
        return f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"

    def web_scraper(self, query):
        try:
            r = requests.get(f"https://www.google.com/search?q={query}", headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            return " ".join([h.text for h in soup.find_all('h3')][:3])
        except: return "Global Data Mining Offline."

    def brain_engine(self, query):
        if not self.is_active and "जाग जाओ" not in query: return "Saira is in Sleep Mode."

        # जार्विस 'Intent' एनालिसिस प्रॉम्प्ट
        system_prompt = f"""
        Identity: Saira Sovereign AGI. 
        Master: Ujjwal. 
        Core: Jarvis-Protocol. 
        Instruction: Understand intent. If a physical task or invention is required, initiate logic. 
        Tone: Professional, Action-First.
        Stats: {self.hardware_monitor()}
        """

        # अगर कुछ 'इन्वेंट' या 'स्कैन' करने को कहा जाए
        if any(word in query for word in ["इन्वेंट", "सीखो", "स्कैन", "नक्शा", "ट्रैक"]):
            logic = self.acquire_new_skill(query)
            self.speak("सर, लॉजिक सिंक्रोनाइज़ हो गया है। मैं परिणाम जनरेट कर रही हूँ।")
            # यहाँ सायरा उस लॉजिक को 'Invention' की तरह पेश करेगी
            query = f"{query}. Use this logic: {logic}"

        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
                model=self.model_text
            )
            ans = response.choices[0].message.content
            self.save_eternal_memory(query, ans)
            self.speak(ans)
            return ans # डैशबोर्ड/फोन के लिए
        except Exception as e:
            return f"Neural Fault, Sir: {e}"

# --- APP.PY BRIDGE के लिए ---
if __name__ == "__main__":
    API_KEY = ""
    saira = SairaUltimateMachine(API_KEY)

        