import os

PREMIUM_CSS = """
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
      padding: 1.2rem 5%;
      background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(255,255,255,0.05);
      position: sticky; top: 0; z-index: 100;
    }
    .logo { font-size: 1.4rem; font-weight: 700; display: flex; align-items: center; gap: 12px; letter-spacing: -0.5px; }
    .logo-icon { background: var(--brand-accent); width: 34px; height: 34px; border-radius: 10px; display:flex; align-items:center; justify-content:center; color:white; box-shadow: 0 0 15px rgba(16,185,129,0.4); }
    .nav-links { display: flex; gap: 2rem; align-items: center; }
    .nav-links a, .nav-links button { color: #94a3b8; text-decoration: none; font-weight: 500; cursor:pointer; background:none; border:none; font-size:1rem; transition: color 0.2s; font-family: 'Inter', sans-serif;}
    .nav-links a:hover, .nav-links button:hover { color: white; }
    
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
    
    .badge { padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
    .badge-pending { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-success { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-primary { background: rgba(59, 130, 246, 0.1); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }
    
    .list-item {
      background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.03);
      padding: 1.5rem; border-radius: 16px; margin-bottom: 1rem;
      transition: all 0.3s ease;
    }
    .list-item:hover { border-color: rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.03); transform: translateX(5px); }
    
    .text-muted { color: #94a3b8; }
    .text-highlight { color: white; font-weight: 600; }
    h2, h3, h4 { margin-top: 0; }
  </style>
"""

# --- DASHBOARD HTML ---
DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sarathi AI - Escrow Wallet</title>
  <script src="https://unpkg.com/lucide@latest"></script>
  {PREMIUM_CSS}
