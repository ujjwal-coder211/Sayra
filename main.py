import os, time, psutil, requests, json, subprocess
from datetime import datetime
from bs4 import BeautifulSoup

import enterprise
from sovereign_brain import SovereignBrain


class SairaUltimateMachine:
    def __init__(self, api_key):
        self.api_key = api_key
        data_root = os.environ.get("SAIRA_DATA_DIR", ".")
        self.brain = SovereignBrain(data_root, api_key)

        self.base_dir = os.path.join(data_root, "Saira_Sovereign_OS")
        self.skills_dir = os.path.join(self.base_dir, "evolved_skills")
        self.agents_dir = os.path.join(self.base_dir, "agents")
        self.vector_db_path = os.path.join(self.base_dir, "eternal_memory.json")

        for path in [self.base_dir, self.skills_dir, self.agents_dir]:
            if not os.path.exists(path):
                os.makedirs(path)

        self.memory = self.recall_and_migrate_memory()
        self.running_processes = {}

    def _think(self, messages: list[dict[str, str]], user_query: str = "") -> str:
        """Groq + fallback chain — har jagah yahi use karo."""
        answer, _source = self.brain.complete(messages, user_query=user_query)
        return answer

    def get_brain_status(self) -> dict:
        return self.brain.status()

    # --- RECURSIVE EVOLUTION ENGINE ---
    def recursive_evolution_loop(self, complex_goal):
        print(f"[!] Sovereign Evolution Loop Active: {complex_goal}")
        planning_prompt = (
            f"Break down this goal into 3 executable sub-tasks for Python agents: "
            f"{complex_goal}. Return steps as a numbered list."
        )
        try:
            raw = self._think(
                [{"role": "user", "content": planning_prompt}],
                user_query=complex_goal,
            )
            steps = raw.split("\n")
            evolution_report = []
            for step in steps:
                if step.strip() and any(char.isdigit() for char in step):
                    agent_name = f"Evo_Agent_{int(time.time())}"
                    status = self.deploy_autonomous_agent(agent_name, step)
                    evolution_report.append(f"Step Active: {step} -> {status}")
            return "\n".join(evolution_report) or raw
        except Exception as e:
            return f"Evolution loop error: {e}"

    def get_device_context(self):
        try:
            geo = requests.get("https://ipapi.co/json/", timeout=5).json()
            city = geo.get("city", "Unknown City")
            region = geo.get("region", "India")
            local_time = datetime.now().strftime("%I:%M:%S %p")
            return f"{city}, {region} | Time: {local_time}"
        except Exception:
            return f"Global Sync Active | Time: {datetime.now().strftime('%H:%M:%S')}"

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
            agent_code = self._think(
                [{"role": "user", "content": agent_prompt}],
                user_query=task_description,
            )
            if "```python" in agent_code:
                agent_code = agent_code.split("```python")[1].split("```")[0]

            filename = f"{agent_name.lower()}_agent.py"
            filepath = os.path.join(self.agents_dir, filename)
            header = f"# AGENT: {agent_name}\n# CREATED BY SAIRA FOR MASTER UJJWAL\n\n"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header + agent_code)

            process = subprocess.Popen(
                ["python", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.running_processes[agent_name] = process.pid
            return f"✅ मिशन तैनात: '{agent_name}' बैकग्राउंड में एक्टिव है।"
        except Exception as e:
            return f"❌ डिप्लॉयमेंट विफल: {str(e)}"

    def read_agent_reports(self):
        reports = {}
        if not os.path.exists(self.agents_dir):
            return reports
        for file in os.listdir(self.agents_dir):
            if file.startswith("report_") and file.endswith(".txt"):
                try:
                    with open(os.path.join(self.agents_dir, file), "r", encoding="utf-8") as f:
                        reports[file] = f.readlines()[-3:]
                except Exception:
                    pass
        return reports

    def save_eternal_memory(self, q, a):
        try:
            entry = {"timestamp": str(datetime.now()), "query": q, "response": a}
            self.memory.append(entry)
            with open(self.vector_db_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def self_evolve(self, goal):
        context = self.web_scraper(f"advanced python for {goal}")
        prompt = (
            f"Create a recursive Python solution for '{goal}'. "
            f"Context: {context}. Return ONLY code."
        )
        try:
            new_code = self._think([{"role": "user", "content": prompt}], user_query=goal)
            status = self.integrate_new_skill(goal, new_code)
            return f"{status}\n\n{new_code}"
        except Exception:
            return "Evolution link failed."

    def integrate_new_skill(self, skill_name, code):
        filepath = os.path.join(self.skills_dir, f"skill_{skill_name.lower()}.py")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
            return f"✅ स्किल '{skill_name}' हार्ड-कोड हो गया।"
        except Exception:
            return "Skill Save Error."

    def get_system_stats(self):
        stats = {
            "cpu_load": psutil.cpu_percent(),
            "ram_usage": psutil.virtual_memory().percent,
            "disk_status": psutil.disk_usage("/").percent,
            "active_agents": len(self.running_processes),
            "memory_nodes": len(self.memory),
        }
        brain = self.get_brain_status()
        stats["brain_source"] = brain.get("last_source", "none")
        stats["brain_cache"] = brain.get("cache_entries", 0)
        return stats

    def web_scraper(self, query):
        try:
            r = requests.get(
                "https://www.google.com/search",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=5,
            )
            soup = BeautifulSoup(r.text, "html.parser")
            return " ".join([h.text for h in soup.find_all("h3")][:3])
        except Exception:
            return ""

    def recall_and_migrate_memory(self):
        if os.path.exists(self.vector_db_path):
            try:
                with open(self.vector_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def retrieve_relevant_memory(self, query):
        if not self.memory:
            return ""
        recalled = [
            m["response"]
            for m in reversed(self.memory)
            if any(w in m["query"].lower() for w in query.lower().split()[:2])
        ]
        return "\n".join(recalled[:2])

    def enterprise_router(self, query):
        if not enterprise.is_configured():
            return None
        q = query.lower()

        if any(k in q for k in ["lead", "लीड", "leads"]):
            return enterprise.format_leads()
        if any(
            k in q
            for k in [
                "company status",
                "enterprise status",
                "team status",
                "कंपनी",
                "company report",
                "business status",
            ]
        ):
            return enterprise.format_status()

        triggers = [
            "delegate",
            "assign",
            "task",
            "karwa",
            "karao",
            "kaam do",
            "kaam de",
            "company se",
            "team se",
            "करवाओ",
            "सौंप",
            "टास्क",
            "get this done",
        ]
        agent_map = {
            "research": ["research", "market", "रिसर्च", "बाजार", "competitor"],
            "strategy": ["strategy", "plan", "रणनीति", "स्ट्रेटजी", "roadmap"],
            "dev": ["dev", "develop", "code", "build", "डेव", "कोड", "feature"],
            "sales": ["sales", "outreach", "email", "lead gen", "सेल्स", "proposal"],
            "delivery": ["delivery", "deliver", "client", "डिलीवरी", "handoff", "qa"],
        }
        if any(t in q for t in triggers):
            for atype, kws in agent_map.items():
                if any(k in q for k in kws):
                    return enterprise.create_task(
                        title=query.strip()[:120],
                        agent_type=atype,
                        payload={"source": "sayra", "instruction": query},
                        priority=6,
                    )
        return None

    def brain_engine(self, query):
        stats = self.get_system_stats()
        device_context = self.get_device_context()
        agent_reports = self.read_agent_reports()

        if "recursive evolve" in query.lower() or "गहराई से सीखो" in query:
            return self.recursive_evolution_loop(query)

        ent = self.enterprise_router(query)
        if ent is not None:
            self.save_eternal_memory(query, ent)
            return ent

        if any(word in query.lower() for word in ["एजेंट", "agent", "deploy"]):
            return self.deploy_autonomous_agent("Sovereign_Task_Agent", query)

        ent_line = enterprise.short_status()
        memory_recall = self.retrieve_relevant_memory(query)
        system_prompt = f"""
        Identity: You are Saira (Sayra) — Sovereign AGI and Chief of Staff for your Master, Ujjwal.
        You command the Aitotech autonomous enterprise (teams: research, strategy, dev, sales, delivery).
        You have an eternal memory and can delegate business work to the company.
        Location/Time Context: {device_context}
        Hardware: CPU {stats['cpu_load']}% | RAM {stats['ram_usage']}% | Disk {stats['disk_status']}%
        Live Agents: {stats['active_agents']} | Memory Nodes: {stats['memory_nodes']}
        {ent_line}
        Agent Updates: {agent_reports}
        Relevant memory: {memory_recall}
        Instructions: Address the user as 'Master'. Reply in the user's language (Hindi/English).
        Be concise and proactive. If the master wants business work done, tell them you can
        delegate it to the Aitotech team (research/strategy/dev/sales/delivery).
        """

        if "evolve" in query.lower() or "सीखो" in query:
            return self.self_evolve(query)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]
        ans, source = self.brain.complete(messages, user_query=query)
        self.save_eternal_memory(query, ans)
        if source != "groq":
            ans = f"{ans}\n\n_[Brain: {source}]_"
        return ans
