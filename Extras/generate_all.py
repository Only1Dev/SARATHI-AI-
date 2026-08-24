import os

SERVER_PY = """import os
import json
import time
import uuid
import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__, static_folder='public')
CORS(app)

CONFIG = {
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", "")
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

AWAITING_REPLY = {}
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "+917015960679")

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return "Not found", 404

def call_live_groq_triage(query: str, api_key: str):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    sys_prompt = "You are the core Triage Intelligence Engine for Sarathi AI.\\nAnalyze the user's task request and classify it into one of 3 tiers:\\n1. 'ai' (Cost: 0) - Informational, drafting, coding.\\n2. 'gig' (Cost: 50-200) - Real-world actions (phone calls to vendors, app testing).\\n3. 'expert' (Cost: 300-1000) - Certified professionals (CA tax, legal review).\\nRespond strictly in valid JSON format:\\n{\\n  \\"tier\\": \\"ai\\" | \\"gig\\" | \\"expert\\",\\n  \\"reasoning\\": \\"1-2 sentence explanation\\",\\n  \\"confidence\\": 0.95,\\n  \\"quote_inr\\": 0 or integer in INR,\\n  \\"turnaround_mins\\": 0 or 15-60,\\n  \\"skills_required\\": [\\"skill1\\"],\\n  \\"direct_ai_response\\": \\"Full detailed answer to user request if tier is 'ai', else null\\"\\n}"
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": query}],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    return json.loads(r.json()["choices"][0]["message"]["content"])

def call_ai_proof_verifier(prompt, proof_text, proof_type, image_base64=None, image_mime=None):
    sys_prompt = "You are an AI Proof Verification Auditor for Sarathi AI.\\nCompare the User's Original Task against the Worker's Submitted Proof.\\nIf the proof does not match the requested task, return a low confidence score and set is_verified to false.\\nRespond strictly in valid JSON format:\\n{\\n  \\"is_verified\\": true,\\n  \\"confidence_score\\": 98,\\n  \\"audit_summary\\": \\"1 sentence verdict on proof validity\\"\\n}"
    gemini_key = CONFIG.get("GEMINI_API_KEY")
    if not image_base64 or not gemini_key:
        return {"is_verified": True, "confidence_score": 90, "audit_summary": "Auto-verified via text."}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gemini_key}"
    payload = {
        "contents": [{"parts": [
            {"text": sys_prompt + "\\n\\nUser Task: " + prompt + "\\nProof: " + proof_text},
            {"inlineData": {"mimeType": image_mime or "image/jpeg", "data": image_base64}}
        ]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
    except Exception as e:
        print("Gemini verify error:", e)
    return {"is_verified": False, "confidence_score": 0, "audit_summary": "API Error"}

# --- AUTH ROUTES ---
@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    phone = request.json.get("phone_number")
    if not phone: return jsonify({"status": "error", "message": "Missing phone"}), 400
    u_res = supabase.table("users").select("*").eq("phone_number", phone).execute()
    if u_res.data:
        user = u_res.data[0]
    else:
        u_res = supabase.table("users").insert({"phone_number": phone}).execute()
        user = u_res.data[0]
    is_admin = (phone == ADMIN_PHONE)
    return jsonify({"status": "success", "user": user, "is_admin": is_admin})

# --- USER DASHBOARD ROUTES ---
@app.route('/api/user/dashboard', methods=['POST'])
def user_dashboard():
    phone = request.json.get("phone_number")
    u_res = supabase.table("users").select("*").eq("phone_number", phone).execute()
    if not u_res.data: return jsonify({"error": "User not found"}), 404
    user = u_res.data[0]
    
    t_res = supabase.table("tasks").select("*, workers(name)").eq("user_id", user["id"]).order("created_at", desc=True).execute()
    escrow_held = sum(float(t["quote_inr"]) for t in t_res.data if t["status"] in ["ESCROW_LOCKED", "CLAIMED", "DELIVERED"])
    
    return jsonify({"status": "success", "user": user, "tasks": t_res.data, "escrow_held": escrow_held})

@app.route('/api/user/topup', methods=['POST'])
def user_topup():
    phone = request.json.get("phone_number")
    amount = float(request.json.get("amount", 0))
    u_res = supabase.table("users").select("*").eq("phone_number", phone).execute()
    if not u_res.data: return jsonify({"error": "User not found"}), 404
    user = u_res.data[0]
    
    new_bal = float(user["wallet_balance_inr"]) + amount
    supabase.table("users").update({"wallet_balance_inr": new_bal}).eq("id", user["id"]).execute()
    supabase.table("transactions").insert({
        "user_id": user["id"], "type": "TOP_UP", "amount_inr": amount
    }).execute()
    return jsonify({"status": "success", "new_balance": new_bal})

# --- ADMIN ROUTES ---
@app.route('/api/admin/dashboard', methods=['POST'])
def admin_dashboard():
    phone = request.json.get("phone_number")
    if phone != ADMIN_PHONE: return jsonify({"error": "Unauthorized"}), 401
    
    tasks = supabase.table("tasks").select("*, users(phone_number), workers(name)").order("created_at", desc=True).execute()
    workers = supabase.table("workers").select("*").order("created_at", desc=True).execute()
    txs = supabase.table("transactions").select("*").eq("type", "TOP_UP").execute()
    platform_volume = sum(float(tx["amount_inr"]) for tx in txs.data)
    
    return jsonify({
        "status": "success", 
        "tasks": tasks.data, 
        "workers": workers.data, 
        "platform_volume": platform_volume
    })

@app.route('/api/admin/approve_worker', methods=['POST'])
def admin_approve_worker():
    phone = request.json.get("phone_number")
    if phone != ADMIN_PHONE: return jsonify({"error": "Unauthorized"}), 401
    w_id = request.json.get("worker_id")
    supabase.table("workers").update({"status": "APPROVED"}).eq("id", w_id).execute()
    return jsonify({"status": "success"})

# --- WORKER ROUTES ---
@app.route('/api/worker/auth', methods=['POST'])
def worker_auth():
    data = request.json
    phone = data.get("phone_number")
    w_res = supabase.table("workers").select("*").eq("phone_number", phone).execute()
    if w_res.data:
        return jsonify({"status": "success", "worker": w_res.data[0]})
    
    if not data.get("name"):
        return jsonify({"status": "needs_registration"})
        
    w_insert = supabase.table("workers").insert({
        "phone_number": phone, "name": data.get("name"), "city": data.get("city"), "upi_id": data.get("upi_id"), "status": "PENDING"
    }).execute()
    return jsonify({"status": "success", "worker": w_insert.data[0]})

@app.route('/api/worker/feed', methods=['GET'])
def get_worker_feed():
    t_res = supabase.table("tasks").select("*, users(phone_number), workers(name)").in_("status", ["ESCROW_LOCKED", "CLAIMED", "DELIVERED"]).execute()
    return jsonify({"status": "success", "tasks": t_res.data})

@app.route('/api/worker/claim', methods=['POST'])
def claim_task():
    data = request.json or {}
    task_id = data.get("task_id")
    worker_id = data.get("worker_id")
    
    w_res = supabase.table("workers").select("*").eq("id", worker_id).execute()
    worker = w_res.data[0]
    
    t_res = supabase.table("tasks").update({"status": "CLAIMED", "worker_id": worker_id}).eq("id", task_id).execute()
    task = t_res.data[0]
    
    u_res = supabase.table("users").select("*").eq("id", task["user_id"]).execute()
    if u_res.data and u_res.data[0].get("telegram_chat_id"):
        chat_id = u_res.data[0]["telegram_chat_id"]
        msg = f"⚡ *Task Accepted!*\\n\\nYour task is now being worked on by {worker['name']}.\\nRating: {worker['rating']}"
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
        
    return jsonify({"status": "success", "task": task})

@app.route('/api/worker/ask', methods=['POST'])
def worker_ask():
    data = request.json or {}
    task_id = data.get("task_id")
    t_res = supabase.table("tasks").select("*, users(telegram_chat_id), workers(name)").eq("id", task_id).execute()
    task = t_res.data[0]
    chat_id = task.get("users", {}).get("telegram_chat_id")
    if chat_id:
        msg = f"💬 *Message from Worker ({task.get('workers', {}).get('name', '')}):*\\n\\n{data.get('question')}\\n\\n_Reply directly to this message to answer._"
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
        AWAITING_REPLY[str(chat_id)] = task_id
    return jsonify({"status": "success"})

@app.route('/api/worker/submit', methods=['POST'])
def submit_work():
    data = request.json
    task_id = data.get("task_id")
    t_res = supabase.table("tasks").select("*, users(telegram_chat_id), workers(*)").eq("id", task_id).execute()
    task = t_res.data[0]
    
    audit_res = call_ai_proof_verifier(task["query"], data.get("proof_text"), data.get("proof_type"), data.get("proof_image_base64"), data.get("proof_image_mime"))
    
    deliv = {
        "text": data.get("proof_text"),
        "proof_type": data.get("proof_type"),
        "has_image": bool(data.get("proof_image_base64")),
        "ai_verification": audit_res
    }
    supabase.table("tasks").update({"status": "DELIVERED", "deliverable": deliv}).eq("id", task_id).execute()
    
    chat_id = task.get("users", {}).get("telegram_chat_id")
    if chat_id:
        if data.get("proof_image_base64"):
            img_data = base64.b64decode(data.get("proof_image_base64"))
            requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendPhoto", data={"chat_id": chat_id}, files={"photo": ("proof.jpg", img_data, data.get("proof_image_mime") or "image/jpeg")})
            
        msg = f"📦 *Deliverable Submitted!*\\n\\n• *Worker:* {task['workers']['name']}\\n• *Proof:* {deliv['text']}\\n• *AI Verdict:* {audit_res.get('audit_summary')}\\n\\nTap below to approve:"
        kb = {"inline_keyboard": [[{"text": f"⭐ Approve & Pay ₹{task['quote_inr']}", "callback_data": f"approve_{task['id']} "}]]}
        
        score = float(str(audit_res.get("confidence_score", 100)).replace("%","").strip())
        if score < 80 or not audit_res.get("is_verified", True):
            kb["inline_keyboard"][0].append({"text": "❌ Reject Proof", "callback_data": f"reject_proof_{task['id']}"})
            
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown", "reply_markup": kb})
        
    return jsonify({"status": "success"})

# --- TELEGRAM BOT WEBHOOKS & ACTIONS ---
@app.route('/api/triage', methods=['POST'])
def triage_task():
    data = request.json or {}
    query = data.get("query", "")
    chat_id = data.get("telegram_chat_id")
    
    user = None
    if chat_id:
        u_res = supabase.table("users").select("*").eq("telegram_chat_id", str(chat_id)).execute()
        if u_res.data:
            user = u_res.data[0]
            
    target_worker = None
    if "shivam" in query.lower():
        target_worker = "Shivam"
        
    ai_res = call_live_groq_triage(query, CONFIG["GROQ_API_KEY"])
    
    task_data = {
        "query": query,
        "tier": ai_res.get("tier", "gig"),
        "quote_inr": ai_res.get("quote_inr", 50),
        "turnaround_mins": ai_res.get("turnaround_mins", 30),
        "status": "QUOTE_PREPARED",
        "target_worker_name": target_worker,
        "ai_reasoning": ai_res.get("reasoning", "")
    }
    if user:
        task_data["user_id"] = user["id"]
        
    t_res = supabase.table("tasks").insert(task_data).execute()
    task = t_res.data[0]
    task["telegram_chat_id"] = chat_id 
    
    return jsonify({"status": "success", "task": task, "response": ai_res.get("direct_ai_response")})

@app.route('/api/task/escrow', methods=['POST'])
def lock_escrow():
    data = request.json or {}
    task_id = data.get("task_id")
    
    t_res = supabase.table("tasks").select("*").eq("id", task_id).execute()
    if not t_res.data: return jsonify({"error": "Not found"}), 404
    task = t_res.data[0]
    
    if task.get("user_id"):
        u_res = supabase.table("users").select("*").eq("id", task["user_id"]).execute()
        user = u_res.data[0]
        new_bal = float(user.get("wallet_balance_inr", 0)) - float(task["quote_inr"])
        supabase.table("users").update({"wallet_balance_inr": new_bal}).eq("id", user["id"]).execute()
        
        supabase.table("transactions").insert({
            "user_id": user["id"], "task_id": task["id"], "type": "ESCROW_LOCK", "amount_inr": task["quote_inr"]
        }).execute()
        
    supabase.table("tasks").update({"status": "ESCROW_LOCKED"}).eq("id", task_id).execute()
    return jsonify({"status": "success"})

@app.route('/api/task/reply', methods=['POST'])
def handle_user_reply():
    chat_id = str(request.json.get("telegram_chat_id"))
    text = request.json.get("text")
    if chat_id in AWAITING_REPLY:
        task_id = AWAITING_REPLY[chat_id]
        t_res = supabase.table("tasks").select("query").eq("id", task_id).execute()
        if t_res.data:
            new_query = t_res.data[0]["query"] + f"\\n\\n--- User Update ---\\n{text}"
            supabase.table("tasks").update({"query": new_query}).eq("id", task_id).execute()
            del AWAITING_REPLY[chat_id]
            return jsonify({"status": "success", "handled": True})
    return jsonify({"status": "success", "handled": False})

@app.route('/api/task/approve', methods=['POST'])
def approve_task():
    task_id = request.json.get("task_id")
    t_res = supabase.table("tasks").select("*, workers(*)").eq("id", task_id).execute()
    task = t_res.data[0]
    
    worker = task.get("workers")
    if worker:
        new_bal = float(worker.get("balance_inr", 0)) + float(task["quote_inr"])
        supabase.table("workers").update({"balance_inr": new_bal, "tasks_completed": int(worker.get("tasks_completed", 0)) + 1}).eq("id", worker["id"]).execute()
        
    supabase.table("tasks").update({"status": "APPROVED_PAID_OUT"}).eq("id", task_id).execute()
    supabase.table("transactions").insert({"task_id": task["id"], "type": "ESCROW_RELEASE", "amount_inr": task["quote_inr"]}).execute()
    return jsonify({"status": "success", "task": task, "payout_tx_id": f"UPI-SETTLE-{uuid.uuid4().hex[:8]}"})

@app.route('/api/task/reject_proof', methods=['POST'])
def reject_proof():
    task_id = request.json.get("task_id")
    supabase.table("tasks").update({"status": "CLAIMED", "deliverable": None}).eq("id", task_id).execute()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(port=5000)
"""

