import os

SHARED_CSS = """
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    :root {
      --brand-accent: #10b981;
      --bg-dark: #0f172a;
      --card-bg: linear-gradient(145deg, #1e293b, #0f172a);
    }
    * { box-sizing: border-box; }
    body {
      background: var(--bg-dark);
      color: #f8fafc;
      font-family: 'Inter', sans-serif;
      margin: 0; min-height: 100vh;
    }
    .navbar {
      display: flex; justify-content: space-between; align-items: center; 
      padding: 1rem 5%;
      background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(255,255,255,0.05);
      position: sticky; top: 0; z-index: 100;
    }
    .logo { font-size: 1.4rem; font-weight: 700; display: flex; align-items: center; gap: 12px; letter-spacing: -0.5px; }
    .logo-icon { background: var(--brand-accent); width: 34px; height: 34px; border-radius: 10px; display:flex; align-items:center; justify-content:center; color:white; box-shadow: 0 0 15px rgba(16,185,129,0.4); }
    
    .nav-links { display: flex; gap: 2rem; align-items: center; }
    .nav-links a { color: #94a3b8; text-decoration: none; font-weight: 500; font-size:1rem; transition: color 0.2s; }
    .nav-links a:hover { color: white; }
    
    .modern-card {
      background: var(--card-bg);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 24px;
      padding: 2.5rem;
      box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
      position: relative;
      overflow: hidden;
    }
    .modern-card::before {
      content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
      background: linear-gradient(90deg, transparent, var(--brand-accent), transparent);
      opacity: 0.3;
    }
    
    .btn-glow {
      background: linear-gradient(135deg, var(--brand-accent), #059669);
      color: white; border: none; padding: 1rem 1.5rem; border-radius: 12px;
      font-weight: 600; cursor: pointer; transition: all 0.2s;
      box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
      font-family: 'Inter', sans-serif;
      display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    }
    .btn-glow:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.5); }
    
    .btn-outline {
      background: transparent; border: 1px solid rgba(255,255,255,0.2); color: white;
      padding: 0.6rem 1.2rem; border-radius: 8px; font-weight: 500; cursor: pointer; transition: all 0.2s;
    }
    .btn-outline:hover { background: rgba(255,255,255,0.05); border-color: white; }

    .modern-input { width: 100%; padding: 1rem; border-radius: 12px; border: 1px solid #334155; background: rgba(15, 23, 42, 0.6); color: white; font-size: 1.1rem; text-align: center; margin-bottom: 1.5rem; }
    .modern-input:focus { outline: none; border-color: var(--brand-accent); box-shadow: 0 0 15px rgba(16, 185, 129, 0.2); }
    
    .list-item {
      background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.03);
      padding: 1.5rem; border-radius: 16px; margin-bottom: 1rem;
      transition: all 0.3s ease;
    }
    .list-item:hover { border-color: rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.03); transform: translateX(5px); }
    
    .badge { padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
    .badge-pending { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-success { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-primary { background: rgba(59, 130, 246, 0.1); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }

    /* Fix for index modal */
    .modal-overlay {
      display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(10px); z-index: 1000;
      justify-content: center; align-items: center;
    }
    .modal-overlay.active { display: flex; }
  </style>
"""

NAV_HTML = """
  <nav class="navbar">
    <a href="/" style="text-decoration:none; color:inherit;" class="logo">
      <div class="logo-icon">{icon}</div>
      {title}
    </a>
    <div class="nav-links">
      {links}
    </div>
  </nav>
"""

# 1. INDEX.HTML
INDEX = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sarathi AI - Escrow Network</title>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
  <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script>
  {SHARED_CSS}
