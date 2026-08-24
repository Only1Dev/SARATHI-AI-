with open('public/worker.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the navbar to match the new design
old_nav = """<nav class="navbar">
    <div class="logo">⚡ Worker Portal</div>
    <div class="nav-links">
      <a href="#" onclick="localStorage.removeItem('worker_phone'); window.location.reload();" id="logout-btn" style="display:none;">Logout</a>
    </div>
  </nav>"""

new_nav = """<nav class="navbar">
    <div class="logo">
      <div class="logo-icon" style="background: var(--brand-accent);">⚡</div>
      Worker Portal
    </div>
    <div class="nav-links">
      <a href="/dashboard.html">User Wallet</a>
      <button class="btn btn-outline" onclick="localStorage.removeItem('worker_phone'); window.location.reload();" id="logout-btn" style="display:none;">Logout</button>
    </div>
  </nav>"""

text = text.replace(old_nav, new_nav)

# Make sure the auth box matches the modern modal design somewhat
text = text.replace('class="glass-card"', 'class="modern-modal" style="margin: 4rem auto; background: linear-gradient(145deg, #1e293b, #0f172a); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 2.5rem 2rem; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);"', 1)
text = text.replace('id="send-otp-btn" style="width:100%;"', 'id="send-otp-btn" class="btn-glow"')
text = text.replace('id="verify-otp-btn" style="width:100%;"', 'id="verify-otp-btn" class="btn-glow"')
text = text.replace('onclick="completeRegistration()"', 'class="btn-glow" onclick="completeRegistration()"')

# Add the btn-glow CSS dynamically if it doesn't exist
style_injection = """<style>
    .btn-glow { background: linear-gradient(135deg, var(--brand-accent), #059669); color: white; border: none; padding: 1rem; border-radius: 12px; font-size: 1.1rem; font-weight: 600; width: 100%; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4); }
    .btn-glow:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6); }
    .modern-input { width: 100%; padding: 1rem; border-radius: 12px; border: 1px solid #334155; background: rgba(15, 23, 42, 0.6); color: white; font-size: 1.1rem; text-align: center; margin-bottom: 1.5rem; }
  </style>
</head>"""
text = text.replace("</head>", style_injection)

# Replace old inline inputs with modern ones
import re
text = re.sub(r'<input (.*?) style="width:100%; padding:0.8rem; margin:1rem 0; background:#111; color:#fff; border:1px solid #333;">', r'<input \1 class="modern-input">', text)
text = re.sub(r'<input (.*?) style="width:100%; padding:0.8rem; margin:0.5rem 0; background:#111; color:#fff; border:1px solid #333;">', r'<input \1 class="modern-input" style="margin-bottom: 0.5rem;">', text)


with open('public/worker.html', 'w', encoding='utf-8') as f:
    f.write(text)
