import os
import requests
import time
from dotenv import load_dotenv
import re

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Use environment variable in production, fallback to localhost for development
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
AWAITING_NEGOTIATION = {}

def send_telegram_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode: payload["parse_mode"] = parse_mode
    if reply_markup: payload["reply_markup"] = reply_markup
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def remove_inline_keyboard(chat_id, message_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageReplyMarkup"
    payload = {"chat_id": chat_id, "message_id": message_id, "reply_markup": {"inline_keyboard": []}}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def handle_user_text(chat_id, user_text):

    if chat_id in AWAITING_NEGOTIATION:
        task_id = AWAITING_NEGOTIATION.pop(chat_id)
        if str(user_text).strip().isdigit():
            offer = int(str(user_text).strip())
            send_telegram_message(chat_id, "🤖 _Consulting the AI Negotiator..._", parse_mode="Markdown")
            try:
                res = requests.post(f"{BACKEND_URL}/api/task/negotiate", json={"task_id": task_id, "offer": offer, "chat_id": chat_id}, timeout=10)
                data = res.json()
                if data.get("status") == "success":
                    ai = data["ai_data"]
                    if ai.get("accepted"):
                        msg = f"🤝 *Offer Accepted!*\n\n{ai.get('message')}\n\n*New Price:* ₹{ai.get('final_quote')}\n\nConfirm below to lock escrow:"
                    else:
                        msg = f"🙅 *Offer Rejected*\n\n{ai.get('message')}\n\n*Minimum Acceptable:* ₹{ai.get('final_quote')}\n\nConfirm below to lock escrow:"
                    
                    keyboard = {"inline_keyboard": [[
                        {"text": f"✅ Approve & Pre-Auth ₹{ai.get('final_quote')}", "callback_data": f"escrow_{task_id}"},
                        {"text": "❌ Final Decline", "callback_data": f"finaldecline_{task_id}"}
                    ]]}
                    send_telegram_message(chat_id, msg, reply_markup=keyboard)
                else:
                    send_telegram_message(chat_id, "❌ Negotiation failed.")
            except: pass
        else:
            send_telegram_message(chat_id, "❌ Cancelled.")
        return
    
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=2)
    except: pass

    try:
        check_res = requests.post(f"{BACKEND_URL}/api/bot/check_user", json={"chat_id": chat_id}, timeout=5).json()
        if check_res.get("status") == "unlinked":
            if re.match(r'^\+?[\d\s\-\(\)]{10,15}$', user_text):
                link_res = requests.post(f"{BACKEND_URL}/api/bot/link", json={"chat_id": chat_id, "phone": user_text}, timeout=5).json()
                if link_res.get("status") == "success":
                    send_telegram_message(chat_id, f"✅ Account Linked! Welcome {user_text}. You can now send tasks.")
                else: send_telegram_message(chat_id, f"❌ {link_res.get('message')}")
            else:
                send_telegram_message(chat_id, "🔒 *Unrecognized User*\n\nPlease reply with your registered phone number (e.g., `+919999999999`) to link your account.")
            return
    except Exception: return

    try:
        reply_res = requests.post(f"{BACKEND_URL}/api/task/reply", json={"telegram_chat_id": chat_id, "text": user_text}, timeout=5)
        if reply_res.json().get("handled"):
            send_telegram_message(chat_id, "✅ Your reply has been sent to the worker.")
            return
    except: pass

    try:
        res = requests.post(f"{BACKEND_URL}/api/triage", json={"query": user_text, "telegram_chat_id": chat_id}, timeout=15)
        data = res.json()
        
        if data.get("status") == "insufficient_funds":
            send_telegram_message(chat_id, f"⚠️ *Insufficient Funds*\n\nThis task requires ₹{data['quote']}, but you only have ₹{data['balance']} in your wallet.\n\nPlease Top-Up here: http://localhost:5000")
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
                f"📋 *Quote Prepared:* 💎 {'Gig Network' if tier == 'gig' else 'Expert Network'}\n\n"
                f"• *Task:* {task['query']}\n"
                f"• *Price:* ₹{task['quote_inr']} (held safely in UPI Escrow)\n"
                f"• *Time Limit:* {task['turnaround_mins']} mins\n"
                f"• *Reasoning:* _{task['ai_reasoning']}_\n\n"
                f"Nothing spends until you say yes. Confirm below to lock escrow:"
            )
            keyboard = {"inline_keyboard": [[
                {"text": f"✅ Approve & Pre-Auth ₹{task['quote_inr']}", "callback_data": f"escrow_{task['id']}"},
                {"text": "❌ Decline", "callback_data": f"decline_{task['id']}"}
            ]]}
            send_telegram_message(chat_id, msg, reply_markup=keyboard)
    except Exception as e:
        send_telegram_message(chat_id, f"❌ Error: {e}", parse_mode=None)


