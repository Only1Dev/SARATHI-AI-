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
      width: 100%;
    }
    .btn-glow:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.5); }
    
    .modern-input { width: 100%; padding: 1rem; border-radius: 12px; border: 1px solid #334155; background: rgba(15, 23, 42, 0.6); color: white; font-size: 1.1rem; text-align: center; margin-bottom: 1.5rem; }
    
    .list-item {
      background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.03);
      padding: 1.5rem; border-radius: 16px; margin-bottom: 1rem;
      transition: all 0.3s ease;
    }
    .list-item:hover { border-color: rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.03); }
    
    .badge { padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
    .badge-pending { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-success { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
  </style>
"""

with open('public/worker.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace old CSS with ultra premium CSS
text = text.split('<style>')[0] + PREMIUM_CSS + "</head>" + text.split('</head>')[1]

# Also ensure classes are right
text = text.replace('class="glass-card"', 'class="modern-card"')

with open('public/worker.html', 'w', encoding='utf-8') as f:
    f.write(text)
