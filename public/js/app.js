/**
 * Sarathi AI (Cascade India) - Frontend Controller & Realtime State Sync
 */

let CURRENT_TASK_FOR_ESCROW = null;
let CURRENT_WORKER_ID = 'w_1';
let LAST_PROCESSED_TASKS = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  setupEventListeners();
  fetchInitialData();
  // Poll state every 2.5s for real-time synchronization across panes
  setInterval(syncState, 2500);
});

function setupEventListeners() {
  // Chat form submit
  document.getElementById('chat-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const input = document.getElementById('chat-input-field');
    const text = input.value.trim();
    if (text) {
      sendTaskQuery(text);
      input.value = '';
    }
  });

  // Suggestion chips
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      sendTaskQuery(prompt);
    });
  });

  // Voice note simulation button
  const voiceBtn = document.getElementById('btn-voice-sim');
  voiceBtn.addEventListener('click', () => {
    voiceBtn.classList.toggle('recording');
    if (voiceBtn.classList.contains('recording')) {
      showToast("🎙️ Recording simulated voice note (Hindi/English)...");
      setTimeout(() => {
        voiceBtn.classList.remove('recording');
        const sampleVoiceQueries = [
          "Bhai Koramangala ke Om Stationary me call karke pucho A3 drafting board hai kya aur kitne ka hai",
          "Draft an email to my team about tomorrow's SIH sprint milestone",
          "Can you have someone test my UPI intent flow on an actual Realme Android phone?"
        ];
        const randomQuery = sampleVoiceQueries[Math.floor(Math.random() * sampleVoiceQueries.length)];
        sendTaskQuery(randomQuery, true);
      }, 2000);
    }
  });

  // Worker Select
  document.getElementById('worker-select').addEventListener('change', (e) => {
    CURRENT_WORKER_ID = e.target.value;
    updateWorkerProfileDisplay();
    syncState();
  });

  // UPI Simulation Pay button
  document.getElementById('btn-simulate-upi-pay').addEventListener('click', () => {
    if (CURRENT_TASK_FOR_ESCROW) {
      lockEscrowForTask(CURRENT_TASK_FOR_ESCROW.id);
    }
  });

  // Worker Deliverable Submit form
  document.getElementById('worker-submit-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const taskId = document.getElementById('submit-task-id').value;
    const proofType = document.getElementById('submit-proof-type').value;
    const proofText = document.getElementById('submit-proof-text').value;
    submitWorkerProof(taskId, proofType, proofText);
  });

  // Settings Modal
  document.getElementById('btn-open-settings').addEventListener('click', openSettingsModal);
  document.getElementById('settings-form').addEventListener('submit', saveSettings);

  // Reset Demo
  document.getElementById('btn-reset-demo').addEventListener('click', async () => {
    if (confirm("Reset demo data and wallet balances?")) {
      await fetch('/api/reset', { method: 'POST' });
      showToast("Demo data reset to initial state");
      fetchInitialData();
    }
  });
}

// ----------------- Data Fetching & Sync -----------------
async function fetchInitialData() {
  await syncState();
  await loadSettings();
}

async function syncState() {
  try {
    const [statsRes, tasksRes, logsRes] = await Promise.all([
      fetch('/api/stats').then(r => r.json()),
      fetch('/api/tasks').then(r => r.json()),
      fetch('/api/logs').then(r => r.json())
    ]);

    if (statsRes.status === 'success') {
      updateStats(statsRes);
    }
    if (tasksRes.status === 'success') {
      renderChatAndWorkerPanes(tasksRes.tasks);
    }
    if (logsRes.status === 'success') {
      renderLogs(logsRes.logs);
    }
  } catch (err) {
    console.error("Sync error:", err);
  }
}

function updateStats(data) {
  const w = data.wallet;
  const s = data.stats;

  document.getElementById('header-wallet-bal').textContent = `₹${w.balance_inr.toLocaleString('en-IN')}`;
  document.getElementById('header-escrow-bal').textContent = `₹${w.escrow_locked_inr.toLocaleString('en-IN')}`;

  document.getElementById('stat-ai-count').textContent = s.ai_tasks;
  document.getElementById('stat-human-count').textContent = s.human_tasks;
  document.getElementById('stat-payout-total').textContent = `₹${s.total_payouts_inr.toLocaleString('en-IN')}`;

  const escrowStateEl = document.getElementById('metric-escrow-state');
  if (w.escrow_locked_inr > 0) {
    escrowStateEl.textContent = `₹${w.escrow_locked_inr} LOCKED`;
    escrowStateEl.style.color = "var(--accent-upi)";
  } else {
    escrowStateEl.textContent = "IDLE";
    escrowStateEl.style.color = "var(--text-dim)";
  }
}