</head>
<body>
  {NAV_HTML.format(icon="⚡", title="Sarathi AI", links='<a href="/worker.html">Worker Portal</a><button class="btn-glow" style="padding: 0.6rem 1.2rem; border-radius:8px;" onclick="openLoginModal()">Login / Sign Up</button>')}
  
  <main style="max-width: 800px; margin: 4rem auto; text-align: center; padding: 0 1rem;">
    <div style="display:inline-block; padding: 0.5rem 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--brand-accent); border-radius: 30px; color: var(--brand-accent); margin-bottom: 1.5rem; font-weight: 600;">
      Now Live for SIH 2026
    </div>
    <h1 style="font-size: 4rem; margin-bottom: 1.5rem; line-height: 1.1;">
      Get anything done.<br>Pay only when it's <span style="color: var(--brand-accent);">perfect.</span>
    </h1>
    <p style="font-size: 1.25rem; color: #94a3b8; margin-bottom: 2.5rem; line-height: 1.6;">
      The AI-powered gig network for India. Send a text on Telegram, get an instant quote, and your money is held safely in UPI Escrow until the job is done.
    </p>
    
    <div style="display: flex; gap: 1rem; justify-content: center;">
      <button class="btn-glow" style="width: auto; padding: 1rem 2.5rem; font-size: 1.1rem;" onclick="openLoginModal()">
        Open Escrow Wallet
      </button>
      <a href="https://t.me/SarathiAI_SIH_bot" target="_blank" class="btn-outline" style="text-decoration:none; padding:1rem 2rem; font-size:1.1rem; border-radius:12px; display:flex; align-items:center; gap:8px;">
        <i data-lucide="send" style="width: 18px;"></i> Message Telegram Bot
      </a>
    </div>
  </main>

  <div id="login-modal" class="modal-overlay">
    <div class="modern-card" style="width: 90%; max-width: 420px; text-align: center;">
      <button onclick="closeLoginModal()" style="position:absolute; top:1rem; right:1rem; background:none; border:none; color:#94a3b8; cursor:pointer;"><i data-lucide="x"></i></button>
      <div style="width:50px; height:50px; background:var(--brand-accent); border-radius:12px; display:flex; align-items:center; justify-content:center; margin:0 auto 1.5rem; box-shadow:0 0 20px rgba(16,185,129,0.4);"><i data-lucide="shield-check" style="color:white; width:28px;"></i></div>
      <h3 style="margin-bottom:0.5rem; font-size:1.6rem;">Secure Login</h3>
      <p style="color:#94a3b8; margin-bottom:2rem;">Enter your phone number to access your Escrow Wallet.</p>
      
      <div id="step-phone">
        <input type="tel" class="modern-input" id="phone-input" placeholder="+91 9999999999">
        <div id="recaptcha-container" style="margin-bottom: 1.5rem; display: flex; justify-content: center;"></div>
        <button class="btn-glow" id="send-otp-btn" style="width:100%;" onclick="sendOTP()">Send Secure OTP</button>
      </div>

      <div id="step-otp" style="display: none;">
        <input type="text" class="modern-input" id="otp-input" placeholder="123456" maxlength="6">
        <button class="btn-glow" id="verify-otp-btn" style="width:100%;" onclick="verifyOTP()">Verify & Access Wallet</button>
        <p style="margin-top: 1rem; color: #94a3b8; font-size: 0.85rem; cursor: pointer;" onclick="resetLogin()">← Back to phone number</p>
      </div>
    </div>
  </div>

  <script>
    lucide.createIcons();
    const firebaseConfig = {{ apiKey: "AIzaSyA2lrC0hSXSh8QdP9qVvQa0Mg7nCy_HA-8", authDomain: "sarathi-ai-33e65.firebaseapp.com", projectId: "sarathi-ai-33e65" }};
    if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();
    let confirmationResult = null;

    window.onload = () => {{
        if(!window.recaptchaVerifier) {{
            window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {{'size': 'normal'}});
            window.recaptchaVerifier.render();
        }}
    }};

    function openLoginModal() {{ document.getElementById('login-modal').classList.add('active'); }}
    function closeLoginModal() {{ document.getElementById('login-modal').classList.remove('active'); resetLogin(); }}
    function resetLogin() {{ document.getElementById('step-phone').style.display = 'block'; document.getElementById('step-otp').style.display = 'none'; document.getElementById('otp-input').value = ''; }}

    async function sendOTP() {{
      const phoneNumber = document.getElementById('phone-input').value.replace(/\s+/g, '').trim(); 
      const btn = document.getElementById('send-otp-btn');
      if(!phoneNumber.startsWith('+')) return alert("Please include country code, e.g. +91");
      btn.innerText = "Sending..."; btn.disabled = true;
      try {{
        confirmationResult = await auth.signInWithPhoneNumber(phoneNumber, window.recaptchaVerifier);
        document.getElementById('step-phone').style.display = 'none';
        document.getElementById('step-otp').style.display = 'block';
      }} catch (error) {{ alert("Firebase Error: " + error.message); window.recaptchaVerifier.render(); }}
      btn.innerText = "Send Secure OTP"; btn.disabled = false;
    }}

    async function verifyOTP() {{
      const otp = document.getElementById('otp-input').value.trim();
      const btn = document.getElementById('verify-otp-btn');
      btn.innerText = "Verifying..."; btn.disabled = true;
      try {{
        const result = await confirmationResult.confirm(otp);
        await syncUserAndRedirect(result.user.phoneNumber);
      }} catch (error) {{ alert("Invalid OTP"); btn.innerText = "Verify & Access Wallet"; btn.disabled = false; }}
    }}

    async function syncUserAndRedirect(phoneNumber) {{
      try {{
        const res = await fetch('/api/auth/login', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ phone_number: phoneNumber }}) }});
        const data = await res.json();
        if (data.status === 'success') {{
          localStorage.setItem('user_id', data.user.id);
          localStorage.setItem('phone_number', data.user.phone_number);
          window.location.href = data.is_admin ? '/admin.html' : '/dashboard.html';
        }}
      }} catch (err) {{ console.error(err); }}
    }}
  </script>
