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
</head>
<body class="dark-theme">

  <nav class="navbar">
    <div class="logo">
      <div class="logo-icon" style="background: var(--brand-accent);">⚡</div>
      Sarathi AI
    </div>
    <div class="nav-links">
      <a href="#how-it-works">How it works</a>
      <a href="/worker.html">Worker Portal</a>
      <button class="btn btn-primary" onclick="openLoginModal()">Login / Sign Up</button>
    </div>
  </nav>

  <main class="hero-section">
    <div class="hero-content text-center" style="max-width: 800px; margin: 4rem auto;">
      <h1 class="hero-title" style="font-size: 3.5rem; margin-bottom: 1rem;">
        Get anything done.<br>Pay only when it's perfect.
      </h1>
      <p class="hero-subtitle" style="font-size: 1.2rem; color: var(--text-muted); margin-bottom: 2rem;">
        The AI-powered gig network for India. Send a text on Telegram, get an instant quote, and your money is held safely in UPI Escrow until the job is done.
      </p>
      
      <div style="display: flex; gap: 1rem; justify-content: center;">
        <button class="btn btn-primary" style="font-size: 1.1rem; padding: 1rem 2rem;" onclick="openLoginModal()">
          Get Started
        </button>
        <a href="https://t.me/SarathiAI_SIH_bot" target="_blank" class="btn btn-outline" style="font-size: 1.1rem; padding: 1rem 2rem; border-color: var(--brand-accent); color: var(--brand-accent-bright);">
          <i data-lucide="send" style="width: 18px; margin-right: 8px;"></i> Message Bot
        </a>
      </div>
    </div>
  </main>

  <!-- Login Modal -->
  <div id="login-modal" class="modal-overlay">
    <div class="modal-content glass-card" style="max-width: 400px; text-align: center;">
      <h3 style="margin-bottom: 0.5rem; font-size: 1.5rem;">Welcome to Sarathi AI</h3>
      <p style="color: var(--text-muted); margin-bottom: 2rem; font-size: 0.9rem;">Enter your phone number to login or sign up.</p>
      
      <!-- Phone Input Step -->
      <div id="step-phone">
        <input type="tel" id="phone-input" placeholder="+91 9999999999" style="width: 100%; padding: 0.8rem; border-radius: 4px; border: 1px solid var(--border-color); background: rgba(0,0,0,0.5); color: white; font-size: 1.1rem; text-align: center; margin-bottom: 1rem;">
        
        <div id="recaptcha-container" style="margin-bottom: 1rem; display: flex; justify-content: center;"></div>
        
        <button class="btn btn-primary" id="send-otp-btn" style="width: 100%; padding: 0.8rem; font-size: 1.1rem;" onclick="sendOTP()">
          Send OTP
        </button>
      </div>

      <!-- OTP Input Step -->
      <div id="step-otp" style="display: none;">
        <input type="text" id="otp-input" placeholder="123456" style="width: 100%; padding: 0.8rem; border-radius: 4px; border: 1px solid var(--border-color); background: rgba(0,0,0,0.5); color: white; font-size: 1.2rem; text-align: center; letter-spacing: 4px; margin-bottom: 1rem;" maxlength="6">
        
        <button class="btn btn-primary" id="verify-otp-btn" style="width: 100%; padding: 0.8rem; font-size: 1.1rem;" onclick="verifyOTP()">
          Verify & Login
        </button>
      </div>

      <button class="btn btn-outline" style="width: 100%; margin-top: 1rem; border: none;" onclick="closeLoginModal()">Cancel</button>
    </div>
  </div>

  <script>
    lucide.createIcons();

    const firebaseConfig = {
      apiKey: "AIzaSyA2lrC0hSXSh8QdP9qVvQa0Mg7nCy_HA-8",
      authDomain: "sarathi-ai-33e65.firebaseapp.com",
      projectId: "sarathi-ai-33e65",
      storageBucket: "sarathi-ai-33e65.firebasestorage.app",
      messagingSenderId: "240982372574",
      appId: "1:240982372574:web:90ce49cfe77af625da524f"
    };
    
    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
    }
    const auth = firebase.auth();
    let confirmationResult = null;

    // Initialize reCAPTCHA exactly ONCE when the window loads
    window.onload = () => {
        window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
          'size': 'normal',
          'callback': (response) => {
             // reCAPTCHA solved
          }
        });
        window.recaptchaVerifier.render();
    };

    function openLoginModal() {
      document.getElementById('login-modal').classList.add('active');
    }

    function closeLoginModal() {
      document.getElementById('login-modal').classList.remove('active');
      document.getElementById('step-phone').style.display = 'block';
      document.getElementById('step-otp').style.display = 'none';
    }

    async function sendOTP() {
      const rawPhone = document.getElementById('phone-input').value;
      const phoneNumber = rawPhone.replace(/\s+/g, '').trim(); 
      const btn = document.getElementById('send-otp-btn');
      
      if(!phoneNumber.startsWith('+')) {
        alert("Please include country code, e.g. +91");
        return;
      }
      
      if (!window.recaptchaVerifier) {
          alert("Wait for ReCAPTCHA to load...");
          return;
      }
      
      btn.innerText = "Sending...";
      btn.disabled = true;

      try {
        confirmationResult = await auth.signInWithPhoneNumber(phoneNumber, window.recaptchaVerifier);
        document.getElementById('step-phone').style.display = 'none';
        document.getElementById('step-otp').style.display = 'block';
      } catch (error) {
        console.error(error);
        alert("Firebase Error: " + error.message);
        
        // Only reset it if it failed, so they can try again
        window.recaptchaVerifier.render();
      }
      btn.innerText = "Send OTP";
      btn.disabled = false;
    }

    async function verifyOTP() {
      const otp = document.getElementById('otp-input').value.trim();
      const btn = document.getElementById('verify-otp-btn');
      btn.innerText = "Verifying...";
      btn.disabled = true;

      try {
        const result = await confirmationResult.confirm(otp);
        const user = result.user;
        await syncUserAndRedirect(user.phoneNumber);
      } catch (error) {
        alert("Invalid OTP or expired.");
        btn.innerText = "Verify & Login";
        btn.disabled = false;
      }
    }

    async function syncUserAndRedirect(phoneNumber) {
      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone_number: phoneNumber })
        });
        const data = await res.json();
        if (data.status === 'success') {
          localStorage.setItem('user_id', data.user.id);
          localStorage.setItem('phone_number', data.user.phone_number);
          
          if(data.is_admin) {
             window.location.href = '/admin.html';
          } else {
             window.location.href = '/dashboard.html';
          }
        }
      } catch (err) {
        console.error(err);
      }
    }
  </script>
</body>
</html>"""

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
