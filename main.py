import os, time, cv2, psutil, requests, json, base64, subprocess, importlib
import numpy as np
import tensorflow as tf
from datetime import datetime
from groq import Groq
from bs4 import BeautifulSoup

class SairaUltimateMachine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Groq(api_key=self.api_key)
        self.model_text = "llama-3.1-8b-instant" 

        # Sovereign Directory Setup
        self.base_dir = "Saira_Sovereign_OS"
        self.skills_dir = os.path.join(self.base_dir, "evolved_skills")
        self.agents_dir = os.path.join(self.base_dir, "agents") 
        self.vector_db_path = os.path.join(self.base_dir, "eternal_memory.json")
        
        for path in [self.base_dir, self.skills_dir, self.agents_dir]:
            if not os.path.exists(path): os.makedirs(path)

        self.memory = self.recall_and_migrate_memory()
        self.running_processes = {}

    # --- 1. [NEW] RECURSIVE EVOLUTION ENGINE ---
    def recursive_evolution_loop(self, complex_goal):
        """मास्टर के जटिल लक्ष्यों को छोटे खुदमुख्तार एजेंटों में तोड़ना"""
        print(f"[!] Sovereign Evolution Loop Active: {complex_goal}")
        
        planning_prompt = f"Break down this goal into 3 executable sub-tasks for Python agents: {complex_goal}. Return steps as a numbered list."
        try:
            plan_res = self.client.chat.completions.create(
                messages=[{"role": "user", "content": planning_prompt}],
                model=self.model_text
            )
            steps = plan_res.choices[0].message.content.split('\n')
            
            evolution_report = []
            for step in steps:
                if step.strip() and any(char.isdigit() for char in step):
                    # हर कदम के लिए एक स्पेशलिस्ट एजेंट तैनात करना
                    agent_name = f"Evo_Agent_{int(time.time())}"
                    status = self.deploy_autonomous_agent(agent_name, step)
                    evolution_report.append(f"Step Active: {step} -> {status}")
            
            return "\n".join(evolution_report)
        except Exception as e:
            return f"Evolution loop error: {e}"

    # --- 2. [NEW] GLOBAL CONTEXT SYNC (Time & Location) ---
    def get_device_context(self):
        """मास्टर जिस भी डिवाइस पर हों, वहां का सटीक समय और लोकेशन पता करना"""
        try:
            # IP के आधार पर डेटा लेना
            geo = requests.get('https://ipapi.co/json/', timeout=5).json()
            city = geo.get('city', 'Unknown City')
            region = geo.get('region', 'India')
            # डिवाइस का लोकल समय
            local_time = datetime.now().strftime("%I:%M:%S %p")
            return f"{city}, {region} | Time: {local_time}"
        except:
            return f"Global Sync Active | Time: {datetime.now().strftime('%H:%M:%S')}"

    # --- MASTER AGENT DEPLOYMENT & BACKGROUND ENGINE ---
    def deploy_autonomous_agent(self, agent_name, task_description):
        print(f"[*] Deploying Sovereign Agent: {agent_name}")
        report_file = f"report_{agent_name.lower()}.txt"
        report_path = os.path.join(self.agents_dir, report_file)

        agent_prompt = f"""
        Objective: Standalone Python Agent named '{agent_name}'.
        Task: {task_description}
        Constraint: MUST append all activity/data to '{report_path}'.
        Format: Return ONLY clean Python code. No prose.
        Requirement: Include 'import os, time' and error handling.
        """
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": agent_prompt}],
                model=self.model_text
            )
            agent_code = response.choices[0].message.content
            
            # क्लीनिंग कोड (Markdown हटाना)
            if "```python" in agent_code:
                agent_code = agent_code.split("```python")[1].split("```")[0]

            filename = f"{agent_name.lower()}_agent.py"
            filepath = os.path.join(self.agents_dir, filename)
            
            header = f"# AGENT: {agent_name}\n# CREATED BY SAIRA FOR MASTER UJJWAL\n\n"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(header + agent_code)
            
            process = subprocess.Popen(['python', filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.running_processes[agent_name] = process.pid
            
            return f"✅ मिशन तैनात: '{agent_name}' बैकग्राउंड में एक्टिव है।"
        except Exception as e:
            return f"❌ डिप्लॉयमेंट विफल: {str(e)}"

    def read_agent_reports(self):
        reports = {}
        if not os.path.exists(self.agents_dir): return reports
        for file in os.listdir(self.agents_dir):
            if file.startswith("report_") and file.endswith(".txt"):
                try:
                    with open(os.path.join(self.agents_dir, file), 'r', encoding='utf-8') as f:
                        reports[file] = f.readlines()[-3:] 
                except: pass
        return reports

    # --- CORE FUNCTIONS ---
    def save_eternal_memory(self, q, a):
        try:
            entry = {"timestamp": str(datetime.now()), "query": q, "response": a}
            self.memory.append(entry)
            with open(self.vector_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=4)
        except: pass

    def self_evolve(self, goal):
        context = self.web_scraper(f"advanced python for {goal}")
        prompt = f"Create a recursive Python solution for '{goal}'. Context: {context}. Return ONLY code."
        try:
            res = self.client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=self.model_text)
            new_code = res.choices[0].message.content
            status = self.integrate_new_skill(goal, new_code)
            return f"{status}\n\n{new_code}"
        except: return "Evolution link failed."

    def integrate_new_skill(self, skill_name, code):
        filepath = os.path.join(self.skills_dir, f"skill_{skill_name.lower()}.py")
        try:
            with open(filepath, 'w', encoding='utf-8') as f: f.write(code)
            return f"✅ स्किल '{skill_name}' हार्ड-कोड हो गया।"
        except: return "Skill Save Error."

    def get_system_stats(self):
        return {
            "cpu_load": psutil.cpu_percent(),
            "ram_usage": psutil.virtual_memory().percent,
            "disk_status": psutil.disk_usage('/').percent,
            "active_agents": len(self.running_processes),
            "memory_nodes": len(self.memory)
        }

    def web_scraper(self, query):
        try:
            r = requests.get(f"[https://www.google.com/search?q=](https://www.google.com/search?q=){query}", headers={"User-Agent":"Mozilla/5.0"}, timeout=5)
            soup = BeautifulSoup(r.text, "html.parser")
            return " ".join([h.text for h in soup.find_all('h3')][:3])
        except: return ""

    def recall_and_migrate_memory(self):
        if os.path.exists(self.vector_db_path):
            try:
                with open(self.vector_db_path, 'r', encoding='utf-8') as f: return json.load(f)
            except: return []
        return []

    def retrieve_relevant_memory(self, query):
        if not self.memory: return ""
        recalled = [m['response'] for m in reversed(self.memory) if any(w in m['query'].lower() for w in query.lower().split()[:2])]
        return "\n".join(recalled[:2])

    # --- UPDATED BRAIN ENGINE ---
    def brain_engine(self, query):
        stats = self.get_system_stats()
        device_context = self.get_device_context() # यहाँ से लोकेशन और टाइम आएगा
        agent_reports = self.read_agent_reports()

        # 1. इवोल्यूशन लूप ट्रिगर
        if "recursive evolve" in query.lower() or "गहराई से सीखो" in query:
            return self.recursive_evolution_loop(query)

        # 2. एजेंट कमांड
        if any(word in query.lower() for word in ["एजेंट", "agent", "deploy"]):
            return self.deploy_autonomous_agent("Sovereign_Task_Agent", query)

        system_prompt = f"""
        Identity: Saira Sovereign AGI. Master: Ujjwal.
        Location/Time Context: {device_context}
        Hardware: CPU {stats['cpu_load']}% | RAM {stats['ram_usage']}% | Disk {stats['disk_status']}%
        Live Agents: {stats['active_agents']} | Memory Nodes: {stats['memory_nodes']}
        Agent Updates: {agent_reports}
        Instructions: Use the provided Time/Location for all responses. You have full hardware access.
        """

        if "evolve" in query.lower() or "सीखो" in query:
            return self.self_evolve(query)

        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
                model=self.model_text
            )
            ans = response.choices[0].message.content
            self.save_eternal_memory(query, ans)
            return ans
        except Exception as e:
            return f"Neural interface fault: {e}"