</body>
</html>"""

# 2. DASHBOARD.HTML
DASHBOARD = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sarathi AI - Escrow Wallet</title>
  <script src="https://unpkg.com/lucide@latest"></script>
  {SHARED_CSS}
</head>
<body>
  {NAV_HTML.format(icon="⚡", title="Sarathi AI Escrow", links='<button class="btn-outline" onclick="localStorage.clear(); window.location.href=\'/\'">Sign Out</button>')}
  
  <main style="max-width: 1200px; margin: 3rem auto; padding: 0 2rem; display: grid; grid-template-columns: 1fr 2fr; gap: 3rem;">
    <!-- Wallet Card -->
    <div class="modern-card" style="height: fit-content;">
      <h3 style="margin-bottom: 2rem; font-size: 1.3rem; display: flex; align-items: center; gap: 10px;"><i data-lucide="wallet" style="color: var(--brand-accent);"></i> Your Wallet</h3>
      <div style="margin-bottom: 2.5rem;">
        <div style="font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Available Balance</div>
        <div style="font-size: 3.5rem; font-weight: 700; color: white; line-height: 1;">₹<span id="wallet-balance">0</span></div>
      </div>
      <div style="background: rgba(0,0,0,0.3); padding: 1.2rem; border-radius: 12px; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; align-items: center; gap: 0.8rem;"><i data-lucide="lock" style="color: #f59e0b; width: 18px;"></i><span style="font-size: 0.95rem; color: #94a3b8;">In Escrow</span></div>
        <div style="font-weight: 600; font-size: 1.1rem; color: #f59e0b;">₹<span id="escrow-balance">0</span></div>
      </div>
      <button class="btn-glow" style="width: 100%;" onclick="addFunds()"><i data-lucide="plus" style="width: 20px;"></i> Add Funds via Stripe</button>
    </div>

    <!-- Tasks Card -->
    <div class="modern-card">
      <h3 style="margin-bottom: 1.5rem; font-size: 1.3rem; display: flex; align-items: center; gap: 10px;"><i data-lucide="layout-list" style="color: var(--brand-accent);"></i> Active Escrow Tasks</h3>
      <div id="tasks-list" style="margin-top: 1rem;"><div style="text-align: center; padding: 4rem 0; color: #94a3b8;">Loading...</div></div>
    </div>
  </main>

  <script>
    lucide.createIcons();
    const phone = localStorage.getItem("phone_number");
    if(!phone) window.location.href = '/';

    async function loadDashboard() {{
      const res = await fetch('/api/user/dashboard', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{phone_number: phone}}) }});
      const data = await res.json();
      if(data.status === 'success') {{
        document.getElementById('wallet-balance').innerText = data.user.wallet_balance_inr || "0";
        document.getElementById('escrow-balance').innerText = data.escrow_held || "0";
        const tasksList = document.getElementById('tasks-list');
        if(data.tasks.length === 0) {{
          tasksList.innerHTML = `<div style="text-align:center; padding:4rem 0; color:#64748b;"><p>No tasks yet. Message the Telegram bot to start!</p></div>`;
        }} else {{
          tasksList.innerHTML = data.tasks.map(t => {{
            let badgeClass = 'badge-pending';
            if (t.status === 'APPROVED_PAID_OUT') badgeClass = 'badge-success';
            if (t.status === 'CLAIMED' || t.status === 'DELIVERED') badgeClass = 'badge-primary';
            return `<div class="list-item"><div style="display:flex; justify-content:space-between; margin-bottom:0.8rem;"><strong style="font-size:1.1rem; color:white;">${{t.query}}</strong><span class="badge ${{badgeClass}}">${{t.status.replace(/_/g, ' ')}}</span></div><div style="display:flex; gap:1.5rem; font-size:0.9rem; color:#94a3b8;"><span>₹${{t.quote_inr}} Held</span><span>Worker: ${{t.workers ? t.workers.name : 'Awaiting...'}}</span></div></div>`
          }}).join('');
        }}
      }}
    }}

    async function addFunds() {{
      const amt = prompt("Enter amount to add via Stripe (INR):", "500");
      if(amt && !isNaN(amt)) {{
        const btn = document.querySelector('button[onclick="addFunds()"]');
        const originalText = btn.innerHTML; btn.innerHTML = "Redirecting..."; btn.disabled = true;
        try {{
            const res = await fetch('/api/stripe/create-checkout-session', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{phone_number: phone, amount: amt}}) }});
            const data = await res.json();
            if(data.url) window.location.href = data.url;
        }} catch (e) {{ btn.innerHTML = originalText; btn.disabled = false; }}
      }}
    }}
    loadDashboard();
  </script>
</body>
</html>"""

