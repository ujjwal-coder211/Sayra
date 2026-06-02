# Saira (Sayra) — Role in the Aitotech ecosystem

## Sayra kya hai
**Sayra = Master Ujjwal ka personal Sovereign AGI / Chief of Staff.**
Ye ek persistent-memory AI assistant hai (eternal brain), jo:
- Master se baat karti hai (chat + dashboard — direct open, no login)
- Sab kuch **yaad** rakhti hai (eternal memory)
- Khud **local agents deploy** kar sakti hai (sovereign OS)
- Web se info la sakti hai, system monitor karti hai

## Sayra ka role (ecosystem me)
Sayra poore Aitotech setup ke **upar** baithti hai — **CEO / Commander layer**:

```
        (Master Ujjwal)
              │  (baat karta hai)
              ▼
   ┌─────────────────────┐
   │   SAYRA (AGI / CoS)  │  ← memory + command center
   └──────────┬──────────┘
              │ delegate / report  (HTTP)
              ▼
   ┌─────────────────────┐
   │  Aitotech-agents    │  ← research, strategy, dev, sales, delivery
   │  (the company)      │
   └──────────┬──────────┘
              ▼
   Supabase (memory) + ai-engine/n8n (real actions) + Aitotech website
```

- **Master** sirf **Sayra** se baat karta hai.
- **Sayra** business kaam **Aitotech-agents** company ko delegate karti hai aur
  results/leads wapas laa kar Master ko batati hai.
- Company ke agents kaam karte hain; n8n real actions (email/WhatsApp) karta hai.

## Naye commands (Sayra ko bol sakte ho)
| Aap bolo | Sayra karegi |
|---|---|
| "company status" / "कंपनी रिपोर्ट" | Aitotech enterprise ka live status + recent tasks |
| "leads dikhao" / "leads" | Website se aaye leads |
| "research team ko market research ka task do" | research agent ko task delegate |
| "sales team se outreach karwao" | sales agent ko task delegate |
| "dev team ko ye feature build karne ka task do" | dev agent ko task delegate |
| (koi bhi normal baat) | Sayra apni memory + context se jawaab degi |

> Delegation tab hota hai jab command me ek **trigger word** (task/karwao/delegate/सौंपो)
> + ek **team ka naam** (research/strategy/dev/sales/delivery) ho.

## Setup
1. `.env.example` ko `.env` banao, values bharo (`GROQ_API_KEY`, `ENTERPRISE_API_URL` = Railway URL).
2. `pip install -r requirements.txt`
3. `python app.py` → `http://localhost:7860` (dashboard seedha khulega)

`ENTERPRISE_API_URL` set na ho to Sayra akele (bina company ke) bhi normally chalti hai.

## Is update me kya behtar hua
- 🔗 **Enterprise bridge** (`enterprise.py`) — Sayra ab Aitotech company ko command karti hai.
- 🧠 **Memory ab use hoti hai** — purani relevant baatein system prompt me jaati hain.
- ⚡ **Fast boot** — `cv2`/`tensorflow` optional (na ho to crash nahi).
- 🔓 **Open dashboard** — login hata diya gaya (public URL pe koi bhi access kar sakta hai).
- 🐛 **web_scraper URL bug fix**; model env-configurable (default behtar 70b).
