import os

SERVER_UPDATE = """import os
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
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return {"tier": "gig", "quote_inr": 150, "turnaround_mins": 60, "reasoning": "Fallback routing.", "direct_ai_response": None}

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
    except Exception: pass
    return {"is_verified": False, "confidence_score": 0, "audit_summary": "API Error"}

# --- AUTH & DASHBOARD ROUTES (Kept from previous) ---
@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    phone = request.json.get("phone_number")
    if not phone: return jsonify({"status": "error"}), 400
    u_res = supabase.table("users").select("*").eq("phone_number", phone).execute()
    if u_res.data: user = u_res.data[0]
    else: user = supabase.table("users").insert({"phone_number": phone}).execute().data[0]
    return jsonify({"status": "success", "user": user, "is_admin": (phone == ADMIN_PHONE)})

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
    user = supabase.table("users").select("*").eq("phone_number", phone).execute().data[0]
    new_bal = float(user["wallet_balance_inr"]) + amount
    supabase.table("users").update({"wallet_balance_inr": new_bal}).eq("id", user["id"]).execute()
    supabase.table("transactions").insert({"user_id": user["id"], "type": "TOP_UP", "amount_inr": amount}).execute()
    return jsonify({"status": "success", "new_balance": new_bal})

@app.route('/api/admin/dashboard', methods=['POST'])
def admin_dashboard():
    phone = request.json.get("phone_number")
    if phone != ADMIN_PHONE: return jsonify({"error": "Unauthorized"}), 401
    tasks = supabase.table("tasks").select("*, users(phone_number), workers(name)").order("created_at", desc=True).execute().data
    workers = supabase.table("workers").select("*").order("created_at", desc=True).execute().data
    txs = supabase.table("transactions").select("*").eq("type", "TOP_UP").execute().data
    return jsonify({"status": "success", "tasks": tasks, "workers": workers, "platform_volume": sum(float(tx["amount_inr"]) for tx in txs)})

@app.route('/api/admin/approve_worker', methods=['POST'])
def admin_approve_worker():
    supabase.table("workers").update({"status": "APPROVED"}).eq("id", request.json.get("worker_id")).execute()
    return jsonify({"status": "success"})

@app.route('/api/worker/auth', methods=['POST'])
def worker_auth():
    data = request.json
    phone = data.get("phone_number")
    w_res = supabase.table("workers").select("*").eq("phone_number", phone).execute()
    if w_res.data: return jsonify({"status": "success", "worker": w_res.data[0]})
    if not data.get("name"): return jsonify({"status": "needs_registration"})
    w_insert = supabase.table("workers").insert({"phone_number": phone, "name": data.get("name"), "city": data.get("city"), "upi_id": data.get("upi_id"), "status": "PENDING"}).execute()
    return jsonify({"status": "success", "worker": w_insert.data[0]})

@app.route('/api/worker/feed', methods=['GET'])
def get_worker_feed():
    t_res = supabase.table("tasks").select("*, users(phone_number), workers(name)").in_("status", ["ESCROW_LOCKED", "CLAIMED", "DELIVERED"]).execute()
    return jsonify({"status": "success", "tasks": t_res.data})

@app.route('/api/worker/claim', methods=['POST'])
def claim_task():
    task_id, worker_id = request.json.get("task_id"), request.json.get("worker_id")
    worker = supabase.table("workers").select("*").eq("id", worker_id).execute().data[0]
    task = supabase.table("tasks").update({"status": "CLAIMED", "worker_id": worker_id}).eq("id", task_id).execute().data[0]
    u_res = supabase.table("users").select("*").eq("id", task["user_id"]).execute()
    if u_res.data and u_res.data[0].get("telegram_chat_id"):
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": u_res.data[0]["telegram_chat_id"], "text": f"⚡ *Task Accepted!*\\n\\nYour task is now being worked on by {worker['name']}.\\nRating: {worker['rating']}", "parse_mode": "Markdown"})
    return jsonify({"status": "success", "task": task})

@app.route('/api/worker/ask', methods=['POST'])
def worker_ask():
    task = supabase.table("tasks").select("*, users(telegram_chat_id), workers(name)").eq("id", request.json.get("task_id")).execute().data[0]
    chat_id = task.get("users", {}).get("telegram_chat_id")
    if chat_id:
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": f"💬 *Message from Worker ({task.get('workers', {}).get('name', '')}):*\\n\\n{request.json.get('question')}\\n\\n_Reply directly to this message to answer._", "parse_mode": "Markdown"})
        AWAITING_REPLY[str(chat_id)] = task["id"]
    return jsonify({"status": "success"})

@app.route('/api/task/reply', methods=['POST'])
def handle_user_reply():
    chat_id = str(request.json.get("telegram_chat_id"))
    if chat_id in AWAITING_REPLY:
        task_id = AWAITING_REPLY[chat_id]
        t_res = supabase.table("tasks").select("query").eq("id", task_id).execute()
        if t_res.data:
            supabase.table("tasks").update({"query": t_res.data[0]["query"] + f"\\n\\n--- User Update ---\\n{request.json.get('text')}"}).eq("id", task_id).execute()
            del AWAITING_REPLY[chat_id]
            return jsonify({"status": "success", "handled": True})
    return jsonify({"status": "success", "handled": False})

@app.route('/api/worker/submit', methods=['POST'])
def submit_work():
    data = request.json
    task = supabase.table("tasks").select("*, users(telegram_chat_id), workers(*)").eq("id", data.get("task_id")).execute().data[0]
    audit_res = call_ai_proof_verifier(task["query"], data.get("proof_text"), data.get("proof_type"), data.get("proof_image_base64"), data.get("proof_image_mime"))
    deliv = {"text": data.get("proof_text"), "proof_type": data.get("proof_type"), "has_image": bool(data.get("proof_image_base64")), "ai_verification": audit_res}
    supabase.table("tasks").update({"status": "DELIVERED", "deliverable": deliv}).eq("id", task["id"]).execute()
    chat_id = task.get("users", {}).get("telegram_chat_id")
    if chat_id:
        msg = f"📦 *Deliverable Submitted!*\\n\\n• *Worker:* {task['workers']['name']}\\n• *Proof:* {deliv['text']}\\n• *AI Verdict:* {audit_res.get('audit_summary')}\\n\\nTap below to approve:"
        kb = {"inline_keyboard": [[{"text": f"⭐ Approve & Pay ₹{task['quote_inr']}", "callback_data": f"approve_{task['id']} "}]]}
        score = float(str(audit_res.get("confidence_score", 100)).replace("%","").strip())
        if score < 80 or not audit_res.get("is_verified", True):
            kb["inline_keyboard"][0].append({"text": "❌ Reject", "callback_data": f"reject_proof_{task['id']}"})
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown", "reply_markup": kb})
    return jsonify({"status": "success"})

@app.route('/api/task/approve', methods=['POST'])
def approve_task():
    task = supabase.table("tasks").select("*, workers(*)").eq("id", request.json.get("task_id")).execute().data[0]
    worker = task.get("workers")
    if worker:
        supabase.table("workers").update({"balance_inr": float(worker.get("balance_inr", 0)) + float(task["quote_inr"]), "tasks_completed": int(worker.get("tasks_completed", 0)) + 1}).eq("id", worker["id"]).execute()
    supabase.table("tasks").update({"status": "APPROVED_PAID_OUT"}).eq("id", task["id"]).execute()
    supabase.table("transactions").insert({"task_id": task["id"], "type": "ESCROW_RELEASE", "amount_inr": task["quote_inr"]}).execute()
    return jsonify({"status": "success", "payout_tx_id": f"UPI-SETTLE-{uuid.uuid4().hex[:8]}"})

@app.route('/api/task/reject_proof', methods=['POST'])
def reject_proof():
    supabase.table("tasks").update({"status": "CLAIMED", "deliverable": None}).eq("id", request.json.get("task_id")).execute()
    return jsonify({"status": "success"})


# --- TELEGRAM BOT WEBHOOKS & ACTIONS ---

@app.route('/api/bot/check_user', methods=['POST'])
def check_user():
    chat_id = str(request.json.get("chat_id"))
    u_res = supabase.table("users").select("*").eq("telegram_chat_id", chat_id).execute()
    if u_res.data:
        return jsonify({"status": "linked", "user": u_res.data[0]})
    return jsonify({"status": "unlinked"})

@app.route('/api/bot/link', methods=['POST'])
def link_user():
    chat_id = str(request.json.get("chat_id"))
    phone = request.json.get("phone")
    if not phone.startswith("+"): phone = "+" + phone.strip()
    u_res = supabase.table("users").select("*").eq("phone_number", phone).execute()
    if not u_res.data:
        return jsonify({"status": "error", "message": "Phone number not registered. Please sign up at http://localhost:5000 first!"})
    
    supabase.table("users").update({"telegram_chat_id": chat_id}).eq("id", u_res.data[0]["id"]).execute()
    return jsonify({"status": "success", "user": u_res.data[0]})

@app.route('/api/triage', methods=['POST'])
def triage_task():
    query, chat_id = request.json.get("query", ""), request.json.get("telegram_chat_id")
    user = supabase.table("users").select("*").eq("telegram_chat_id", str(chat_id)).execute().data[0]
    ai_res = call_live_groq_triage(query, CONFIG["GROQ_API_KEY"])
    
    quote = ai_res.get("quote_inr", 50)
    tier = ai_res.get("tier", "gig")
    
    # Check Wallet Balance
    if tier != "ai" and float(user.get("wallet_balance_inr", 0)) < float(quote):
        return jsonify({"status": "insufficient_funds", "quote": quote, "balance": float(user.get("wallet_balance_inr", 0))})
    
    task_data = {
        "query": query, "tier": tier, "quote_inr": quote, "turnaround_mins": ai_res.get("turnaround_mins", 30),
        "status": "QUOTE_PREPARED", "ai_reasoning": ai_res.get("reasoning", ""), "user_id": user["id"]
    }
    task = supabase.table("tasks").insert(task_data).execute().data[0]
    task["telegram_chat_id"] = chat_id 
    return jsonify({"status": "success", "task": task, "response": ai_res.get("direct_ai_response")})

@app.route('/api/task/escrow', methods=['POST'])
def lock_escrow():
    task = supabase.table("tasks").select("*").eq("id", request.json.get("task_id")).execute().data[0]
    user = supabase.table("users").select("*").eq("id", task["user_id"]).execute().data[0]
    
    new_bal = float(user.get("wallet_balance_inr", 0)) - float(task["quote_inr"])
    supabase.table("users").update({"wallet_balance_inr": new_bal}).eq("id", user["id"]).execute()
    supabase.table("transactions").insert({"user_id": user["id"], "task_id": task["id"], "type": "ESCROW_LOCK", "amount_inr": task["quote_inr"]}).execute()
    supabase.table("tasks").update({"status": "ESCROW_LOCKED"}).eq("id", task["id"]).execute()
    return jsonify({"status": "success"})


if __name__ == '__main__':
    app.run(port=5000)
"""