// ----------------- Chat / Requester Logic -----------------
async function sendTaskQuery(text, isVoice = false) {
  const stream = document.getElementById('chat-stream');

  // Append user message immediately
  const userMsgHtml = `
    <div class="msg msg-user">
      ${isVoice ? '🎙️ <em>[Voice Note]:</em> ' : ''}${escapeHtml(text)}
      <div class="msg-time">Just now</div>
    </div>
  `;
  stream.insertAdjacentHTML('beforeend', userMsgHtml);
  stream.scrollTop = stream.scrollHeight;

  // Append typing indicator
  const typingId = 'typing-' + Date.now();
  const typingHtml = `
    <div class="msg msg-bot" id="${typingId}">
      <span class="live-dot" style="display:inline-block; margin-right:4px;"></span>
      <em>Triaging task & matching lowest-cost capable tier...</em>
    </div>
  `;
  stream.insertAdjacentHTML('beforeend', typingHtml);
  stream.scrollTop = stream.scrollHeight;

  try {
    const res = await fetch('/api/triage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: text })
    });
    const data = await res.json();
    
    // Remove typing indicator
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    if (data.status === 'success') {
      document.getElementById('metric-latency').textContent = `${data.latency_ms} ms`;
      showToast(`Task triaged into: ${data.task.tier_name}`);
      syncState();
    }
  } catch (err) {
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    showToast("⚠️ Triage request failed", true);
  }
}

function renderChatAndWorkerPanes(tasks) {
  renderChatMessages(tasks);
  renderWorkerFeed(tasks);
}

