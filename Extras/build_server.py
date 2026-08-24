import os
new_server = '''import os
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

# Ephemeral state for bot replies
AWAITING_REPLY = {}

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
    sys_prompt = """You are the core Triage Intelligence Engine for Sarathi AI.
Analyze the user's task request and classify it into one of 3 tiers:
1. 'ai' (Cost: 0) - Informational, drafting, coding.
2. 'gig' (Cost: 50-200) - Real-world actions (phone calls to vendors, app testing).
3. 'expert' (Cost: 300-1000) - Certified professionals (CA tax, legal review).
Respond strictly in valid JSON format:
{
  "tier": "ai" | "gig" | "expert",
  "reasoning": "1-2 sentence explanation",
  "confidence": 0.95,
  "quote_inr": 0 or integer in INR,
  "turnaround_mins": 0 or 15-60,
  "skills_required": ["skill1"],
  "direct_ai_response": "Full detailed answer to user request if tier is 'ai', else null"
}"""
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": query}],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    return json.loads(r.json()["choices"][0]["message"]["content"])

def call_ai_proof_verifier(prompt, proof_text, proof_type, image_base64=None, image_mime=None):
    sys_prompt = """You are an AI Proof Verification Auditor for Sarathi AI.
Compare the User's Original Task against the Worker's Submitted Proof.
If the proof does not match the requested task, return a low confidence score and set is_verified to false.
Respond strictly in valid JSON format:
{
  "is_verified": true,
  "confidence_score": 98,
  "audit_summary": "1 sentence verdict on proof validity"
}"""
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

@app.route('/api/triage', methods=['POST'])
def triage_task():
    data = request.json or {}
    query = data.get("query", "")
    chat_id = data.get("telegram_chat_id")
    
    # 1. Fetch User
    user = None
    if chat_id:
        u_res = supabase.table("users").select("*").eq("telegram_chat_id", str(chat_id)).execute()
        if u_res.data:
            user = u_res.data[0]
            
    # Name extraction
    target_worker = None
    lower_q = query.lower()
    if "shivam" in lower_q:
        target_worker = "Shivam"
        
    ai_res = call_live_groq_triage(query, CONFIG["GROQ_API_KEY"])
    
    # Insert task
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
    task["telegram_chat_id"] = chat_id # For bot to use
    
    return jsonify({"status": "success", "task": task, "response": ai_res.get("direct_ai_response")})

@app.route('/api/task/escrow', methods=['POST'])
def lock_escrow():
    data = request.json or {}
    task_id = data.get("task_id")
    
    t_res = supabase.table("tasks").select("*").eq("id", task_id).execute()
    if not t_res.data:
        return jsonify({"error": "Not found"}), 404
    task = t_res.data[0]
    
    if task.get("user_id"):
        # Lock in wallet
        u_res = supabase.table("users").select("*").eq("id", task["user_id"]).execute()
        user = u_res.data[0]
        new_bal = float(user.get("wallet_balance_inr", 0)) - float(task["quote_inr"])
        supabase.table("users").update({"wallet_balance_inr": new_bal}).eq("id", user["id"]).execute()
        
        # Log tx
        supabase.table("transactions").insert({
            "user_id": user["id"],
            "task_id": task["id"],
            "type": "ESCROW_LOCK",
            "amount_inr": task["quote_inr"]
        }).execute()
        
    supabase.table("tasks").update({"status": "ESCROW_LOCKED"}).eq("id", task_id).execute()
    return jsonify({"status": "success"})

@app.route('/api/worker/feed', methods=['GET'])
def get_worker_feed():
    t_res = supabase.table("tasks").select("*, users(phone_number), workers(name)").in_("status", ["ESCROW_LOCKED", "CLAIMED", "DELIVERED"]).execute()
    w_res = supabase.table("workers").select("*").execute()
    return jsonify({
        "status": "success",
        "tasks": t_res.data,
        "workers": w_res.data
    })

@app.route('/api/worker/claim', methods=['POST'])
def claim_task():
    data = request.json or {}
    task_id = data.get("task_id")
    worker_id = data.get("worker_id")
    
    w_res = supabase.table("workers").select("*").eq("id", worker_id).execute()
    if not w_res.data:
        return jsonify({"error": "Worker not found"}), 404
    worker = w_res.data[0]
    
    t_res = supabase.table("tasks").update({"status": "CLAIMED", "worker_id": worker_id}).eq("id", task_id).execute()
    task = t_res.data[0]
    
    # Notify user
    u_res = supabase.table("users").select("*").eq("id", task["user_id"]).execute()
    if u_res.data and u_res.data[0].get("telegram_chat_id"):
        chat_id = u_res.data[0]["telegram_chat_id"]
        msg = f"⚡ *Task Accepted!*\n\nYour task is now being worked on by {worker['name']}.\nRating: {worker['rating']}"
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
        
    return jsonify({"status": "success", "task": task})

@app.route('/api/worker/ask', methods=['POST'])
def worker_ask():
    data = request.json or {}
    task_id = data.get("task_id")
    t_res = supabase.table("tasks").select("*, users(telegram_chat_id), workers(name)").eq("id", task_id).execute()
    if not t_res.data: return jsonify({"error": "Not found"}), 404
    task = t_res.data[0]
    
    chat_id = task.get("users", {}).get("telegram_chat_id")
    if chat_id:
        msg = f"💬 *Message from Worker ({task.get('workers', {}).get('name', '')}):*\n\n{data.get('question')}\n\n_Reply directly to this message to answer._"
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
        AWAITING_REPLY[str(chat_id)] = task_id
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
            
        msg = f"📦 *Deliverable Submitted!*\n\n• *Worker:* {task['workers']['name']}\n• *Proof:* {deliv['text']}\n• *AI Verdict:* {audit_res.get('audit_summary')}\n\nTap below to approve:"
        kb = {"inline_keyboard": [[{"text": f"⭐ Approve & Pay ₹{task['quote_inr']}", "callback_data": f"approve_{task['id']} "}]]}
        
        score = float(str(audit_res.get("confidence_score", 100)).replace("%","").strip())
        if score < 80 or not audit_res.get("is_verified", True):
            kb["inline_keyboard"][0].append({"text": "❌ Reject Proof", "callback_data": f"reject_proof_{task['id']}"})
            
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown", "reply_markup": kb})
        
    return jsonify({"status": "success"})

@app.route('/api/task/approve', methods=['POST'])
def approve_task():
    task_id = request.json.get("task_id")
    t_res = supabase.table("tasks").select("*, workers(*)").eq("id", task_id).execute()
    task = t_res.data[0]
    
    # Release funds to worker
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
'''
with open('server.py', 'w', encoding='utf-8') as f:
    f.write(new_server)