# 3. ADMIN.HTML
ADMIN = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sarathi AI - Admin</title>
  <script src="https://unpkg.com/lucide@latest"></script>
  {SHARED_CSS.replace('--brand-accent: #10b981;', '--brand-accent: #3b82f6;')}
</head>
<body>
  {NAV_HTML.format(icon="⚡", title="Sarathi AI Admin", links='<button class="btn-outline" onclick="localStorage.clear(); window.location.href=\'/\'">Sign Out</button>')}
  <main style="max-width: 1200px; margin: 3rem auto; padding: 0 2rem;">
    <div class="modern-card" style="margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; padding: 2rem 3rem;">
      <div><h2 style="font-size: 2rem; margin: 0;">Command Center</h2></div>
      <div style="text-align: right;"><div style="font-size: 0.85rem; color: #94a3b8; text-transform: uppercase;">Platform Volume</div><div style="font-size: 3rem; font-weight: 700; color: #3b82f6; line-height: 1;">₹<span id="total-volume">0</span></div></div>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 2rem;">
      <div class="modern-card"><h3>Worker Directory</h3><div id="workers-list"></div></div>
      <div class="modern-card"><h3>Global Ledger</h3><div id="tasks-list"></div></div>
    </div>
  </main>
  <script>
    const phone = localStorage.getItem("phone_number");
    if(!phone) window.location.href = '/';
    async function loadAdmin() {{
      const res = await fetch('/api/admin/dashboard', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{phone_number: phone}}) }});
      const data = await res.json();
      if(data.status === 'success') {{
        document.getElementById('total-volume').innerText = data.platform_volume || "0";
        document.getElementById('workers-list').innerHTML = data.workers.map(w => `<div class="list-item"><div style="display:flex; justify-content:space-between; margin-bottom: 0.5rem;"><strong style="color:white; font-size:1.1rem;">${{w.name}}</strong><span class="badge ${{w.status === 'APPROVED' ? 'badge-success' : 'badge-pending'}}">${{w.status}}</span></div><div style="font-size:0.85rem; color:#94a3b8; margin-bottom: 1rem;">${{w.phone_number}} | ${{w.upi_id}}</div>${{w.status === 'PENDING' ? `<button class="btn-glow" onclick="approveWorker('${{w.id}}')" style="width:100%;">Approve Worker</button>` : ''}}</div>`).join('');
        document.getElementById('tasks-list').innerHTML = data.tasks.map(t => `<div class="list-item" style="display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:500;">${{t.query}}</div><div style="font-size:0.8rem; color:#94a3b8;">Status: ${{t.status}}</div></div><div style="font-weight:700; color:var(--brand-accent); font-size:1.2rem;">₹${{t.quote_inr}}</div></div>`).join('');
      }}
    }}
    async function approveWorker(id) {{ await fetch('/api/admin/approve_worker', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{phone_number: phone, worker_id: id}}) }}); loadAdmin(); }}
    loadAdmin();
  </script>