function renderChatMessages(tasks) {
  const stream = document.getElementById('chat-stream');
  
  // Keep the welcome message
  let html = `
    <div class="msg msg-bot">
      👋 Namaste! I'm <strong>Sarathi AI</strong>. Text or voice note any task.
      <div style="margin-top: 6px; font-size: 0.76rem; color: var(--text-muted);">
        • <strong>AI Tier</strong>: Free instant answers, plans, emails.<br>
        • <strong>Gig / Expert Tier</strong>: Real humans for phone calls, tests, or legal/tax advice — paid via UPI when you approve!
      </div>
      <div class="msg-time">Online</div>
    </div>
  `;

  // Sort tasks chronologically for chat view (oldest to newest)
  const sortedTasks = [...tasks].reverse();

  sortedTasks.forEach(task => {
    // User message bubble
    html += `
      <div class="msg msg-user">
        ${escapeHtml(task.query)}
        <div class="msg-time">${task.created_at}</div>
      </div>
    `;

    // Bot response bubble
    if (task.tier === 'ai') {
      html += `
        <div class="msg msg-bot">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 6px;">
            <span class="log-tier-pill pill-ai">✨ AI TIER (₹0 FREE)</span>
            <span style="font-size:0.65rem; color:var(--text-dim);">Latency: ~40ms</span>
          </div>
          <div style="white-space: pre-wrap; font-size: 0.83rem;">${escapeHtml(task.response || '')}</div>
          <div class="msg-time">${task.created_at}</div>
        </div>
      `;
    } else {
      // Human Gig or Expert Tier
      const isGig = task.tier === 'gig';
      const tierBadge = isGig 
        ? '<span class="log-tier-pill pill-gig">🤝 GIG NETWORK TIER</span>' 
        : '<span class="log-tier-pill pill-expert">🎓 VERIFIED SPECIALIST</span>';

      let cardBody = '';

      if (task.status === 'QUOTED') {
        cardBody = `
          <div class="quote-card">
            <div class="quote-header">
              <span class="quote-title">Escrow Quote Prepared</span>
              <span class="quote-price">₹${task.quote_inr}</span>
            </div>
            <div class="quote-details">
              • Est. Turnaround: <strong>~${task.turnaround_mins} mins</strong><br>
              • Reasoning: <em>${escapeHtml(task.reasoning)}</em><br>
              • Held safely in UPI Escrow until you approve deliverable.
            </div>
            <div class="quote-actions">
              <button class="btn btn-primary btn-quote" onclick="openUpiModal('${task.id}', ${task.quote_inr})">
                <i data-lucide="shield-check" style="width:14px;"></i> Confirm & Lock Escrow
              </button>
            </div>
          </div>
        `;
      } else if (task.status === 'ESCROW_LOCKED') {
        cardBody = `
          <div class="quote-card" style="border-color: rgba(16, 185, 129, 0.4);">
            <div class="quote-header">
              <span class="quote-title" style="color: var(--accent-upi);">🔒 Escrow Locked (₹${task.quote_inr})</span>
              <span style="font-size:0.75rem; color:var(--text-dim); font-family:var(--font-mono);">${task.escrow_tx_id || 'UPI-HOLD'}</span>
            </div>
            <div class="quote-details">
              Dispatched to active workers. Waiting for a worker to claim and submit proof...
            </div>
          </div>
        `;
      } else if (task.status === 'CLAIMED') {
        cardBody = `
          <div class="quote-card" style="border-color: rgba(6, 182, 212, 0.4);">
            <div class="quote-header">
              <span class="quote-title" style="color: var(--accent-worker);">⚡ In Progress</span>
              <span style="font-size:0.75rem; color:var(--accent-worker);">Worker: ${task.worker?.name || 'Assigned'}</span>
            </div>
            <div class="quote-details">
              Worker is executing the task. You will be notified when deliverable is submitted.
            </div>
          </div>
        `;
      } else if (task.status === 'DELIVERED') {
        cardBody = `
          <div class="deliverable-card">
            <div class="deliverable-header">📦 Deliverable Submitted for Review</div>
            <div class="deliverable-content">
              <strong>Proof Type:</strong> ${escapeHtml(task.deliverable?.proof_type || 'Result')}<br>
              <strong>Result:</strong> ${escapeHtml(task.deliverable?.text || '')}
            </div>
            <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.6rem;">
              Approve to release ₹${task.quote_inr} instantly to ${task.worker?.name}'s UPI (${task.worker?.upi_id}).
            </div>
            <div style="display:flex; gap:0.5rem;">
              <button class="btn btn-primary" onclick="approveTask('${task.id}')">
                <i data-lucide="check" style="width:14px;"></i> Approve & Release ₹${task.quote_inr}
              </button>
              <button class="btn btn-danger" onclick="rejectTask('${task.id}')">
                Request Revision
              </button>
            </div>
          </div>
        `;
      } else if (task.status === 'APPROVED_PAID_OUT') {
        cardBody = `
          <div class="deliverable-card" style="border-color: rgba(16, 185, 129, 0.5); background: rgba(16, 185, 129, 0.05);">
            <div class="deliverable-header" style="color: var(--accent-upi);">✅ Settled & Paid via UPI (₹${task.quote_inr})</div>
            <div class="deliverable-content">
              <strong>Delivered Result:</strong> ${escapeHtml(task.deliverable?.text || '')}
            </div>
            <div style="font-size: 0.72rem; color: var(--accent-upi); font-family: var(--font-mono); margin-top: 4px;">
              Payout Ref: ${task.payout_tx_id || 'UPI-SETTLE-SUCCESS'}
            </div>
          </div>
        `;
      } else if (task.status === 'REVISION_REQUESTED') {
        cardBody = `
          <div class="quote-card" style="border-color: rgba(239, 68, 68, 0.4);">
            <span class="quote-title" style="color: var(--accent-danger);">⚠️ Revision Requested</span>
            <div class="quote-details">Worker notified to update deliverable.</div>
          </div>
        `;
      }

      html += `
        <div class="msg msg-bot">
          ${tierBadge}
          ${cardBody}
          <div class="msg-time">${task.created_at}</div>
        </div>
      `;
    }
  });

  stream.innerHTML = html;
  if (window.lucide) lucide.createIcons();
}

