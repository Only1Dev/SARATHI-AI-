import os

# 1. Update server.py
with open("server.py", "r", encoding="utf-8") as f:
    server_code = f.read()

# Add imports if not present
if "import stripe" not in server_code:
    server_code = server_code.replace("import requests", "import requests\nimport stripe\nfrom flask import redirect")

# Add Stripe config
if "stripe.api_key =" not in server_code:
    server_code = server_code.replace("SUPABASE_KEY = os.getenv(\"SUPABASE_KEY\", \"\")", "SUPABASE_KEY = os.getenv(\"SUPABASE_KEY\", \"\")\nstripe.api_key = os.getenv(\"STRIPE_SECRET_KEY\")")

# Add Stripe Routes
stripe_routes = """
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
        success_url=f"http://localhost:5000/api/stripe/success?session_id={{CHECKOUT_SESSION_ID}}&phone={phone}&amount={amount}",
        cancel_url="http://localhost:5000/dashboard.html",
    )
    return jsonify({"url": session.url})

@app.route('/api/stripe/success', methods=['GET'])
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
            
    return redirect("/dashboard.html")

"""

if "def create_checkout_session():" not in server_code:
    server_code = server_code.replace("if __name__ == '__main__':", stripe_routes + "\nif __name__ == '__main__':")

with open("server.py", "w", encoding="utf-8") as f:
    f.write(server_code)


# 2. Update dashboard.html
with open("public/dashboard.html", "r", encoding="utf-8") as f:
    dash_code = f.read()

old_add_funds = """    async function addFunds() {
      const amt = prompt("Enter amount to top up (Mock Stripe Topup):", "500");
      if(amt && !isNaN(amt)) {
        await fetch('/api/user/topup', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({phone_number: phone, amount: amt})
        });
        loadDashboard();
      }
    }"""

new_add_funds = """    async function addFunds() {
      const amt = prompt("Enter amount to add via Stripe (INR):", "500");
      if(amt && !isNaN(amt)) {
        const btn = document.querySelector('button[onclick="addFunds()"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = "Redirecting to Stripe...";
        btn.disabled = true;
        
        try {
            const res = await fetch('/api/stripe/create-checkout-session', {
              method: 'POST', headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({phone_number: phone, amount: amt})
            });
            const data = await res.json();
            if(data.url) {
                window.location.href = data.url;
            }
        } catch (e) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
      }
    }"""

if "Mock Stripe Topup" in dash_code:
    dash_code = dash_code.replace(old_add_funds, new_add_funds)

with open("public/dashboard.html", "w", encoding="utf-8") as f:
    f.write(dash_code)