def handle_voice(chat_id, file_id):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=2)
        
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}", timeout=5).json()
        if not file_info.get("ok"): return
        
        file_path = file_info["result"]["file_path"]
        audio_data = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}", timeout=10).content
        
        if not GROQ_API_KEY:
            send_telegram_message(chat_id, "❌ Groq API key is missing.")
            return
            
        send_telegram_message(chat_id, "🎙️ _Listening to your audio..._", parse_mode="Markdown")
            
        res = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            files={"file": ("audio.ogg", audio_data, "audio/ogg")},
            data={"model": "whisper-large-v3-turbo"},
            timeout=15
        )
        
        if res.status_code == 200:
            text = res.json().get("text", "").strip()
            if text:
                send_telegram_message(chat_id, f"📝 *Transcribed:* _{text}_", parse_mode="Markdown")
                handle_user_text(chat_id, text)
            else:
                send_telegram_message(chat_id, "❌ Could not hear speech.")
    except: pass

def handle_callback_query(callback_query):
    data = callback_query.get("data")
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]

    # DOUBLE CLICK PREVENTION: Instantly remove buttons!
    remove_inline_keyboard(chat_id, message_id)

    if data.startswith("escrow_"):
        task_id = data.replace("escrow_", "")
        try:
            res = requests.post(f"{BACKEND_URL}/api/task/escrow", json={"task_id": task_id}, timeout=10)
            if res.json().get("status") == "success":
                msg = f"🔒 *UPI Escrow Locked!*\n\nTask dispatched to Worker Network. They have {res.json().get('turnaround', 30)} mins to complete it once claimed."
                send_telegram_message(chat_id, msg)
        except: pass
            
    elif data.startswith("decline_"):
        task_id = data.replace("decline_", "")
        AWAITING_NEGOTIATION[chat_id] = task_id
        send_telegram_message(chat_id, "📉 You declined the quote. Would you like to negotiate?\n\nReply with your counter-offer amount (in ₹) as a number.")

    elif data.startswith("approve_"):
        task_id = data.replace("approve_", "")
        try:
            res = requests.post(f"{BACKEND_URL}/api/task/approve", json={"task_id": task_id}, timeout=10)
            res_data = res.json()
            if res_data.get("status") == "success":
                tx_id = res_data.get("payout_tx_id", "UPI-SETTLE-SUCCESS")
                msg = f"🎉 *Deliverable Approved & Paid Out!*\n\nReleased directly to worker's UPI ID.\n• *Transaction ID:* `{tx_id}`"
                send_telegram_message(chat_id, msg)
        except: pass
            
    elif data.startswith("finaldecline_"):
        task_id = data.replace("finaldecline_", "")
        send_telegram_message(chat_id, "👋 *Task Cancelled.*\n\nNo worries! No money was charged. Send a new task anytime you need help.", parse_mode="Markdown")

    elif data.startswith("reject_proof_"):
        task_id = data.replace("reject_proof_", "")
        try:
            res = requests.post(f"{BACKEND_URL}/api/task/reject_proof", json={"task_id": task_id}, timeout=10)
            if res.json().get("status") == "success":
                send_telegram_message(chat_id, "❌ Proof rejected. The worker has been notified.")
        except: pass

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
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    if "text" in update["message"]:
                        handle_user_text(chat_id, update["message"]["text"])
                    elif "voice" in update["message"]:
                        handle_voice(chat_id, update["message"]["voice"]["file_id"])
                elif "callback_query" in update:
                    handle_callback_query(update["callback_query"])
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    main()
