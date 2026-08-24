admin_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sarathi AI - Master Admin</title>
  <link rel="stylesheet" href="/css/cascade.css">
  <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body class="dark-theme">
  <nav class="navbar">
    <div class="logo">
      <div class="logo-icon" style="background: var(--brand-accent);">⚡</div>
      Sarathi AI Admin
    </div>
    <div class="nav-links">
      <a href="/">Home</a>
      <a href="#" onclick="localStorage.clear(); window.location.href='/'">Logout</a>
    </div>
  </nav>

  <main style="max-width: 1000px; margin: 2rem auto; padding: 0 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
      <h2 style="font-size: 2rem;">Master Dashboard</h2>
      <div class="glass-card" style="padding: 1rem 2rem; display: flex; align-items: center; gap: 1rem;">
        <i data-lucide="wallet" style="color: var(--brand-accent);"></i>
        <div>
          <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">Platform Volume</div>
          <div style="font-size: 1.5rem; font-weight: 600;">₹ 12,500.00</div>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
      <div class="glass-card">
        <h3 style="margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">Recent Tasks</h3>
        <div style="color: var(--text-muted); font-size: 0.9rem;">No tasks in database yet.</div>
      </div>

      <div class="glass-card">
        <h3 style="margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">Worker Approvals</h3>
        <div style="color: var(--text-muted); font-size: 0.9rem;">No pending workers.</div>
      </div>
    </div>
  </main>

  <script>
    lucide.createIcons();
    // In a real app, we would fetch data from the backend here.
  </script>
</body>
</html>"""

dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sarathi AI - User Dashboard</title>
  <link rel="stylesheet" href="/css/cascade.css">
  <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body class="dark-theme">
  <nav class="navbar">
    <div class="logo">
      <div class="logo-icon" style="background: var(--brand-accent);">⚡</div>
      Sarathi AI Escrow
    </div>
    <div class="nav-links">
      <a href="/">Home</a>
      <a href="#" onclick="localStorage.clear(); window.location.href='/'">Logout</a>
    </div>
  </nav>

  <main style="max-width: 1000px; margin: 2rem auto; padding: 0 1rem;">
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2rem;">
      
      <!-- Wallet Sidebar -->
      <div class="glass-card" style="height: fit-content;">
        <h3 style="margin-bottom: 1.5rem;">Your Wallet</h3>
        <div style="margin-bottom: 1.5rem;">
          <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">Available Balance</div>
          <div style="font-size: 2.5rem; font-weight: 600; color: white;">₹ <span id="balance-amount">0.00</span></div>
        </div>
        
        <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i data-lucide="lock" style="color: #f59e0b; width: 16px;"></i>
            <span style="font-size: 0.9rem; color: var(--text-muted);">In Escrow</span>
          </div>
          <div style="font-weight: 600;">₹ 0.00</div>
        </div>

        <button class="btn btn-primary" style="width: 100%; padding: 0.8rem;">
          <i data-lucide="plus" style="width: 16px; margin-right: 0.5rem;"></i> Add Funds
        </button>
      </div>

      <!-- Task History -->
      <div class="glass-card">
        <h3 style="margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">Active Tasks</h3>
        
        <div style="text-align: center; padding: 3rem 0; color: var(--text-muted);">
          <i data-lucide="inbox" style="width: 48px; height: 48px; opacity: 0.5; margin-bottom: 1rem;"></i>
          <p>No active tasks.</p>
          <p style="font-size: 0.8rem; margin-top: 0.5rem;">Send a message to the Telegram bot to start a task!</p>
        </div>
      </div>
      
    </div>
  </main>

  <script>
    lucide.createIcons();
    // Mock fetching balance based on local storage
    document.addEventListener("DOMContentLoaded", () => {
        const phone = localStorage.getItem("phone_number");
        if(phone === "+917015960679") {
            document.getElementById("balance-amount").innerText = "5000.00";
        }
    });
  </script>
</body>
</html>"""

import os
with open("public/admin.html", "w", encoding="utf-8") as f:
    f.write(admin_html)
with open("public/dashboard.html", "w", encoding="utf-8") as f:
    f.write(dashboard_html)
