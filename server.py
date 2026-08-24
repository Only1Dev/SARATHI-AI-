import os
import json
import time
import uuid
import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import stripe
from flask import redirect
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
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
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
    sys_prompt = "You are the core Triage Intelligence Engine for Sarathi AI.\nAnalyze the user's task request and classify it into one of 3 tiers:\n1. 'ai' (Cost: 0) - Informational, drafting, coding.\n2. 'gig' (Cost: 50-200) - Real-world actions (phone calls to vendors, app testing).\n3. 'expert' (Cost: 300-1000) - Certified professionals (CA tax, legal review).\nIMPORTANT BUDGET RULE: If the user explicitly mentions a maximum budget (e.g., 'under 100'), your `quote_inr` MUST NOT exceed that amount! If tier is 'gig' or 'expert', `quote_inr` MUST BE AT LEAST 50.\nRespond strictly in valid JSON format:\n{\n  \"tier\": \"ai\" | \"gig\" | \"expert\",\n  \"reasoning\": \"1-2 sentence explanation\",\n  \"confidence\": 0.95,\n  \"quote_inr\": 0 (only if ai) or integer >= 50,\n  \"turnaround_mins\": 0 or 15-60,\n  \"skills_required\": [\"skill1\"],\n  \"direct_ai_response\": \"Full detailed answer to user request if tier is 'ai', else null\"\n}"
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
    sys_prompt = "You are an AI Proof Verification Auditor for Sarathi AI.\nCompare the User's Original Task against the Worker's Submitted Proof.\nIf the proof does not match the requested task, return a low confidence score and set is_verified to false.\nRespond strictly in valid JSON format:\n{\n  \"is_verified\": true,\n  \"confidence_score\": 98,\n  \"audit_summary\": \"1 sentence verdict on proof validity\"\n}"
    gemini_key = CONFIG.get("GEMINI_API_KEY")
    if not image_base64 or not gemini_key:
        return {"is_verified": True, "confidence_score": 90, "audit_summary": "Auto-verified via text."}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gemini_key}"
    payload = {
        "contents": [{"parts": [
            {"text": sys_prompt + "\n\nUser Task: " + prompt + "\nProof: " + proof_text},
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
    return jsonify({"status": "success", "turnaround": task.get("turnaround_mins", 30)})

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


@app.route('/api/worker/decline', methods=['POST'])
def decline_task():
    task = supabase.table("tasks").select("*, users(telegram_chat_id)").eq("id", request.json.get("task_id")).execute().data[0]
    supabase.table("tasks").update({"status": "DECLINED_BY_WORKER"}).eq("id", task["id"]).execute()
    
    # Refund User
    user = supabase.table("users").select("*").eq("id", task["user_id"]).execute().data[0]
    new_bal = float(user.get("wallet_balance_inr", 0)) + float(task["quote_inr"])
    supabase.table("users").update({"wallet_balance_inr": new_bal}).eq("id", user["id"]).execute()
    
    chat_id = task.get("users", {}).get("telegram_chat_id")
    if chat_id:
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": f"⚠️ *Task Declined by Network*\n\nA worker viewed your task '{task['query']}' but declined it, likely because the budget (₹{task['quote_inr']}) is too low.\n\n💰 The ₹{task['quote_inr']} has been fully refunded to your wallet! Please submit a new request with a higher budget if needed.", "parse_mode": "Markdown"})
    return jsonify({"status": "success"})

@app.route('/api/worker/claim', methods=['POST'])
def claim_task():
    task_id, worker_id = request.json.get("task_id"), request.json.get("worker_id")
    worker = supabase.table("workers").select("*").eq("id", worker_id).execute().data[0]
    
    # store claim time in JSONB
    t_data = supabase.table("tasks").select("deliverable").eq("id", task_id).execute().data[0]
    deliv = t_data.get("deliverable") or {}
    deliv["claimed_at"] = time.time()
    task = supabase.table("tasks").update({"status": "CLAIMED", "worker_id": worker_id, "deliverable": deliv}).eq("id", task_id).execute().data[0]
    u_res = supabase.table("users").select("*").eq("id", task["user_id"]).execute()
    if u_res.data and u_res.data[0].get("telegram_chat_id"):
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": u_res.data[0]["telegram_chat_id"], "text": f"⚡ *Task Accepted!*\n\nYour task is now being worked on by {worker['name']}.\nRating: {worker['rating']}", "parse_mode": "Markdown"})
    return jsonify({"status": "success", "task": task})

@app.route('/api/worker/ask', methods=['POST'])
def worker_ask():
    task_id = request.json.get("task_id")
    question = request.json.get("question", "")
    image_base64 = request.json.get("image_base64")
    
    task = supabase.table("tasks").select("*, users(telegram_chat_id), workers(name)").eq("id", task_id).execute().data[0]
    chat_id = task["users"]["telegram_chat_id"]
    msg = f"💬 *Message from {task['workers']['name']}:*\n\n{question}" if question else f"🖼 *Photo from {task['workers']['name']}*"
    
    if image_base64:
        try:
            import base64
            image_bytes = base64.b64decode(image_base64)
            files = {'photo': ('photo.jpg', image_bytes, 'image/jpeg')}
            payload = {'chat_id': chat_id, 'caption': msg, 'parse_mode': 'Markdown'}
            requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendPhoto", data=payload, files=files)
        except Exception as e:
            print("Error sending chat photo:", e)
            requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    else:
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
        
    # Store state so we can route their reply
    AWAITING_REPLY[str(chat_id)] = task["id"]
    return jsonify({"status": "success"})

@app.route('/api/task/reply', methods=['POST'])
def handle_user_reply():
    chat_id = str(request.json.get("telegram_chat_id"))
    if chat_id in AWAITING_REPLY:
        task_id = AWAITING_REPLY[chat_id]
        t_res = supabase.table("tasks").select("query").eq("id", task_id).execute()
        if t_res.data:
            supabase.table("tasks").update({"query": t_res.data[0]["query"] + f"\n\n--- User Update ---\n{request.json.get('text')}"}).eq("id", task_id).execute()
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
        msg = f"📦 *Deliverable Submitted!*\n\n• *Worker:* {task['workers']['name']}\n• *Proof:* {deliv['text']}\n• *AI Verdict:* {audit_res.get('audit_summary')}\n\nTap below to approve:"
        kb = {"inline_keyboard": [[{"text": f"⭐ Approve & Pay ₹{task['quote_inr']}", "callback_data": f"approve_{task['id']}"}]]}
        score = float(str(audit_res.get("confidence_score", 100)).replace("%","").strip())
        if score < 80 or not audit_res.get("is_verified", True):
            kb["inline_keyboard"][0].append({"text": "❌ Reject", "callback_data": f"reject_proof_{task['id']}"})
        
        # Send photo if provided, else just text
        if data.get("proof_image_base64"):
            try:
                import io
                image_bytes = base64.b64decode(data["proof_image_base64"])
                files = {'photo': ('proof.jpg', image_bytes, 'image/jpeg')}
                payload = {'chat_id': chat_id, 'caption': msg, 'parse_mode': 'Markdown'}
                if kb:
                    payload['reply_markup'] = json.dumps(kb)
                res = requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendPhoto", data=payload, files=files)
                print("sendPhoto status:", res.status_code, res.text)
                if res.status_code != 200:
                    requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown", "reply_markup": kb})
            except Exception as e:
                print("Error sending photo:", e)
                requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown", "reply_markup": kb})
        else:
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
    
    # Auto-prepend +91 for 10-digit Indian numbers
    phone_digits = phone.replace("+", "").replace(" ", "")
    if len(phone_digits) == 10:
        phone = "+91" + phone_digits
        
    u_res = supabase.table("users").select("*").eq("phone_number", phone).execute()
    
    if not u_res.data:
        # User exists in Firebase but not in Supabase yet. Auto-create them!
        u_insert = supabase.table("users").insert({"phone_number": phone}).execute()
        user = u_insert.data[0]
    else:
        user = u_res.data[0]
    
    supabase.table("users").update({"telegram_chat_id": chat_id}).eq("id", user["id"]).execute()
    return jsonify({"status": "success", "user": user})

@app.route('/api/triage', methods=['POST'])
def triage_task():
    query, chat_id = request.json.get("query", ""), request.json.get("telegram_chat_id")
    user = supabase.table("users").select("*").eq("telegram_chat_id", str(chat_id)).execute().data[0]
    ai_res = call_live_groq_triage(query, CONFIG["GROQ_API_KEY"])
    
    tier = ai_res.get("tier", "gig")
    quote = ai_res.get("quote_inr", 50)
    
    # Enforce minimum pricing for non-AI tasks
    if tier != "ai" and quote < 50:
        quote = 50
    
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
    
    if new_bal < 0:
        return jsonify({"status": "error", "message": "Insufficient funds in wallet to cover this task."})
        
    supabase.table("users").update({"wallet_balance_inr": new_bal}).eq("id", user["id"]).execute()
    supabase.table("transactions").insert({"user_id": user["id"], "task_id": task["id"], "type": "ESCROW_LOCK", "amount_inr": task["quote_inr"]}).execute()
    supabase.table("tasks").update({"status": "ESCROW_LOCKED"}).eq("id", task["id"]).execute()
    
    # Send reliable Formspree email notification to workers
    try:
        requests.post('https://formspree.io/f/xgawbqaq', json={
            'subject': 'New Task Available on Sarathi AI Dashboard',
            'task_id': task['id'],
            'description': task['query'],
            'reward_inr': task['quote_inr'],
            'status': 'ESCROW_LOCKED'
        }, headers={'Accept': 'application/json'}, timeout=5)
    except Exception as e:
        print("Formspree error:", e)
        
    return jsonify({"status": "success", "turnaround": task.get("turnaround_mins", 30)})



# --- STRIPE ROUTES ---
@app.route('/api/stripe/create-checkout-session', methods=['POST'])
def create_checkout_session():
    amount = int(request.json.get("amount", 500))
    phone = request.json.get("phone_number")
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'inr',
                'product_data': {'name': 'Sarathi AI Escrow Top-up'},
                'unit_amount': amount * 100,
            },
            'quantity': 1,
        }],
        mode='payment',
               success_url=f"{request.host_url}api/stripe/success?session_id={{CHECKOUT_SESSION_ID}}&phone={phone}&amount={amount}",
        cancel_url=f"{request.host_url}dashboard.html",
    )
    return jsonify({"url": session.url})

