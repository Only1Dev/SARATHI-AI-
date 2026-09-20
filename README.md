# ⚡ SARATHI AI 
### Conversational AI & Human Task Routing Platform over WhatsApp/Telegram with Instant UPI Escrow

---

## 🎯 The Core Problem & Value Proposition

Existing gig and freelance platforms (Fiverr, Upwork, Urban Company) force users into bulky forms, bidding wars, complex dashboards, and high platform commissions. 

**Sarathi AI** introduces a conversational task routing paradigm:
> *"Text or speak any task into WhatsApp / Telegram. AI answers free (₹0), or a real human worker executes it for ₹50–₹500 — held safely in UPI Escrow and paid out instantly upon your approval."*

```
                 ┌──────────────────────────────────────┐
                 │ User sends text/voice note via WA/TG │
                 └──────────────────┬───────────────────┘
                                    │
                        [ AI Triage & Language Engine ]
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
 ┌───────────────┐        ┌───────────────────┐      ┌──────────────────┐
 │  AI Tier (₹0) │        │  Gig Worker Tier  │      │  Verified Expert │
 │  (Instant)    │        │  (₹50 - ₹500)     │      │  (₹500 - ₹5,000) │
 ├───────────────┤        ├───────────────────┤      ├──────────────────┤
 │ • Summaries   │        │ • Calling vendors │      │ • CAs / Tax audit│
 │ • Drafting    │        │ • Translation     │      │ • Legal review   │
 │ • Price lookup│        │ • Device testing  │      │ • Tech architect │
 │ • Regional AI │        │ • Physical visits │      │ • Doctor consult │
 └───────────────┘        └─────────┬─────────┘      └─────────┬────────┘
                                    │                          │
                                    └────────────┬─────────────┘
                                                 │
                                   [ In-chat Quote: "₹120" ]
                                                 │
                                   [ User taps: "Pay via UPI" ]
                                                 │
                                   [ Worker Delivers Result ]
                                                 │
                                   [ User approves → Instant UPI ]
```

---

## 🌟 Key Features of the Prototype

1. **Triple-Panel Hackathon Simulator**:
   - **Pane 1 (Requester Phone UI)**: Realistic mobile frame with chat stream, simulated Hindi/English voice note button, live quote cards, and deliverable approval actions.
   - **Pane 2 (Worker Dispatch Board)**: Live feed of escrow-locked jobs where registered gig workers can claim tasks, submit proof, and track instant UPI balances.
   - **Pane 3 (AI Triage & Escrow Brain Inspector)**: Real-time telemetry inspector for judges showing intent classification, confidence scores, compute cost vs. human wage, and the escrow state machine.
2. **Zero-Friction UPI Escrow**:
   - Simulates UPI QR Codes and 1-tap pre-auth (PhonePe, Google Pay, Paytm). Money is held in virtual escrow until the user is satisfied.
3. **Works 100% Free Out of the Box**:
   - Built-in heuristic triage handles real Indian use cases (calling local stores in Koramangala, document translation, legal liability audits) without requiring any paid API keys.
4. **Live AI Ready (Google Gemini Free Tier)**:
   - Easily plug in your free Gemini API key to enable dynamic multi-modal reasoning.
5. **Real Smartphone Telegram Bot Integration**:
   - Run `python telegram_bot.py` with a free `@BotFather` token to demo the system directly from your smartphone during hackathon judging!

---

## 🚀 How to Run Locally

### 1. Start the Full-Stack Server
Open your terminal in this directory and run:
```bash
python server.py
```
Open **http://127.0.0.1:5000** in your browser to view the interactive 3-Pane Simulator.

---

### 2. (Optional) Enable Live AI with Google Gemini (Free)
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/).
2. Click **API Keys & Config** on the top navigation bar of the web app and paste your key (or add `GEMINI_API_KEY=...` to your `.env` file).

---

### 3. (Optional) Run Live on Real Phones via Telegram Bot
1. Open Telegram, search for `@BotFather`, and send `/newbot` to create a free bot and get your token.
2. Add your token in the app settings or in `.env` under `TELEGRAM_BOT_TOKEN`.
3. In a separate terminal, run:
```bash
python telegram_bot.py
```
Now, message your bot on Telegram from your phone and watch live tasks appear across the 3-panel dashboard!

---