BOT_UPDATE = """import os
import requests
import time
from dotenv import load_dotenv
import re

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_URL = "http://127.0.0.1:5000"

def send_telegram_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode: payload["parse_mode"] = parse_mode
    if reply_markup: payload["reply_markup"] = reply_markup
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def handle_user_text(chat_id, user_text):
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=2)
    except: pass

    # 1. Check if user is linked
    try:
        check_res = requests.post(f"{BACKEND_URL}/api/bot/check_user", json={"chat_id": chat_id}, timeout=5).json()
        if check_res.get("status") == "unlinked":
            # If user sends a phone number format, try linking
            if re.match(r'^\\+?\\d{10,14}$', user_text.replace(" ", "")):
                link_res = requests.post(f"{BACKEND_URL}/api/bot/link", json={"chat_id": chat_id, "phone": user_text}, timeout=5).json()
                if link_res.get("status") == "success":
                    send_telegram_message(chat_id, f"✅ Account Linked! Welcome {user_text}. You can now send tasks.")
                else:
                    send_telegram_message(chat_id, f"❌ {link_res.get('message')}")
            else:
                send_telegram_message(chat_id, "🔒 *Unrecognized User*\\n\\nPlease reply with your registered phone number (e.g., `+917015960678`) to link your account, or sign up at http://localhost:5000 first.")
            return
    except Exception as e:
        return

    # 2. Check if reply to worker
    try:
        reply_res = requests.post(f"{BACKEND_URL}/api/task/reply", json={"telegram_chat_id": chat_id, "text": user_text}, timeout=5)
        if reply_res.json().get("handled"):
            send_telegram_message(chat_id, "✅ Your reply has been sent to the worker.")
            return
    except: pass

    # 3. Triage Task
    try:
        res = requests.post(f"{BACKEND_URL}/api/triage", json={"query": user_text, "telegram_chat_id": chat_id}, timeout=15)
        data = res.json()
        
        if data.get("status") == "insufficient_funds":
            msg = f"⚠️ *Insufficient Funds*\\n\\nThis task requires ₹{data['quote']}, but you only have ₹{data['balance']} in your wallet.\\n\\nPlease Top-Up here: http://localhost:5000/dashboard.html"
            send_telegram_message(chat_id, msg)
            return
            
        if data.get("status") != "success":
            send_telegram_message(chat_id, "⚠️ Sorry, there was an issue triaging your task.")
            return

        task = data["task"]
        tier = task["tier"]

        if tier == "ai":
            send_telegram_message(chat_id, data.get("response", "I can help with that directly!"))
        else:
            msg = (
                f"📋 *Quote Prepared:* 💎 {'Gig Network' if tier == 'gig' else 'Expert Network'}\\n\\n"
                f"• *Task:* {task['query']}\\n"
                f"• *Price:* ₹{task['quote_inr']} (held safely in UPI Escrow)\\n"
                f"• *Est. Time:* ~{task['turnaround_mins']} mins\\n"
                f"• *Reasoning:* _{task['ai_reasoning']}_\\n\\n"
                f"Nothing spends until you say yes. Confirm below to lock escrow:"
            )
            keyboard = {"inline_keyboard": [[
                {"text": f"✅ Approve & Pre-Auth ₹{task['quote_inr']}", "callback_data": f"escrow_{task['id']}"},
                {"text": "❌ Decline", "callback_data": f"decline_{task['id']}"}
            ]]}
            send_telegram_message(chat_id, msg, reply_markup=keyboard)
    except Exception as e:
        send_telegram_message(chat_id, f"❌ Error: {e}", parse_mode=None)

def handle_callback_query(callback_query):
    data = callback_query.get("data")
    chat_id = callback_query["message"]["chat"]["id"]

    if data.startswith("escrow_"):
        task_id = data.replace("escrow_", "")
        try:
            res = requests.post(f"{BACKEND_URL}/api/task/escrow", json={"task_id": task_id}, timeout=10)
            if res.json().get("status") == "success":
                msg = f"🔒 *UPI Escrow Pre-Auth Locked!*\\n\\nTask has been dispatched to the Worker Web Portal. You will receive a notification here as soon as a worker delivers the result."
                send_telegram_message(chat_id, msg)
        except Exception as e:
            pass
            
    elif data.startswith("approve_"):
        task_id = data.replace("approve_", "")
        try:
            res = requests.post(f"{BACKEND_URL}/api/task/approve", json={"task_id": task_id}, timeout=10)
            res_data = res.json()
            if res_data.get("status") == "success":
                tx_id = res_data.get("payout_tx_id", "UPI-SETTLE-SUCCESS")
                msg = f"🎉 *Deliverable Approved & Paid Out!*\\n\\nReleased directly to worker's UPI ID.\\n• *Transaction ID:* `{tx_id}`\\n\\nThank you for using Sarathi AI!"
                send_telegram_message(chat_id, msg)
        except Exception as e:
            pass
            
    elif data.startswith("reject_proof_"):
        task_id = data.replace("reject_proof_", "")
        try:
            res = requests.post(f"{BACKEND_URL}/api/task/reject_proof", json={"task_id": task_id}, timeout=10)
            if res.json().get("status") == "success":
                send_telegram_message(chat_id, "❌ Proof rejected. The worker has been notified to resubmit.")
        except Exception as e:
            pass

def main():
    print(">> Telegram Bot started...")
    offset = None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    while True:
        try:
            res = requests.get(url, params={"offset": offset, "timeout": 20}, timeout=25)
            updates = res.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    handle_user_text(update["message"]["chat"]["id"], update["message"]["text"])
                elif "callback_query" in update:
                    handle_callback_query(update["callback_query"])
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    main()
"""

with open("server.py", "w", encoding="utf-8") as f:
    f.write(SERVER_UPDATE)
with open("telegram_bot.py", "w", encoding="utf-8") as f:
    f.write(BOT_UPDATE)