// ----------------- Worker Feed Logic (Pane 2) -----------------
function renderWorkerFeed(tasks) {
  const feedList = document.getElementById('worker-feed-list');
  const activeTasks = tasks.filter(t => ['ESCROW_LOCKED', 'CLAIMED', 'DELIVERED'].includes(t.status));
  document.getElementById('feed-count').textContent = activeTasks.length;

  if (activeTasks.length === 0) {
    feedList.innerHTML = `
      <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-dim); font-size: 0.85rem;">
        <i data-lucide="inbox" style="width: 32px; height: 32px; margin-bottom: 0.5rem; opacity: 0.4;"></i>
        <div>No active escrow-funded jobs waiting.</div>
        <div style="font-size: 0.75rem; margin-top: 4px;">Send a task in the User Chat pane to generate a live job!</div>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  let html = '';
  activeTasks.forEach(task => {
    const isGig = task.tier === 'gig';
    const badgeClass = isGig ? 'badge-gig' : 'badge-expert';
    const tierName = isGig ? 'Gig Task' : 'Expert CA/Legal';

    let actionBtn = '';
    if (task.status === 'ESCROW_LOCKED') {
      actionBtn = `
        <button class="btn btn-primary" style="padding: 0.4rem 0.9rem; font-size: 0.78rem;" onclick="claimTask('${task.id}')">
          <i data-lucide="zap" style="width: 13px;"></i> Claim Task (Earn ₹${task.quote_inr})
        </button>
      `;
    } else if (task.status === 'CLAIMED') {
      actionBtn = `
        <button class="btn btn-quote" style="padding: 0.4rem 0.9rem; font-size: 0.78rem;" onclick="openSubmitModal('${task.id}')">
          <i data-lucide="upload" style="width: 13px;"></i> Submit Proof / Deliver
        </button>
      `;
    } else if (task.status === 'DELIVERED') {
      actionBtn = `
        <span style="font-size: 0.75rem; color: var(--accent-upi); font-weight: 600;">
          ⏳ Submitted · Awaiting Requester Approval
        </span>
      `;
    }

    html += `
      <div class="feed-card">
        <div class="feed-header">
          <div>
            <span class="feed-badge ${badgeClass}">${tierName}</span>
            <span class="feed-badge badge-escrow" style="margin-left: 4px;">Escrow Locked</span>
          </div>
          <div class="feed-payout">₹${task.quote_inr}</div>
        </div>

        <div class="feed-desc">
          <strong>Task:</strong> ${escapeHtml(task.query)}
        </div>

        <div style="font-size: 0.75rem; color: var(--text-muted); background: rgba(0,0,0,0.25); padding: 6px; border-radius: 4px;">
          <em>Reasoning:</em> ${escapeHtml(task.reasoning)}
        </div>

        <div class="feed-meta">
          <span>Est. Time: ~${task.turnaround_mins}m</span>
          ${actionBtn}
        </div>
      </div>
    `;
  });

  feedList.innerHTML = html;
  if (window.lucide) lucide.createIcons();
}

function updateWorkerProfileDisplay() {
  const wSelect = document.getElementById('worker-select');
  const wNameEl = document.getElementById('current-worker-name');
  const wUpiEl = document.getElementById('current-worker-upi');

  if (wSelect.value === 'w_1') {
    wNameEl.textContent = 'Aarav Sharma (Bengaluru)';
    wUpiEl.textContent = 'aarav.gig@okhdfc · Rating: ⭐ 4.94';
  } else if (wSelect.value === 'w_2') {
    wNameEl.textContent = 'Priya Nair, CA Inter (Delhi NCR)';
    wUpiEl.textContent = 'priya.ca@okaxis · Rating: ⭐ 5.0';
  } else {
    wNameEl.textContent = 'Rohan Deshmukh (Pune)';
    wUpiEl.textContent = 'rohan.d@icici · Rating: ⭐ 4.88';
  }
}

// ----------------- Triage Inspector Logs (Pane 3) -----------------
function renderLogs(logs) {
  const tbody = document.getElementById('logs-table-body');
  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-dim); padding:1rem;">No triage logs yet.</td></tr>`;
    return;
  }

  let html = '';
  logs.slice(0, 15).forEach(log => {
    let pillClass = 'pill-ai';
    if (log.tier === 'gig') pillClass = 'pill-gig';
    if (log.tier === 'expert') pillClass = 'pill-expert';

    html += `
      <tr>
        <td style="font-family:var(--font-mono); color:var(--text-dim);">${log.timestamp}</td>
        <td style="max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(log.query)}">
          ${escapeHtml(log.query)}
        </td>
        <td><span class="log-tier-pill ${pillClass}">${log.tier.toUpperCase()}</span></td>
        <td style="font-family:var(--font-mono); font-weight:600; color:var(--text-main);">₹${log.quote_inr}</td>
        <td style="font-family:var(--font-mono); color:var(--accent-upi);">${Math.round(log.confidence * 100)}%</td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

// ----------------- Actions & Escrow API Calls -----------------
function openUpiModal(taskId, amount) {
  CURRENT_TASK_FOR_ESCROW = { id: taskId, amount: amount };
  document.getElementById('upi-modal-amount').textContent = `₹${amount.toFixed(2)}`;
  document.getElementById('upi-modal').classList.add('active');
}

function closeUpiModal() {
  document.getElementById('upi-modal').classList.remove('active');
  CURRENT_TASK_FOR_ESCROW = null;
}

async function lockEscrowForTask(taskId) {
  try {
    const res = await fetch('/api/task/escrow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId })
    });
    const data = await res.json();
    if (data.status === 'success') {
      closeUpiModal();
      showToast(`🔒 UPI Pre-Auth Successful! ₹${data.task.quote_inr} locked in Escrow.`);
      syncState();
    }
  } catch (err) {
    showToast("Escrow lock failed", true);
  }
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
      showToast(`⚡ Task claimed by ${data.task.worker.name}!`);
      syncState();
    }
  } catch (err) {
    showToast("Failed to claim task", true);
  }
}

function openSubmitModal(taskId) {
  document.getElementById('submit-task-id').value = taskId;
  document.getElementById('submit-proof-text').value = '';
  document.getElementById('submit-modal').classList.add('active');
}

function closeSubmitModal() {
  document.getElementById('submit-modal').classList.remove('active');
}

async function submitWorkerProof(taskId, proofType, proofText) {
  try {
    const res = await fetch('/api/worker/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id: taskId,
        proof_type: proofType,
        proof_text: proofText
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      closeSubmitModal();
      showToast("📦 Deliverable submitted! Posted to Requester for approval.");
      syncState();
    }
  } catch (err) {
    showToast("Submission failed", true);
  }
}

async function approveTask(taskId) {
  try {
    const res = await fetch('/api/task/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`🎉 Work Approved! ₹${data.task.quote_inr} instantly paid to worker's UPI!`);
      syncState();
    }
  } catch (err) {
    showToast("Approval failed", true);
  }
}

