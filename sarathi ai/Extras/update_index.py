html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sarathi AI - India's First AI Escrow Network</title>
  <link rel="stylesheet" href="/css/cascade.css">
  <script src="https://unpkg.com/lucide@latest"></script>
  
  <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
  <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script>
  
  <style>
    .modal-overlay {
      display: none;
      position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(10px);
      z-index: 1000;
      justify-content: center;
      align-items: center;
      opacity: 0; transition: opacity 0.3s ease;
    }
    .modal-overlay.active { display: flex; opacity: 1; }
    
    .modern-modal {
      background: linear-gradient(145deg, #1e293b, #0f172a);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 40px rgba(16, 185, 129, 0.2);
      border-radius: 20px;
      padding: 2.5rem 2rem;
      width: 90%; max-width: 420px;
      text-align: center;
      position: relative;
      transform: translateY(20px);
      transition: transform 0.3s ease;
    }
    .modal-overlay.active .modern-modal { transform: translateY(0); }
    
    .modern-input {
      width: 100%;
      padding: 1rem;
      border-radius: 12px;
      border: 1px solid #334155;
      background: rgba(15, 23, 42, 0.6);
      color: white;
      font-size: 1.2rem;
      text-align: center;
      letter-spacing: 2px;
      transition: all 0.2s ease;
      margin-bottom: 1.5rem;
    }
    .modern-input:focus { outline: none; border-color: var(--brand-accent); box-shadow: 0 0 15px rgba(16, 185, 129, 0.2); }
    
    .btn-glow {
      background: linear-gradient(135deg, var(--brand-accent), #059669);
      color: white;
      border: none;
      padding: 1rem;
      border-radius: 12px;
      font-size: 1.1rem;
      font-weight: 600;
      width: 100%;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
    }
    .btn-glow:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6); }
    .btn-glow:disabled { opacity: 0.7; cursor: not-allowed; transform: none; box-shadow: none; }
    
    .close-btn {
      position: absolute; top: 1rem; right: 1rem;
      background: none; border: none; color: #94a3b8;
      cursor: pointer; padding: 0.5rem; border-radius: 50%;
      transition: all 0.2s;
    }
    .close-btn:hover { background: rgba(255,255,255,0.1); color: white; }
  </style>