</body>
</html>"""

# 4. WORKER.HTML
WORKER = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sarathi AI - Worker Portal</title>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
  <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script>
  {SHARED_CSS.replace('--brand-accent: #10b981;', '--brand-accent: #a855f7;')}
</head>
<body>
  {NAV_HTML.format(icon="⚡", title="Worker Portal", links='<button class="btn-outline" onclick="localStorage.removeItem(\'worker_phone\'); window.location.reload();" id="logout-btn" style="display:none;">Sign Out</button>')}
  
  <main style="max-width: 800px; margin: 3rem auto; padding: 0 2rem;">
    <!-- Auth Box -->
    <div id="auth-box" class="modern-card" style="max-width:420px; margin: 0 auto; text-align:center;">
      <h3 style="margin-bottom: 2rem; font-size: 1.6rem;">Worker Login</h3>
      <div id="step-phone">
        <input type="tel" class="modern-input" id="phone-input" placeholder="+91 9999999999">
        <div id="recaptcha-container" style="margin-bottom:1.5rem; display:flex; justify-content:center;"></div>
        <button class="btn-glow" id="send-otp-btn" style="width:100%;" onclick="sendOTP()">Send OTP</button>
      </div>
      <div id="step-otp" style="display:none;">
        <input type="text" class="modern-input" id="otp-input" placeholder="123456" maxlength="6">
        <button class="btn-glow" id="verify-otp-btn" style="width:100%;" onclick="verifyOTP()">Verify</button>
      </div>
      <div id="step-register" style="display:none;">
        <h4 style="margin-bottom: 1.5rem;">Complete Profile</h4>
        <input type="text" class="modern-input" id="reg-name" placeholder="Full Name">
        <input type="text" class="modern-input" id="reg-city" placeholder="City">
        <input type="text" class="modern-input" id="reg-upi" placeholder="UPI ID (e.g. shivam@upi)">
        <button class="btn-glow" style="width:100%;" onclick="completeRegistration()">Register</button>
      </div>
    </div>

    <!-- Dashboard Box -->
    <div id="dashboard-box" style="display:none;">
      <div class="modern-card" style="margin-bottom: 2rem; display:flex; justify-content:space-between; align-items:center; padding: 2rem;">
        <div>
          <h3 style="margin-bottom:0.5rem; font-size: 1.8rem;">Welcome, <span id="worker-name"></span></h3>
          <p style="color:#94a3b8; margin:0;">Status: <strong id="worker-status" style="color:white;"></strong></p>
        </div>
        <div style="text-align:right;">
          <p style="font-size:0.85rem; color:#94a3b8; margin:0 0 0.5rem 0; text-transform:uppercase;">Total Earnings</p>
          <p style="font-size:2.5rem; font-weight:700; color:var(--brand-accent); margin:0;">₹<span id="worker-earnings">0</span></p>
        </div>
      </div>
      
      <div id="pending-notice" style="display:none; background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3); color:#f59e0b; padding:1.5rem; border-radius:12px; margin-bottom:2rem; font-weight:500;">
        Your account is pending admin approval. You cannot see tasks yet.
      </div>

      <div id="task-feed-container" style="display:none;" class="modern-card">
        <h3 style="margin-bottom:1.5rem;">Available Tasks</h3>
        <div id="task-feed">Loading...</div>
      </div>
    </div>
  </main>

  <script>
    lucide.createIcons();
    const firebaseConfig = {{ apiKey: "AIzaSyA2lrC0hSXSh8QdP9qVvQa0Mg7nCy_HA-8", authDomain: "sarathi-ai-33e65.firebaseapp.com", projectId: "sarathi-ai-33e65" }};
    if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();
    let confirmationResult = null, verifiedPhone = "";

    window.onload = () => {{
      const storedPhone = localStorage.getItem("worker_phone");
      if(storedPhone) {{ verifiedPhone = storedPhone; document.getElementById("auth-box").style.display = "none"; document.getElementById("logout-btn").style.display = "block"; loginWorker(storedPhone); }}
      else {{ window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {{'size': 'normal'}}); window.recaptchaVerifier.render(); }}
    }};

    async function sendOTP() {{
      verifiedPhone = document.getElementById('phone-input').value.replace(/\s+/g, '').trim();
      try {{ confirmationResult = await auth.signInWithPhoneNumber(verifiedPhone, window.recaptchaVerifier); document.getElementById('step-phone').style.display = 'none'; document.getElementById('step-otp').style.display = 'block'; }} 
      catch (e) {{ alert("Error: " + e.message); window.recaptchaVerifier.render(); }}
    }}

    async function verifyOTP() {{ try {{ await confirmationResult.confirm(document.getElementById('otp-input').value.trim()); loginWorker(verifiedPhone); }} catch (e) {{ alert("Invalid OTP"); }} }}

    async function loginWorker(phone) {{
      const res = await fetch('/api/worker/auth', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{phone_number: phone}}) }});
      const data = await res.json();
      if(data.status === 'needs_registration') {{ document.getElementById('step-otp').style.display = 'none'; document.getElementById('step-phone').style.display = 'none'; document.getElementById('step-register').style.display = 'block'; }}
      else if (data.status === 'success') {{
        localStorage.setItem("worker_phone", phone); localStorage.setItem("worker_id", data.worker.id);
        document.getElementById("auth-box").style.display = "none"; document.getElementById("dashboard-box").style.display = "block"; document.getElementById("logout-btn").style.display = "block";
        document.getElementById("worker-name").innerText = data.worker.name; document.getElementById("worker-status").innerText = data.worker.status; document.getElementById("worker-earnings").innerText = data.worker.balance_inr || "0";
        if(data.worker.status === 'PENDING') document.getElementById("pending-notice").style.display = "block";
        else if (data.worker.status === 'APPROVED') {{ document.getElementById("task-feed-container").style.display = "block"; loadFeed(); }}
      }}
    }}

    async function completeRegistration() {{
      await fetch('/api/worker/auth', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{phone_number: verifiedPhone, name: document.getElementById('reg-name').value, city: document.getElementById('reg-city').value, upi_id: document.getElementById('reg-upi').value}}) }});
      loginWorker(verifiedPhone);
    }}

    async function loadFeed() {{
      const data = await (await fetch('/api/worker/feed')).json();
      document.getElementById('task-feed').innerHTML = data.tasks.length ? data.tasks.map(t => `<div class="list-item"><h4 style="margin:0 0 0.5rem 0; font-size:1.1rem;">${{t.query}}</h4><div style="font-size:0.9rem; color:#94a3b8; margin-bottom:1rem;">Reward: ₹${{t.quote_inr}} | Status: ${{t.status}}</div>${{t.status === 'ESCROW_LOCKED' ? `<button class="btn-glow" style="padding:0.6rem; width:100%; font-size:0.9rem;" onclick="claimTask('${{t.id}}')">Claim Task</button>` : ''}}${{t.status === 'CLAIMED' && t.worker_id === localStorage.getItem("worker_id") ? `<textarea id="proof-${{t.id}}" class="modern-input" style="text-align:left;" placeholder="Type proof..."></textarea><button class="btn-glow" style="width:100%; padding:0.6rem; font-size:0.9rem;" onclick="submitProof('${{t.id}}')">Submit Proof</button>` : ''}}</div>`).join('') : "<p style='color:#64748b;'>No tasks available.</p>";
    }}

    async function claimTask(id) {{ await fetch('/api/worker/claim', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{task_id: id, worker_id: localStorage.getItem("worker_id")}}) }}); loadFeed(); }}
    async function submitProof(id) {{ await fetch('/api/worker/submit', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{task_id: id, proof_text: document.getElementById(`proof-${{id}}`).value, proof_type: "Manual"}}) }}); alert("Proof submitted!"); loadFeed(); }}
  </script>
</body>
</html>"""

with open("public/index.html", "w", encoding="utf-8") as f: f.write(INDEX)
with open("public/dashboard.html", "w", encoding="utf-8") as f: f.write(DASHBOARD)
with open("public/admin.html", "w", encoding="utf-8") as f: f.write(ADMIN)
with open("public/worker.html", "w", encoding="utf-8") as f: f.write(WORKER)