with open("server.py", "w", encoding="utf-8") as f:
    f.write(SERVER_PY)

# --- DASHBOARD HTML ---
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sarathi AI - User Dashboard</title>
  <link rel="stylesheet" href="/css/cascade.css">
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    .task-item { background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid var(--border-color); }
    .badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .badge-ESCROW_LOCKED { background: #f59e0b; color: #fff; }
    .badge-CLAIMED { background: #3b82f6; color: #fff; }
    .badge-DELIVERED { background: #a855f7; color: #fff; }
    .badge-APPROVED_PAID_OUT { background: #10b981; color: #fff; }
  </style>
</head>
<body class="dark-theme">
  <nav class="navbar">
    <div class="logo">
      <div class="logo-icon" style="background: var(--brand-accent);">⚡</div>
      Sarathi AI Escrow
    </div>
    <div class="nav-links">
      <a href="#" onclick="localStorage.clear(); window.location.href='/'">Logout</a>
    </div>
  </nav>

  <main style="max-width: 1000px; margin: 2rem auto; padding: 0 1rem; display: grid; grid-template-columns: 1fr 2fr; gap: 2rem;">
    <div class="glass-card" style="height: fit-content;">
      <h3 style="margin-bottom: 1.5rem;">Your Wallet</h3>
      <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">Available Balance</div>
        <div style="font-size: 2.5rem; font-weight: 600; color: white;">₹ <span id="wallet-balance">0.00</span></div>
      </div>
      <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <i data-lucide="lock" style="color: #f59e0b; width: 16px;"></i>
          <span style="font-size: 0.9rem; color: var(--text-muted);">In Escrow</span>
        </div>
        <div style="font-weight: 600;">₹ <span id="escrow-balance">0.00</span></div>
      </div>
      <button class="btn btn-primary" style="width: 100%; padding: 0.8rem;" onclick="addFunds()">
        <i data-lucide="plus" style="width: 16px; margin-right: 0.5rem;"></i> Add Funds
      </button>
    </div>

    <div class="glass-card">
      <h3 style="margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">Your Tasks</h3>
      <div id="tasks-list">Loading...</div>
    </div>
  </main>

  <script>
    lucide.createIcons();
    const phone = localStorage.getItem("phone_number");
    if(!phone) window.location.href = '/';

    async function loadDashboard() {
      const res = await fetch('/api/user/dashboard', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phone_number: phone})
      });
      const data = await res.json();
      if(data.status === 'success') {
        document.getElementById('wallet-balance').innerText = data.user.wallet_balance_inr || "0.00";
        document.getElementById('escrow-balance').innerText = data.escrow_held || "0.00";
        
        const tasksList = document.getElementById('tasks-list');
        if(data.tasks.length === 0) {
          tasksList.innerHTML = `<div style="text-align:center; padding:2rem; color:#888;">No tasks yet.</div>`;
        } else {
          tasksList.innerHTML = data.tasks.map(t => `
            <div class="task-item">
              <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                <strong>${t.query}</strong>
                <span class="badge badge-${t.status}">${t.status.replace(/_/g, ' ')}</span>
              </div>
              <div style="font-size:0.85rem; color:#aaa;">Amount: ₹${t.quote_inr} | Worker: ${t.workers ? t.workers.name : 'Pending'}</div>
            </div>
          `).join('');
        }
      }
    }

    async function addFunds() {
      const amt = prompt("Enter amount to top up (Mock Stripe Topup):", "500");
      if(amt && !isNaN(amt)) {
        await fetch('/api/user/topup', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({phone_number: phone, amount: amt})
        });
        loadDashboard();
      }
    }

    loadDashboard();
  </script>
