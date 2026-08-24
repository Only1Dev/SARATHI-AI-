import os
new_bot = '''import os
import requests
import time
from dotenv import load_dotenv

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

    # First check if this is a reply to a worker question
    try:
        reply_res = requests.post(f"{BACKEND_URL}/api/task/reply", json={"telegram_chat_id": chat_id, "text": user_text}, timeout=5)
        if reply_res.json().get("handled"):
            send_telegram_message(chat_id, "✅ Your reply has been sent to the worker.")
            return
    except: pass

    # Otherwise, triage the task
    try:
        res = requests.post(f"{BACKEND_URL}/api/triage", json={"query": user_text, "telegram_chat_id": chat_id}, timeout=15)
        data = res.json()
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
                msg = (
                    f"🔒 *UPI Escrow Pre-Auth Locked!*\\n\\n"
                    f"₹50 pre-authorized via UPI.\\n"
                    f"Task has been dispatched to the Worker Web Portal (`http://127.0.0.1:5000/worker`). You will receive a notification here as soon as a worker delivers the result."
                )
                send_telegram_message(chat_id, msg)
        except Exception as e:
            send_telegram_message(chat_id, f"❌ Escrow error: {e}", parse_mode=None)
            
    elif data.startswith("approve_"):
        task_id = data.replace("approve_", "")
        try:
            res = requests.post(f"{BACKEND_URL}/api/task/approve", json={"task_id": task_id}, timeout=10)
            res_data = res.json()
            if res_data.get("status") == "success":
                tx_id = res_data.get("payout_tx_id", "UPI-SETTLE-SUCCESS")
                msg = f"🎉 *Deliverable Approved & Paid Out!*\\n\\n₹ released directly to worker's UPI ID.\\n• *Transaction ID:* `{tx_id}`\\n\\nThank you for using Sarathi AI!"
                send_telegram_message(chat_id, msg)
        except Exception as e:
            send_telegram_message(chat_id, f"❌ Approval error: {e}", parse_mode=None)
            
    elif data.startswith("reject_proof_"):
        task_id = data.replace("reject_proof_", "")
        try:
            res = requests.post(f"{BACKEND_URL}/api/task/reject_proof", json={"task_id": task_id}, timeout=10)
            if res.json().get("status") == "success":
                send_telegram_message(chat_id, "❌ Proof rejected. The worker has been notified to resubmit.")
        except Exception as e:
            send_telegram_message(chat_id, f"❌ Error: {e}", parse_mode=None)

def main():
    print(">> Sarathi AI Telegram Bot started polling (Stateless Mode)...")
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
'''
with open('telegram_bot.py', 'w', encoding='utf-8') as f:
    f.write(new_bot)