</head>
<body>
  <nav class="navbar">
    <div class="logo">
      <div class="logo-icon">⚡</div>
      Sarathi AI Escrow
    </div>
    <div class="nav-links">
      <a href="/worker.html">Worker Portal</a>
      <button onclick="localStorage.clear(); window.location.href='/'">Sign Out</button>
    </div>
  </nav>

  <main style="max-width: 1200px; margin: 3rem auto; padding: 0 2rem; display: grid; grid-template-columns: 1fr 2fr; gap: 3rem;">
    
    <!-- Wallet Card -->
    <div class="modern-card" style="height: fit-content;">
      <h3 style="margin-bottom: 2rem; font-size: 1.3rem; display: flex; align-items: center; gap: 10px;">
        <i data-lucide="wallet" style="color: var(--brand-accent);"></i> Your Wallet
      </h3>
      
      <div style="margin-bottom: 2.5rem;">
        <div style="font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Available Balance</div>
        <div style="font-size: 3.5rem; font-weight: 700; color: white; line-height: 1;">₹<span id="wallet-balance">0</span></div>
      </div>
      
      <div style="background: rgba(0,0,0,0.3); padding: 1.2rem; border-radius: 12px; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <i data-lucide="lock" style="color: #f59e0b; width: 18px;"></i>
          <span style="font-size: 0.95rem; color: #94a3b8;">In Escrow</span>
        </div>
        <div style="font-weight: 600; font-size: 1.1rem; color: #f59e0b;">₹<span id="escrow-balance">0</span></div>
      </div>
      
      <button class="btn-glow" style="width: 100%;" onclick="addFunds()">
        <i data-lucide="plus" style="width: 20px;"></i> Add Funds via Stripe
      </button>
    </div>

    <!-- Tasks Card -->
    <div class="modern-card">
      <h3 style="margin-bottom: 1.5rem; font-size: 1.3rem; display: flex; align-items: center; gap: 10px;">
        <i data-lucide="layout-list" style="color: var(--brand-accent);"></i> Active Escrow Tasks
      </h3>
      
      <div id="tasks-list" style="margin-top: 1rem;">
        <div style="text-align: center; padding: 4rem 0; color: #94a3b8;">
          <i data-lucide="loader" style="width: 40px; height: 40px; animation: spin 2s linear infinite; opacity: 0.5; margin-bottom: 1rem;"></i>
          <p>Syncing ledger...</p>
        </div>
      </div>
    </div>
  </main>

  <script>
    lucide.createIcons();
    const phone = localStorage.getItem("phone_number");
    if(!phone) window.location.href = '/';

    async function loadDashboard() {{
      const res = await fetch('/api/user/dashboard', {{
        method: 'POST', headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{phone_number: phone}})
      }});
      const data = await res.json();
      if(data.status === 'success') {{
        document.getElementById('wallet-balance').innerText = data.user.wallet_balance_inr || "0";
        document.getElementById('escrow-balance').innerText = data.escrow_held || "0";
        
        const tasksList = document.getElementById('tasks-list');
        if(data.tasks.length === 0) {{
          tasksList.innerHTML = `<div style="text-align:center; padding:4rem 0; color:#64748b;"><i data-lucide="inbox" style="width:48px;height:48px;opacity:0.3;margin-bottom:1rem;"></i><p>No tasks yet. Message the Telegram bot to start!</p></div>`;
          lucide.createIcons();
        }} else {{
          tasksList.innerHTML = data.tasks.map(t => {{
            let badgeClass = 'badge-pending';
            if (t.status === 'APPROVED_PAID_OUT') badgeClass = 'badge-success';
            if (t.status === 'CLAIMED' || t.status === 'DELIVERED') badgeClass = 'badge-primary';
            
            return `
            <div class="list-item">
              <div style="display:flex; justify-content:space-between; margin-bottom:0.8rem; align-items: flex-start;">
                <strong style="font-size: 1.1rem; color: white; line-height: 1.4;">${{t.query}}</strong>
                <span class="badge ${{badgeClass}}">${{t.status.replace(/_/g, ' ')}}</span>
              </div>
              <div style="display:flex; gap: 1.5rem; font-size:0.9rem; color:#94a3b8;">
                <span style="display:flex; align-items:center; gap:5px;"><i data-lucide="indian-rupee" style="width:14px;"></i> ${{t.quote_inr}} Held</span>
                <span style="display:flex; align-items:center; gap:5px;"><i data-lucide="user" style="width:14px;"></i> ${{t.workers ? t.workers.name : 'Awaiting claim...'}}</span>
              </div>
            </div>
          `}}).join('');
          lucide.createIcons();
        }}
      }}
    }}

    async function addFunds() {{
      const amt = prompt("Enter amount to add via Stripe (INR):", "500");
      if(amt && !isNaN(amt)) {{
        const btn = document.querySelector('button[onclick="addFunds()"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = "Redirecting..."; btn.disabled = true;
        try {{
            const res = await fetch('/api/stripe/create-checkout-session', {{
              method: 'POST', headers: {{'Content-Type': 'application/json'}},
              body: JSON.stringify({{phone_number: phone, amount: amt}})
            }});
            const data = await res.json();
            if(data.url) window.location.href = data.url;
        }} catch (e) {{ btn.innerHTML = originalText; btn.disabled = false; }}
      }}
    }}
    loadDashboard();
  </script>
</body>
</html>"""


# --- ADMIN HTML ---
ADMIN_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sarathi AI - Master Admin</title>
  <script src="https://unpkg.com/lucide@latest"></script>
  {PREMIUM_CSS}
</head>
<body>
  <nav class="navbar">
    <div class="logo">
      <div class="logo-icon" style="background: #3b82f6;">⚡</div>
      Sarathi AI Master Admin
    </div>
    <div class="nav-links">
      <a href="/dashboard.html">My Wallet</a>
      <button onclick="localStorage.clear(); window.location.href='/'">Sign Out</button>
    </div>
  </nav>

  <main style="max-width: 1200px; margin: 3rem auto; padding: 0 2rem;">
    <!-- Top Stats -->
    <div class="modern-card" style="margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; padding: 2rem 3rem;">
      <div>
        <h2 style="font-size: 2rem; margin: 0;">Command Center</h2>
        <p style="color: #94a3b8; margin: 0.5rem 0 0 0;">Manage platform workers and view global ledger.</p>
      </div>
      <div style="text-align: right;">
        <div style="font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Platform Volume</div>
        <div style="font-size: 3rem; font-weight: 700; color: #3b82f6; line-height: 1;">₹<span id="total-volume">0</span></div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 2rem;">
      <!-- Workers -->
      <div class="modern-card">
        <h3 style="margin-bottom: 1.5rem; display: flex; align-items: center; gap: 10px;">
          <i data-lucide="users" style="color: #3b82f6;"></i> Worker Directory
        </h3>
        <div id="workers-list">Loading...</div>
      </div>
      
      <!-- Tasks -->
      <div class="modern-card">
        <h3 style="margin-bottom: 1.5rem; display: flex; align-items: center; gap: 10px;">
          <i data-lucide="activity" style="color: #3b82f6;"></i> Global Ledger
        </h3>
        <div id="tasks-list">Loading...</div>
      </div>
    </div>
  </main>

  <script>
    lucide.createIcons();
    const phone = localStorage.getItem("phone_number");
    if(!phone) window.location.href = '/';

    async function loadAdmin() {{
      const res = await fetch('/api/admin/dashboard', {{
        method: 'POST', headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{phone_number: phone}})
      }});
      const data = await res.json();
      if(data.status === 'success') {{
        document.getElementById('total-volume').innerText = data.platform_volume || "0";
        
        document.getElementById('workers-list').innerHTML = data.workers.map(w => `
          <div class="list-item">
            <div style="display:flex; justify-content:space-between; margin-bottom: 0.5rem;">
              <strong style="color:white; font-size:1.1rem;">${{w.name}} <span style="color:#64748b; font-weight:400;">(${{w.city}})</span></strong> 
              <span class="badge ${{w.status === 'APPROVED' ? 'badge-success' : 'badge-pending'}}">${{w.status}}</span>
            </div>
            <div style="font-size:0.85rem; color:#94a3b8; margin-bottom: 1rem;">📱 ${{w.phone_number}} &nbsp;|&nbsp; 🏦 ${{w.upi_id}}</div>
            ${{w.status === 'PENDING' ? `<button class="btn-glow" onclick="approveWorker('${{w.id}}')" style="width:100%; padding:0.6rem; font-size:0.9rem;">Approve Worker</button>` : ''}}
          </div>
        `).join('') || "<div style='color:#64748b;'>No workers.</div>";

        document.getElementById('tasks-list').innerHTML = data.tasks.map(t => `
          <div class="list-item" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="color:white; font-weight:500; margin-bottom:0.4rem;">${{t.query}}</div>
              <div style="font-size:0.8rem; color:#94a3b8;">Status: <span style="color:#cbd5e1;">${{t.status}}</span> &nbsp;|&nbsp; User: ${{t.users.phone_number}}</div>
            </div>
            <div style="font-weight:700; color:var(--brand-accent); font-size:1.2rem;">₹${{t.quote_inr}}</div>
          </div>
        `).join('') || "<div style='color:#64748b;'>No tasks.</div>";
      }} else {{ alert("Unauthorized"); window.location.href = '/dashboard.html'; }}
    }}

    async function approveWorker(id) {{
      await fetch('/api/admin/approve_worker', {{
        method: 'POST', headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{phone_number: phone, worker_id: id}})
      }});
      loadAdmin();
    }}
    loadAdmin();
  </script>
</body>
</html>"""


with open("public/dashboard.html", "w", encoding="utf-8") as f:
    f.write(DASHBOARD_HTML)
with open("public/admin.html", "w", encoding="utf-8") as f:
    f.write(ADMIN_HTML)