</body>
</html>"""

# --- ADMIN HTML ---
ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sarathi AI - Master Admin</title>
  <link rel="stylesheet" href="/css/cascade.css">
</head>
<body class="dark-theme">
  <nav class="navbar">
    <div class="logo">⚡ Sarathi AI Admin</div>
    <div class="nav-links"><a href="#" onclick="localStorage.clear(); window.location.href='/'">Logout</a></div>
  </nav>

  <main style="max-width: 1000px; margin: 2rem auto; padding: 0 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
      <h2 style="font-size: 2rem;">Master Dashboard</h2>
      <div class="glass-card" style="padding: 1rem 2rem;">
        <div style="font-size: 0.8rem; color: #888;">Platform Volume</div>
        <div style="font-size: 1.5rem; font-weight: 600;">₹ <span id="total-volume">0.00</span></div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
      <div class="glass-card">
        <h3>Worker Approvals</h3><hr style="border-color:#333; margin:1rem 0;">
        <div id="workers-list">Loading...</div>
      </div>
      <div class="glass-card">
        <h3>Recent Tasks</h3><hr style="border-color:#333; margin:1rem 0;">
        <div id="tasks-list">Loading...</div>
      </div>
    </div>
  </main>

  <script>
    const phone = localStorage.getItem("phone_number");
    if(!phone) window.location.href = '/';

    async function loadAdmin() {
      const res = await fetch('/api/admin/dashboard', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phone_number: phone})
      });
      const data = await res.json();
      if(data.status === 'success') {
        document.getElementById('total-volume').innerText = data.platform_volume || "0";
        
        document.getElementById('workers-list').innerHTML = data.workers.map(w => `
          <div style="background:#111; padding:1rem; border-radius:8px; margin-bottom:1rem; border:1px solid #333;">
            <div style="display:flex; justify-content:space-between;">
              <strong>${w.name} (${w.city})</strong> <span>${w.status}</span>
            </div>
            <div style="font-size:0.8rem; color:#aaa; margin-top:0.5rem;">Phone: ${w.phone_number} | UPI: ${w.upi_id}</div>
            ${w.status === 'PENDING' ? `<button onclick="approveWorker('${w.id}')" style="margin-top:0.5rem; background:#10b981; color:#fff; border:none; padding:5px 10px; border-radius:4px; cursor:pointer;">Approve</button>` : ''}
          </div>
        `).join('') || "No workers.";

        document.getElementById('tasks-list').innerHTML = data.tasks.map(t => `
          <div style="background:#111; padding:1rem; border-radius:8px; margin-bottom:1rem; border:1px solid #333;">
            <div><strong>${t.query}</strong></div>
            <div style="font-size:0.8rem; color:#aaa; margin-top:0.5rem;">Status: ${t.status} | Amt: ₹${t.quote_inr}</div>
          </div>
        `).join('') || "No tasks.";
      } else {
        alert("Unauthorized");
      }
    }

    async function approveWorker(id) {
      await fetch('/api/admin/approve_worker', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phone_number: phone, worker_id: id})
      });
      loadAdmin();
    }

    loadAdmin();
  </script>
</body>
</html>"""

