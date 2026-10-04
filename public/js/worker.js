/**
 * Sarathi Worker Portal Controller (Cascade India)
 */

let CURRENT_WORKER_ID = 'w_1';
let WORKERS = {
  'w_1': { name: 'Aarav Sharma (Bengaluru)', upi: 'aarav.gig@okhdfc', rating: '⭐ 4.94', balance: 1820 },
  'w_2': { name: 'Priya Nair, CA Inter (Delhi NCR)', upi: 'priya.ca@okaxis', rating: '⭐ 5.0', balance: 4500 },
  'w_3': { name: 'Rohan Deshmukh (Pune)', upi: 'rohan.d@icici', rating: '⭐ 4.88', balance: 960 },
  'w_4': { name: 'Shivam', upi: 'shivam.dev@okaxis', rating: '⭐ 4.99', balance: 0 }
};

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();
  
  document.getElementById('worker-select-dropdown').addEventListener('change', (e) => {
    CURRENT_WORKER_ID = e.target.value;
    updateWorkerDisplay();
    fetchWorkerFeed();
  });

  document.getElementById('submit-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const taskId = document.getElementById('modal-task-id').value;
    const proofType = document.getElementById('modal-proof-type').value;
    const proofText = document.getElementById('modal-proof-text').value;
    
    // Handle optional image upload
    const imgInput = document.getElementById('modal-proof-image');
    let base64Image = null;
    let mimeType = null;
    
    if (imgInput.files.length > 0) {
      const file = imgInput.files[0];
      mimeType = file.type;
      base64Image = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.readAsDataURL(file);
      });
    }
    
    submitWorkerProof(taskId, proofType, proofText, base64Image, mimeType);
  });

  updateWorkerDisplay();
  fetchWorkerFeed();
  setInterval(fetchWorkerFeed, 2500);
});

function updateWorkerDisplay() {
  const w = WORKERS[CURRENT_WORKER_ID];
  document.getElementById('worker-name-display').textContent = w.name;
  document.getElementById('worker-upi-display').textContent = `UPI ID: ${w.upi} · Earnings: ₹${w.balance} · Rating: ${w.rating}`;
}

async function fetchWorkerFeed() {
  try {
    const res = await fetch('/api/worker/feed');
    const data = await res.json();
    if (data.status === 'success') {
      renderJobFeed(data.tasks);
    }
  } catch (err) {
    console.error("Error fetching feed:", err);
  }
}

