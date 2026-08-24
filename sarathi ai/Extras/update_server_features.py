import os

with open("server.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. AI Budget constraint
old_prompt = """sys_prompt = "You are the core Triage Intelligence Engine for Sarathi AI.\\nAnalyze the user's task request and classify it into one of 3 tiers:\\n1. 'ai' (Cost: 0) - Informational, drafting, coding.\\n2. 'gig' (Cost: 50-200) - Real-world actions (phone calls to vendors, app testing).\\n3. 'expert' (Cost: 300-1000) - Certified professionals (CA tax, legal review).\\nRespond strictly in valid JSON format:\\n{\\n  \\"tier\\": \\"ai\\" | \\"gig\\" | \\"expert\\",\\n  \\"reasoning\\": \\"1-2 sentence explanation\\",\\n  \\"confidence\\": 0.95,\\n  \\"quote_inr\\": 0 or integer in INR,\\n  \\"turnaround_mins\\": 0 or 15-60,\\n  \\"skills_required\\": [\\"skill1\\"],\\n  \\"direct_ai_response\\": \\"Full detailed answer to user request if tier is 'ai', else null\\"\\n}\""""
new_prompt = """sys_prompt = "You are the core Triage Intelligence Engine for Sarathi AI.\\nAnalyze the user's task request and classify it into one of 3 tiers:\\n1. 'ai' (Cost: 0) - Informational, drafting, coding.\\n2. 'gig' (Cost: 50-200) - Real-world actions (phone calls to vendors, app testing).\\n3. 'expert' (Cost: 300-1000) - Certified professionals (CA tax, legal review).\\nIMPORTANT BUDGET RULE: If the user explicitly mentions a maximum budget (e.g., 'under 100', 'for 50 bucks'), your `quote_inr` MUST NOT exceed that amount!\\nRespond strictly in valid JSON format:\\n{\\n  \\"tier\\": \\"ai\\" | \\"gig\\" | \\"expert\\",\\n  \\"reasoning\\": \\"1-2 sentence explanation\\",\\n  \\"confidence\\": 0.95,\\n  \\"quote_inr\\": 0 or integer in INR,\\n  \\"turnaround_mins\\": 0 or 15-60,\\n  \\"skills_required\\": [\\"skill1\\"],\\n  \\"direct_ai_response\\": \\"Full detailed answer to user request if tier is 'ai', else null\\"\\n}\""""

if old_prompt in code:
    code = code.replace(old_prompt, new_prompt)

# 2. Add /api/worker/decline
decline_route = """
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
        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": f"⚠️ *Task Declined by Network*\\n\\nA worker viewed your task '{task['query']}' but declined it, likely because the budget (₹{task['quote_inr']}) is too low.\\n\\n💰 The ₹{task['quote_inr']} has been fully refunded to your wallet! Please submit a new request with a higher budget if needed.", "parse_mode": "Markdown"})
    return jsonify({"status": "success"})
"""
if "/api/worker/decline" not in code:
    code = code.replace("@app.route('/api/worker/claim'", decline_route + "\n@app.route('/api/worker/claim'")

# 3. Update task/escrow to return turnaround
escrow_old = """return jsonify({"status": "success"})"""
escrow_new = """return jsonify({"status": "success", "turnaround": task.get("turnaround_mins", 30)})"""
if "def lock_escrow():" in code and escrow_old in code:
    # careful replacement
    code = code.replace("return jsonify({\"status\": \"success\"})", "return jsonify({\"status\": \"success\", \"turnaround\": task.get(\"turnaround_mins\", 30)})", 1)

# 4. Add claimed_at to /api/worker/claim
claim_old = """task = supabase.table("tasks").update({"status": "CLAIMED", "worker_id": worker_id}).eq("id", task_id).execute().data[0]"""
claim_new = """
    # store claim time in JSONB
    t_data = supabase.table("tasks").select("deliverable").eq("id", task_id).execute().data[0]
    deliv = t_data.get("deliverable") or {}
    deliv["claimed_at"] = time.time()
    task = supabase.table("tasks").update({"status": "CLAIMED", "worker_id": worker_id, "deliverable": deliv}).eq("id", task_id).execute().data[0]"""
if claim_old in code:
    code = code.replace(claim_old, claim_new)

# 5. Add Background Timeout Thread
timeout_watcher = """
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
                        requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage", json={"chat_id": chat_id, "text": f"⏳ *Worker Timed Out!*\\n\\nThe worker failed to submit a deliverable within {int(turnaround)} minutes. The task has been automatically revoked and placed back on the global Worker Network to be claimed by someone else.", "parse_mode": "Markdown"})
        except Exception as e:
            pass
        time.sleep(30)

threading.Thread(target=task_timeout_watcher, daemon=True).start()
"""
if "task_timeout_watcher" not in code:
    code = code.replace("if __name__ == '__main__':", timeout_watcher + "\nif __name__ == '__main__':")

with open("server.py", "w", encoding="utf-8") as f:
    f.write(code)
