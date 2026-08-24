with open("server.py", "r", encoding="utf-8") as f:
    code = f.read()

old_func = """@app.route('/api/stripe/success', methods=['GET'])
def stripe_success():
    session_id = request.args.get('session_id')
    phone = request.args.get('phone')
    amount = float(request.args.get('amount'))
    
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status == 'paid':
        existing = supabase.table("transactions").select("*").eq("stripe_payment_id", session_id).execute()
        if not existing.data:
            user = supabase.table("users").select("*").eq("phone_number", phone).execute().data[0]
            new_bal = float(user.get("wallet_balance_inr", 0)) + amount
            supabase.table("users").update({"wallet_balance_inr": new_bal}).eq("id", user["id"]).execute()
            supabase.table("transactions").insert({
                "user_id": user["id"], "type": "TOP_UP", "amount_inr": amount, "stripe_payment_id": session_id
            }).execute()
            
    return redirect("/dashboard.html")"""

new_func = """@app.route('/api/stripe/success', methods=['GET'])
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
            
    return redirect("/dashboard.html")"""

if old_func in code:
    code = code.replace(old_func, new_func)

with open("server.py", "w", encoding="utf-8") as f:
    f.write(code)