function renderJobFeed(tasks) {
  const container = document.getElementById('worker-job-list');
  
  // Filter tasks for current worker
  const currentWorkerId = document.getElementById('worker-select-dropdown').value;
  const workerObj = WORKERS[currentWorkerId];
  
  const visibleTasks = tasks.filter(t => {
    // If task is claimed by someone else, hide it
    if (t.worker && t.worker.id !== currentWorkerId) return false;
    // If task is targeted to a specific worker
    if (t.target_worker) {
        // Allow if the target worker name matches our worker's name
        return t.target_worker.toLowerCase() === workerObj.name.toLowerCase() || workerObj.name.toLowerCase().includes(t.target_worker.toLowerCase());
    }
    return true; // No target worker, show to all
  });

  document.getElementById('job-count').textContent = visibleTasks.length;

  if (visibleTasks.length === 0) {
    container.innerHTML = `
      <div style="background: var(--bg-surface); border: 1px solid var(--border-hairline); border-radius: 1rem; padding: 3rem; text-align: center; color: var(--text-dim);">
        <i data-lucide="inbox" style="width: 40px; height: 40px; opacity: 0.4; margin-bottom: 0.5rem;"></i>
        <div style="font-size: 1.1rem; color: var(--text-main);">No active escrow jobs in queue</div>
        <div style="font-size: 0.85rem; margin-top: 4px;">Send a task on Telegram to generate a live job!</div>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  let html = '';
  tasks.forEach(task => {
    const isGig = task.tier === 'gig';
    const badgeClass = isGig ? 'badge-gig' : 'badge-expert';
    const tierTitle = isGig ? 'Gig Task' : 'Certified Specialist';

    let actionBtn = '';

    if (task.status === 'ESCROW_LOCKED') {
      actionBtn = `
        <button class="btn btn-primary" onclick="claimTask('${task.id}')">
          <i data-lucide="zap" style="width: 15px;"></i> Claim Task (Earn ₹${task.quote_inr})
        </button>
      `;
    } else if (task.status === 'CLAIMED') {
      actionBtn = `
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
          <button class="btn btn-outline" style="border-color: var(--brand-accent); color: var(--brand-accent-bright); padding: 0.4rem 0.8rem; font-size: 0.8rem;" onclick="openAskModal('${task.id}')">
            <i data-lucide="message-square" style="width: 14px;"></i> Ask User
          </button>
          <button class="btn btn-outline" style="border-color: var(--brand-accent); color: var(--brand-accent-bright); padding: 0.4rem 0.8rem; font-size: 0.8rem;" onclick="openSubmitModal('${task.id}')">
            <i data-lucide="upload-cloud" style="width: 14px;"></i> Submit Proof
          </button>
        </div>
      `;
    } else if (task.status === 'DELIVERED') {
      const score = task.deliverable?.ai_verification?.confidence_score || 'Pending';
      actionBtn = `
        <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); padding: 8px 14px; border-radius: 8px; font-size: 0.8rem; color: var(--brand-accent-bright);">
          🤖 AI Proof Verified: ${score}% Score · Payout Released to ${task.worker?.name || 'Worker'}!
        </div>
      `;
    }

    html += `
      <div class="task-job-card">
        <div class="task-job-header">
          <div>
            <span class="badge-tag ${badgeClass}">${tierTitle}</span>
            <span class="badge-tag badge-escrow" style="margin-left: 6px;">₹${task.quote_inr} Escrow Locked</span>
          </div>
          <div class="payout-amt">₹${task.quote_inr}</div>
        </div>

        <div style="font-size: 1.05rem; font-weight: 600; line-height: 1.4;">
          ${escapeHtml(task.query)}
        </div>

        <div style="font-size: 0.85rem; color: var(--text-muted); background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; border-left: 3px solid var(--brand-saffron);">
          <em>Triage Reasoning:</em> ${escapeHtml(task.reasoning)}
        </div>

        ${task.deliverable ? `
          <div style="font-size: 0.85rem; background: rgba(16, 185, 129, 0.08); padding: 10px; border-radius: 8px; border-left: 3px solid var(--brand-accent);">
            <strong>Submitted Proof (${escapeHtml(task.deliverable.proof_type)}):</strong><br>
            ${escapeHtml(task.deliverable.text)}
          </div>
        ` : ''}

        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem;">
          <span style="font-size: 0.8rem; color: var(--text-dim);">Est. Time: ~${task.turnaround_mins} mins</span>
          ${actionBtn}
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
  if (window.lucide) lucide.createIcons();
}

async function claimTask(taskId) {
  try {
    const res = await fetch('/api/worker/claim', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId, worker_id: CURRENT_WORKER_ID })
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert(`⚡ Task claimed by ${data.task.worker.name}!`);
      fetchWorkerFeed();
    }
  } catch (err) {
    alert("Failed to claim task");
  }
}

function openSubmitModal(taskId) {
  document.getElementById('modal-task-id').value = taskId;
  document.getElementById('modal-proof-text').value = '';
  document.getElementById('submit-modal').classList.add('active');
}

function closeSubmitModal() {
  document.getElementById('submit-modal').classList.remove('active');
}

function openAskModal(taskId) {
  document.getElementById('ask-task-id').value = taskId;
  document.getElementById('ask-text').value = '';
  document.getElementById('ask-modal').classList.add('active');
}

function closeAskModal() {
  document.getElementById('ask-modal').classList.remove('active');
}

document.getElementById('ask-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const taskId = document.getElementById('ask-task-id').value;
  const text = document.getElementById('ask-text').value;
  try {
    const res = await fetch('/api/worker/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId, question: text })
    });
    const data = await res.json();
    if (data.status === 'success') {
      closeAskModal();
      alert("Message sent to user!");
    } else {
      alert("Failed to send message: " + data.message);
    }
  } catch(e) {
    alert("Error sending message.");
  }
});

async function submitWorkerProof(taskId, proofType, proofText, base64Image, mimeType) {
  try {
    const payload = {
      task_id: taskId,
      proof_type: proofType,
      proof_text: proofText,
    };
    if (base64Image) {
      payload.proof_image_base64 = base64Image;
      payload.proof_image_mime = mimeType;
    }
    
    const res = await fetch('/api/worker/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === 'success') {
      closeSubmitModal();
      alert("📦 Deliverable submitted! AI Proof Verification Engine triggered.");
      fetchWorkerFeed();
    }
  } catch (err) {
    alert("Submission failed");
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
