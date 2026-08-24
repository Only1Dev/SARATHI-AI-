import os

with open("public/worker.html", "r", encoding="utf-8") as f:
    html = f.read()

# Replace Claim button with Claim / Decline buttons
old_claim = """content += `<button class="btn-glow" style="padding:0.6rem; width:100%; font-size:0.9rem;" onclick="claimTask('${t.id}')">Claim Task</button>`;"""
new_claim = """content += `<div style="display:flex; gap:10px;">
    <button class="btn-glow" id="btn-claim-${t.id}" style="padding:0.6rem; width:100%; font-size:0.9rem;" onclick="claimTask('${t.id}')">Claim Task</button>
    <button class="btn-outline" id="btn-decline-${t.id}" style="padding:0.6rem; width:100%; font-size:0.9rem; border-color: rgba(244,63,94,0.5); color: #f43f5e;" onclick="declineTask('${t.id}')">Decline (Low Budget)</button>
</div>`;"""

if old_claim in html:
    html = html.replace(old_claim, new_claim)
    
# Add declineTask logic and debounce claimTask
old_claim_logic = """async function claimTask(id) { 
      await fetch('/api/worker/claim', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({task_id: id, worker_id: localStorage.getItem("worker_id")}) }); 
      loadFeed(); 
    }"""
new_claim_logic = """async function claimTask(id) { 
      const btn = document.getElementById(`btn-claim-${id}`);
      btn.innerText = "Claiming..."; btn.disabled = true;
      document.getElementById(`btn-decline-${id}`).style.display = "none";
      await fetch('/api/worker/claim', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({task_id: id, worker_id: localStorage.getItem("worker_id")}) }); 
      loadFeed(); 
    }
    
    async function declineTask(id) {
      if(!confirm("Are you sure you want to decline this task? The user will be notified that the budget was too low.")) return;
      const btn = document.getElementById(`btn-decline-${id}`);
      btn.innerText = "Declining..."; btn.disabled = true;
      document.getElementById(`btn-claim-${id}`).style.display = "none";
      await fetch('/api/worker/decline', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({task_id: id}) });
      loadFeed();
    }"""

if old_claim_logic in html:
    html = html.replace(old_claim_logic, new_claim_logic)

with open("public/worker.html", "w", encoding="utf-8") as f:
    f.write(html)