</head>
<body class="dark-theme">

  <nav class="navbar">
    <div class="logo">
      <div class="logo-icon" style="background: var(--brand-accent);">⚡</div>
      Sarathi AI
    </div>
    <div class="nav-links">
      <a href="/worker.html">Worker Portal</a>
      <button class="btn btn-primary" onclick="openLoginModal()">Login / Sign Up</button>
    </div>
  </nav>

  <main class="hero-section">
    <div class="hero-content text-center" style="max-width: 800px; margin: 4rem auto;">
      <div style="display:inline-block; padding: 0.5rem 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--brand-accent); border-radius: 30px; color: var(--brand-accent); margin-bottom: 1.5rem; font-weight: 600;">
        Now Live for SIH 2026
      </div>
      <h1 class="hero-title" style="font-size: 4rem; margin-bottom: 1.5rem; line-height: 1.1;">
        Get anything done.<br>Pay only when it's <span style="color: var(--brand-accent);">perfect.</span>
      </h1>
      <p class="hero-subtitle" style="font-size: 1.25rem; color: #94a3b8; margin-bottom: 2.5rem; line-height: 1.6;">
        The AI-powered gig network for India. Send a text on Telegram, get an instant quote, and your money is held safely in UPI Escrow until the job is done.
      </p>
      
      <div style="display: flex; gap: 1rem; justify-content: center;">
        <button class="btn-glow" style="width: auto; padding: 1rem 2.5rem; font-size: 1.1rem;" onclick="openLoginModal()">
          Open Escrow Wallet
        </button>
        <a href="https://t.me/SarathiAI_SIH_bot" target="_blank" class="btn btn-outline" style="font-size: 1.1rem; padding: 1rem 2rem; border-color: #334155; color: white;">
          <i data-lucide="send" style="width: 18px; margin-right: 8px;"></i> Message Telegram Bot
        </a>
      </div>
    </div>
  </main>

  <!-- Modern Login Modal -->
  <div id="login-modal" class="modal-overlay">
    <div class="modern-modal">
      <button class="close-btn" onclick="closeLoginModal()"><i data-lucide="x"></i></button>
      
      <div style="width: 50px; height: 50px; background: var(--brand-accent); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem; box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);">
        <i data-lucide="shield-check" style="color: white; width: 28px; height: 28px;"></i>
      </div>
      
      <h3 style="margin-bottom: 0.5rem; font-size: 1.6rem; font-weight: 600;">Secure Login</h3>
      <p style="color: #94a3b8; margin-bottom: 2rem; font-size: 0.95rem;">Enter your phone number to access your Escrow Wallet.</p>
      
      <div id="step-phone">
        <input type="tel" class="modern-input" id="phone-input" placeholder="+91 9999999999">
        <div id="recaptcha-container" style="margin-bottom: 1.5rem; display: flex; justify-content: center;"></div>
        <button class="btn-glow" id="send-otp-btn" onclick="sendOTP()">Send Secure OTP</button>
      </div>

      <div id="step-otp" style="display: none;">
        <input type="text" class="modern-input" id="otp-input" placeholder="123456" maxlength="6">
        <button class="btn-glow" id="verify-otp-btn" onclick="verifyOTP()">Verify & Access Wallet</button>
        <p style="margin-top: 1rem; color: #94a3b8; font-size: 0.85rem; cursor: pointer;" onclick="resetLogin()">← Back to phone number</p>
      </div>
    </div>
  </div>

  <script>
    lucide.createIcons();

    const firebaseConfig = {
      apiKey: "AIzaSyA2lrC0hSXSh8QdP9qVvQa0Mg7nCy_HA-8",
      authDomain: "sarathi-ai-33e65.firebaseapp.com",
      projectId: "sarathi-ai-33e65"
    };
    if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();
    let confirmationResult = null;

    window.onload = () => {
        if(!window.recaptchaVerifier) {
            window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {'size': 'normal'});
            window.recaptchaVerifier.render();
        }
    };

    function openLoginModal() { document.getElementById('login-modal').classList.add('active'); }
    function closeLoginModal() { document.getElementById('login-modal').classList.remove('active'); resetLogin(); }
    function resetLogin() {
        document.getElementById('step-phone').style.display = 'block';
        document.getElementById('step-otp').style.display = 'none';
        document.getElementById('otp-input').value = '';
    }

    async function sendOTP() {
      const rawPhone = document.getElementById('phone-input').value;
      const phoneNumber = rawPhone.replace(/\s+/g, '').trim(); 
      const btn = document.getElementById('send-otp-btn');
      
      if(!phoneNumber.startsWith('+')) return alert("Please include country code, e.g. +91");
      
      btn.innerText = "Sending...";
      btn.disabled = true;

      try {
        confirmationResult = await auth.signInWithPhoneNumber(phoneNumber, window.recaptchaVerifier);
        document.getElementById('step-phone').style.display = 'none';
        document.getElementById('step-otp').style.display = 'block';
      } catch (error) {
        alert("Firebase Error: " + error.message);
        window.recaptchaVerifier.render();
      }
      btn.innerText = "Send Secure OTP";
      btn.disabled = false;
    }

    async function verifyOTP() {
      const otp = document.getElementById('otp-input').value.trim();
      const btn = document.getElementById('verify-otp-btn');
      btn.innerText = "Verifying...";
      btn.disabled = true;

      try {
        const result = await confirmationResult.confirm(otp);
        await syncUserAndRedirect(result.user.phoneNumber);
      } catch (error) {
        alert("Invalid OTP or expired.");
        btn.innerText = "Verify & Access Wallet";
        btn.disabled = false;
      }
    }

    async function syncUserAndRedirect(phoneNumber) {
      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone_number: phoneNumber })
        });
        const data = await res.json();
        if (data.status === 'success') {
          localStorage.setItem('user_id', data.user.id);
          localStorage.setItem('phone_number', data.user.phone_number);
          window.location.href = data.is_admin ? '/admin.html' : '/dashboard.html';
        }
      } catch (err) { console.error(err); }
    }
  </script>
</body>
</html>"""

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