@app.route('/api/stripe/success', methods=['GET'])
def stripe_success():
    session_id = request.args.get('session_id')
    phone = request.args.get('phone', '').replace(' ', '+')
    try:
        amount = float(request.args.get('amount', 0))
    except:
        amount = 0
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            existing = supabase.table("transactions").select("*").eq("stripe_payment_id", session_id).execute()
            if not existing.data:
                u_res = supabase.table("users").select("*").eq("phone_number", phone).execute()
                if u_res.data:
                    user = u_res.data[0]
                    new_bal = float(user.get("wallet_balance_inr", 0)) + amount
                    supabase.table("users").update({"wallet_balance_inr": new_bal}).eq("id", user["id"]).execute()
                    supabase.table("transactions").insert({
                        "user_id": user["id"], "type": "TOP_UP", "amount_inr": amount, "stripe_payment_id": session_id
                    }).execute()
    except Exception as e:
        print("Stripe error:", e)
            
    return redirect("/dashboard.html")



import threading
def task_timeout_watcher():
    while True:
        try:
            res = supabase.table("tasks").select("*, users(telegram_chat_id)").eq("status", "CLAIMED").execute()
            for t in res.data:
                claimed_at = t.get("deliverable", {}).get("claimed_at", 0) if t.get("deliverable") else 0
                turnaround = float(t.get("turnaround_mins", 30))
                # Auto-revoke if over time limit
                if claimed_at > 0 and time.time() > claimed_at + (turnaround * 60):
                    supabase.table("tasks").update({"status": "ESCROW_LOCKED", "worker_id": None, "deliverable": None}).eq("id", t["id"]).execute()
                    chat_id = t.get("users", {}).get("telegram_chat_id")
                    if chat_id:
                        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": f"⏳ *Worker Timed Out!*\n\nThe worker failed to submit a deliverable within {int(turnaround)} minutes. The task has been automatically revoked and placed back on the global Worker Network to be claimed by someone else.", "parse_mode": "Markdown"})
        except Exception as e:
            pass
        time.sleep(30)

threading.Thread(target=task_timeout_watcher, daemon=True).start()

if __name__ == '__main__':
    app.run(port=5000)
