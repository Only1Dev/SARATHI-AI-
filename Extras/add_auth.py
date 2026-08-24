with open("server.py", "r", encoding="utf-8") as f:
    text = f.read()

auth_code = '''
@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    phone = request.json.get("phone_number")
    if not phone:
        return jsonify({"status": "error", "message": "Missing phone"}), 400
        
    u_res = supabase.table("users").select("*").eq("phone_number", phone).execute()
    if u_res.data:
        user = u_res.data[0]
    else:
        # Create new user
        u_res = supabase.table("users").insert({"phone_number": phone}).execute()
        user = u_res.data[0]
        
    is_admin = (phone == os.getenv("ADMIN_PHONE", "+917015960679"))
    return jsonify({"status": "success", "user": user, "is_admin": is_admin})

@app.route('/api/triage', methods=['POST'])
'''

text = text.replace("@app.route('/api/triage', methods=['POST'])", auth_code)

with open("server.py", "w", encoding="utf-8") as f:
    f.write(text)