async function rejectTask(taskId) {
  const reason = prompt("Enter feedback for revision:", "Need clearer confirmation from store owner.");
  if (reason) {
    await fetch('/api/task/reject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId, feedback: reason })
    });
    showToast("Revision requested from worker");
    syncState();
  }
}

// ----------------- Settings & Free Keys -----------------
function openSettingsModal() {
  document.getElementById('settings-modal').classList.add('active');
}

function closeSettingsModal() {
  document.getElementById('settings-modal').classList.remove('active');
}

async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    if (data.has_gemini) {
      document.getElementById('cfg-gemini-key').placeholder = `Configured (${data.gemini_masked})`;
    }
    if (data.has_groq) {
      document.getElementById('cfg-groq-key').placeholder = `Configured (${data.groq_masked || 'Active'})`;
    }
    if (data.has_telegram) {
      document.getElementById('cfg-telegram-token').placeholder = `Configured (${data.telegram_masked})`;
    }
  } catch (err) {}
}

async function saveSettings(e) {
  e.preventDefault();
  const gemini = document.getElementById('cfg-gemini-key').value.trim();
  const groq = document.getElementById('cfg-groq-key').value.trim();
  const telegram = document.getElementById('cfg-telegram-token').value.trim();

  const payload = {};
  if (gemini) payload.GEMINI_API_KEY = gemini;
  if (groq) payload.GROQ_API_KEY = groq;
  if (telegram) payload.TELEGRAM_BOT_TOKEN = telegram;

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === 'success') {
      closeSettingsModal();
      showToast("✅ Settings & API keys updated successfully!");
    }
  } catch (err) {
    showToast("Failed to save settings", true);
  }
}

// ----------------- Toast Utility -----------------
function showToast(message, isError = false) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  if (isError) toast.style.borderColor = 'var(--accent-danger)';
  toast.innerHTML = `
    <i data-lucide="${isError ? 'alert-circle' : 'sparkles'}" style="width:16px; color:${isError ? 'var(--accent-danger)' : 'var(--accent-upi)'}"></i>
    <span>${escapeHtml(message)}</span>
  `;
  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