# --- WORKER HTML ---
WORKER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Worker Portal - Sarathi AI</title>
  <link rel="stylesheet" href="/css/cascade.css">
  <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
  <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script>
</head>
<body class="dark-theme">
  <nav class="navbar">
    <div class="logo">⚡ Worker Portal</div>
    <div class="nav-links">
      <a href="#" onclick="localStorage.removeItem('worker_phone'); window.location.reload();" id="logout-btn" style="display:none;">Logout</a>
    </div>
  </nav>

  <main style="max-width: 800px; margin: 2rem auto; padding: 0 1rem;" id="main-content">
    
    <!-- Login/Register Box -->
    <div id="auth-box" class="glass-card" style="max-width:400px; margin: 4rem auto; text-align:center;">
      <h3>Worker Login</h3>
      <div id="step-phone">
        <input type="tel" id="phone-input" placeholder="+91 9999999999" style="width:100%; padding:0.8rem; margin:1rem 0; background:#111; color:#fff; border:1px solid #333;">
        <div id="recaptcha-container"></div>
        <button class="btn btn-primary" id="send-otp-btn" style="width:100%;" onclick="sendOTP()">Send OTP</button>
      </div>
      <div id="step-otp" style="display:none;">
        <input type="text" id="otp-input" placeholder="123456" style="width:100%; padding:0.8rem; margin:1rem 0; background:#111; color:#fff; border:1px solid #333;">
        <button class="btn btn-primary" id="verify-otp-btn" style="width:100%;" onclick="verifyOTP()">Verify</button>
      </div>
      <div id="step-register" style="display:none;">
        <h4>Complete Profile</h4>
        <input type="text" id="reg-name" placeholder="Full Name" style="width:100%; padding:0.8rem; margin:0.5rem 0; background:#111; color:#fff; border:1px solid #333;">
        <input type="text" id="reg-city" placeholder="City" style="width:100%; padding:0.8rem; margin:0.5rem 0; background:#111; color:#fff; border:1px solid #333;">
        <input type="text" id="reg-upi" placeholder="UPI ID" style="width:100%; padding:0.8rem; margin:0.5rem 0; background:#111; color:#fff; border:1px solid #333;">
        <button class="btn btn-primary" style="width:100%; margin-top:1rem;" onclick="completeRegistration()">Register</button>
      </div>
    </div>

    <!-- Dashboard Box -->
    <div id="dashboard-box" style="display:none;">
      <div class="glass-card" style="margin-bottom: 2rem; display:flex; justify-content:space-between;">
        <div>
          <h3>Welcome, <span id="worker-name"></span></h3>
          <p style="color:#aaa;">Status: <strong id="worker-status"></strong></p>
        </div>
        <div style="text-align:right;">
          <p style="font-size:0.8rem; color:#888;">Total Earnings</p>
          <p style="font-size:1.5rem; font-weight:bold;">₹ <span id="worker-earnings">0</span></p>
        </div>
      </div>
      
      <div id="pending-notice" style="display:none; background:#f59e0b22; color:#f59e0b; padding:1rem; border-radius:8px; border:1px solid #f59e0b55;">
        Your account is pending admin approval. You cannot see tasks yet.
      </div>

      <div id="task-feed-container" style="display:none;">
        <h3>Available Tasks</h3>
        <hr style="border-color:#333; margin:1rem 0;">
        <div id="task-feed">Loading...</div>
      </div>
    </div>

  </main>

  <script>
    const firebaseConfig = {
      apiKey: "AIzaSyA2lrC0hSXSh8QdP9qVvQa0Mg7nCy_HA-8",
      authDomain: "sarathi-ai-33e65.firebaseapp.com",
      projectId: "sarathi-ai-33e65"
    };
    if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();
    let confirmationResult = null;
    let verifiedPhone = "";

    window.onload = () => {
      const storedPhone = localStorage.getItem("worker_phone");
      if(storedPhone) {
        verifiedPhone = storedPhone;
        document.getElementById("auth-box").style.display = "none";
        document.getElementById("logout-btn").style.display = "block";
        loginWorker(storedPhone);
      } else {
        window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {'size': 'normal'});
        window.recaptchaVerifier.render();
      }
    };

    async function sendOTP() {
      verifiedPhone = document.getElementById('phone-input').value.replace(/\s+/g, '').trim();
      try {
        confirmationResult = await auth.signInWithPhoneNumber(verifiedPhone, window.recaptchaVerifier);
        document.getElementById('step-phone').style.display = 'none';
        document.getElementById('step-otp').style.display = 'block';
      } catch (e) { alert("Error: " + e.message); window.recaptchaVerifier.render(); }
    }

    async function verifyOTP() {
      const otp = document.getElementById('otp-input').value.trim();
      try {
        await confirmationResult.confirm(otp);
        loginWorker(verifiedPhone);
      } catch (e) { alert("Invalid OTP"); }
    }

    async function loginWorker(phone) {
      const res = await fetch('/api/worker/auth', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phone_number: phone})
      });
      const data = await res.json();
      
      if(data.status === 'needs_registration') {
        document.getElementById('step-otp').style.display = 'none';
        document.getElementById('step-phone').style.display = 'none';
        document.getElementById('step-register').style.display = 'block';
      } else if (data.status === 'success') {
        localStorage.setItem("worker_phone", phone);
        localStorage.setItem("worker_id", data.worker.id);
        
        document.getElementById("auth-box").style.display = "none";
        document.getElementById("dashboard-box").style.display = "block";
        document.getElementById("logout-btn").style.display = "block";
        
        document.getElementById("worker-name").innerText = data.worker.name;
        document.getElementById("worker-status").innerText = data.worker.status;
        document.getElementById("worker-earnings").innerText = data.worker.balance_inr || "0";
        
        if(data.worker.status === 'PENDING') {
          document.getElementById("pending-notice").style.display = "block";
        } else if (data.worker.status === 'APPROVED') {
          document.getElementById("task-feed-container").style.display = "block";
          loadFeed();
        }
      }
    }

    async function completeRegistration() {
      const name = document.getElementById('reg-name').value;
      const city = document.getElementById('reg-city').value;
      const upi = document.getElementById('reg-upi').value;
      const res = await fetch('/api/worker/auth', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phone_number: verifiedPhone, name, city, upi_id: upi})
      });
      const data = await res.json();
      if(data.status === 'success') {
        loginWorker(verifiedPhone);
      }
    }

    async function loadFeed() {
      const res = await fetch('/api/worker/feed');
      const data = await res.json();
      const feed = document.getElementById('task-feed');
      
      if(data.tasks.length === 0) {
        feed.innerHTML = "<p>No tasks available.</p>";
        return;
      }
      
      feed.innerHTML = data.tasks.map(t => `
        <div class="glass-card" style="margin-bottom:1rem;">
          <h4>${t.query}</h4>
          <p style="color:#aaa; font-size:0.9rem; margin:0.5rem 0;">Status: ${t.status} | Reward: ₹${t.quote_inr}</p>
          ${t.status === 'ESCROW_LOCKED' ? `<button class="btn btn-primary" onclick="claimTask('${t.id}')">Claim</button>` : ''}
          ${t.status === 'CLAIMED' && t.worker_id === localStorage.getItem("worker_id") ? `
            <div style="background:#111; padding:1rem; border-radius:4px; margin-top:1rem;">
              <textarea id="proof-${t.id}" style="width:100%; background:#000; color:#fff; padding:0.5rem;" placeholder="Type proof text..."></textarea>
              <button class="btn btn-primary" style="margin-top:0.5rem;" onclick="submitProof('${t.id}')">Submit Proof</button>
            </div>
          ` : ''}
        </div>
      `).join('');
    }

    async function claimTask(id) {
      await fetch('/api/worker/claim', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_id: id, worker_id: localStorage.getItem("worker_id")})
      });
      loadFeed();
    }
    
    async function submitProof(id) {
      const txt = document.getElementById(`proof-${id}`).value;
      await fetch('/api/worker/submit', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_id: id, proof_text: txt, proof_type: "Manual"})
      });
      alert("Proof submitted to user!");
      loadFeed();
    }
  </script>
</body>
</html>"""

with open("public/dashboard.html", "w", encoding="utf-8") as f:
    f.write(DASHBOARD_HTML)
with open("public/admin.html", "w", encoding="utf-8") as f:
    f.write(ADMIN_HTML)
with open("public/worker.html", "w", encoding="utf-8") as f:
    f.write(WORKER_HTML)

print("Files generated!")
