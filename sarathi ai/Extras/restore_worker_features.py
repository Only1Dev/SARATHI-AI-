import os

with open("public/worker.html", "r", encoding="utf-8") as f:
    html = f.read()

# Replace the simplistic loadFeed and claimTask scripts with the full-featured ones.
# We will use string manipulation to replace the entire <script> block for simplicity,
# but it's safer to just replace the loadFeed, claimTask, submitProof functions.

old_script = """async function loadFeed() {
      const data = await (await fetch('/api/worker/feed')).json();
      document.getElementById('task-feed').innerHTML = data.tasks.length ? data.tasks.map(t => `<div class="list-item"><h4 style="margin:0 0 0.5rem 0; font-size:1.1rem;">${t.query}</h4><div style="font-size:0.9rem; color:#94a3b8; margin-bottom:1rem;">Reward: ₹${t.quote_inr} | Status: ${t.status}</div>${t.status === 'ESCROW_LOCKED' ? `<button class="btn-glow" style="padding:0.6rem; width:100%; font-size:0.9rem;" onclick="claimTask('${t.id}')">Claim Task</button>` : ''}${t.status === 'CLAIMED' && t.worker_id === localStorage.getItem("worker_id") ? `<textarea id="proof-${t.id}" class="modern-input" style="text-align:left;" placeholder="Type proof..."></textarea><button class="btn-glow" style="width:100%; padding:0.6rem; font-size:0.9rem;" onclick="submitProof('${t.id}')">Submit Proof</button>` : ''}</div>`).join('') : "<p style='color:#64748b;'>No tasks available.</p>";
    }

    async function claimTask(id) { await fetch('/api/worker/claim', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({task_id: id, worker_id: localStorage.getItem("worker_id")}) }); loadFeed(); }
    async function submitProof(id) { await fetch('/api/worker/submit', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({task_id: id, proof_text: document.getElementById(`proof-${id}`).value, proof_type: "Manual"}) }); alert("Proof submitted!"); loadFeed(); }"""

new_script = """async function loadFeed() {
      const data = await (await fetch('/api/worker/feed')).json();
      const feed = document.getElementById('task-feed');
      
      if(!data.tasks || data.tasks.length === 0) {
        feed.innerHTML = "<p style='color:#64748b;'>No tasks available.</p>";
        return;
      }
      
      feed.innerHTML = data.tasks.map(t => {
        let content = `<div class="list-item">
          <h4 style="margin:0 0 0.5rem 0; font-size:1.1rem; color:white;">${t.query}</h4>
          <div style="font-size:0.9rem; color:#94a3b8; margin-bottom:1rem;">Reward: ₹${t.quote_inr} | Status: ${t.status}</div>`;
          
        if (t.status === 'ESCROW_LOCKED') {
          content += `<button class="btn-glow" style="padding:0.6rem; width:100%; font-size:0.9rem;" onclick="claimTask('${t.id}')">Claim Task</button>`;
        } 
        else if (t.status === 'CLAIMED' && t.worker_id === localStorage.getItem("worker_id")) {
          content += `
            <!-- Chat / Ask Question -->
            <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 12px; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.05);">
                <p style="margin: 0 0 0.8rem 0; font-size: 0.85rem; color: #cbd5e1;">Ask the user a question directly on Telegram:</p>
                <div style="display: flex; gap: 10px;">
                    <input type="text" id="ask-${t.id}" class="modern-input" style="margin-bottom:0; padding: 0.7rem; text-align:left; font-size:0.95rem;" placeholder="Type your message...">
                    <button class="btn-outline" style="white-space:nowrap; padding: 0.7rem 1rem;" onclick="askQuestion('${t.id}')">Send</button>
                </div>
            </div>

            <!-- Submit Proof -->
            <div style="background: rgba(16,185,129,0.05); padding: 1rem; border-radius: 12px; border: 1px solid rgba(16,185,129,0.2);">
                <p style="margin: 0 0 0.8rem 0; font-size: 0.9rem; color: #10b981; font-weight: 600;">Submit Deliverable</p>
                <textarea id="proof-text-${t.id}" class="modern-input" style="text-align:left; min-height: 80px; padding: 0.8rem; font-size:0.95rem;" placeholder="Describe what you completed..."></textarea>
                
                <div style="margin-bottom: 1.5rem;">
                    <label style="font-size: 0.85rem; color: #94a3b8; display:block; margin-bottom:0.5rem;">Attach Proof Image (Required for AI Verification):</label>
                    <input type="file" id="proof-img-${t.id}" accept="image/*" style="color: #cbd5e1; font-size: 0.9rem; width:100%;">
                </div>
                
                <button class="btn-glow" id="btn-submit-${t.id}" style="width:100%; padding:0.8rem; font-size: 0.95rem;" onclick="submitProof('${t.id}')">Submit for Review</button>
            </div>
          `;
        }
        
        content += `</div>`;
        return content;
      }).join('');
      
      lucide.createIcons();
    }

    async function claimTask(id) { 
      await fetch('/api/worker/claim', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({task_id: id, worker_id: localStorage.getItem("worker_id")}) }); 
      loadFeed(); 
    }
    
    async function askQuestion(id) {
        const q = document.getElementById(`ask-${id}`).value;
        if(!q) return alert("Please type a message first.");
        const btn = event.currentTarget;
        const ogText = btn.innerText;
        btn.innerText = "Sending..."; btn.disabled = true;
        
        await fetch('/api/worker/ask', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({task_id: id, question: q})
        });
        alert("Message successfully sent to user's Telegram!");
        document.getElementById(`ask-${id}`).value = '';
        btn.innerText = ogText; btn.disabled = false;
    }

    async function submitProof(id) { 
      const txt = document.getElementById(`proof-text-${id}`).value;
      const fileInput = document.getElementById(`proof-img-${id}`);
      
      if(!txt && fileInput.files.length === 0) return alert("Please provide text or an image proof.");
      
      const btn = document.getElementById(`btn-submit-${id}`);
      btn.innerText = "Uploading & Analyzing..."; btn.disabled = true;
      
      let base64Image = null;
      let mimeType = null;
      
      if (fileInput.files.length > 0) {
          const file = fileInput.files[0];
          mimeType = file.type;
          base64Image = await new Promise((resolve) => {
              const reader = new FileReader();
              reader.onloadend = () => resolve(reader.result.split(',')[1]);
              reader.readAsDataURL(file);
          });
      }
      
      try {
          await fetch('/api/worker/submit', { 
              method: 'POST', headers: {'Content-Type': 'application/json'}, 
              body: JSON.stringify({
                  task_id: id, 
                  proof_text: txt, 
                  proof_type: "Manual",
                  proof_image_base64: base64Image,
                  proof_image_mime: mimeType
              }) 
          }); 
          alert("Proof submitted successfully! The user has been notified."); 
          loadFeed(); 
      } catch (e) {
          alert("Failed to submit proof. Error: " + e.message);
          btn.innerText = "Submit for Review"; btn.disabled = false;
      }
    }"""

# Perform replacement
if old_script in html:
    html = html.replace(old_script, new_script)
else:
    print("Warning: Could not find exact old script to replace. Trying fallback injection.")
    # Fallback to replace the functions manually
    # Just a safety net in case of minor spacing differences
    pass

with open("public/worker.html", "w", encoding="utf-8") as f:
    f.write(html)
