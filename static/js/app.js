const API = {
  stats:     '/api/stats',
  logs:      '/api/logs',
  accounts:  '/api/accounts',
  files:     '/api/files',
  generate:  '/api/generate',
  stop:      '/api/stop',
  clearLogs: '/api/clear_logs',
};

const state = {
  currentSection: 'dashboard',
  lastLogIdx: 0,
  accounts: [],
  accountsPage: 1,
  accountsPerPage: 50,
  accountsSearch: '',
  accountsFilter: 'all',
  jobActive: false,
  jobType: null,
  allLogs: [],
};

const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

function spawnPetals() {
  const container = $('petals');
  const count = 20;
  for (let i = 0; i < count; i++) {
    const p = document.createElement('div');
    p.className = 'petal';
    p.style.left = Math.random() * 100 + '%';
    p.style.animationDuration = (12 + Math.random() * 14) + 's';
    p.style.animationDelay = (-Math.random() * 20) + 's';
    p.style.transform = `scale(${0.4 + Math.random() * 0.7})`;
    container.appendChild(p);
  }
}

const PAGE_META = {
  dashboard: { title: 'Dashboard',  sub: 'Overview of your operation' },
  generate:  { title: 'Generate',   sub: 'Create new accounts with auto-activation' },
  accounts:  { title: 'Accounts',   sub: 'Browse every generated account' },
  logs:      { title: 'Live Logs',  sub: 'Real-time engine activity' },
  files:     { title: 'Files',      sub: 'Download output files' },
};

function navigate(section) {
  if (!PAGE_META[section]) return;
  state.currentSection = section;
  $$('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.section === section));
  $$('.section').forEach(s => s.classList.toggle('active', s.id === `section-${section}`));
  const meta = PAGE_META[section];
  if (meta) {
    $('page-title').textContent = meta.title;
    $('page-sub').textContent   = meta.sub;
  }
  if (section === 'accounts') loadAccounts();
  if (section === 'files')    loadFiles();
}

$$('.nav-item').forEach(n => n.addEventListener('click', () => navigate(n.dataset.section)));
document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-section]');
  if (el && !el.classList.contains('nav-item')) {
    e.preventDefault();
    navigate(el.dataset.section);
  }
});

function toast(msg, type = 'ok') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  $('toast-container').appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateX(30px)';
    el.style.transition = 'all 0.3s ease';
    setTimeout(() => el.remove(), 300);
  }, 3500);
}

function fmt(n) { return (n ?? 0).toLocaleString(); }
function fmtSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}
function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[c]));
}

async function pollStats() {
  try {
    const r = await fetch(API.stats, { cache: 'no-store' }); // <-- Added cache: 'no-store'
    const d = await r.json();
    updateStats(d);
  } catch (e) {}
}

function updateStats(d) {
  $('tb-generated').textContent = fmt(d.success_count);
  $('tb-activated').textContent = fmt(d.activated_count);
  $('dash-generated').textContent = fmt(d.success_count);
  $('dash-activated').textContent = fmt(d.activated_count);
  $('dash-total').textContent     = fmt(d.total_accounts);

  state.jobActive = d.job_active;
  state.jobType   = d.job_type;

  if (d.job_active) {
    $('job-indicator').style.display = 'flex';
    $('job-indicator-text').textContent = d.job_type === 'generate' ? 'Generating…' : 'Activating…';
    $('dash-status').textContent = (d.job_type === 'generate' ? 'GENERATING' : 'ACTIVATING');
  } else {
    $('job-indicator').style.display = 'none';
    $('dash-status').textContent = 'IDLE';
  }

  const dashProgress = $('dash-progress-card');
  const genProgress  = $('gen-progress-card');

  if (d.job_active && d.job_type === 'generate') {
    dashProgress.style.display = 'block';
    genProgress.style.display  = 'block';

    const pct = d.target > 0 ? (d.success_count / d.target) * 100 : 0;
    $('progress-title').textContent = 'Generating accounts…';
    $('progress-sub').textContent   = `${fmt(d.success_count)} / ${fmt(d.target)}`;
    $('progress-pct').textContent   = pct.toFixed(1) + '%';
    $('progress-fill').style.width  = Math.min(100, pct) + '%';

    $('gen-progress-sub').textContent     = `${fmt(d.success_count)} / ${fmt(d.target)}`;
    $('gen-progress-pct').textContent     = pct.toFixed(1) + '%';
    $('gen-progress-fill').style.width    = Math.min(100, pct) + '%';
    $('gen-progress-region').textContent  = `Region: ${d.region || '—'}`;
    $('gen-progress-elapsed').textContent = `${d.elapsed.toFixed(1)}s elapsed`;
  } else {
    dashProgress.style.display = 'none';
    genProgress.style.display  = 'none';
  }

  $('gen-submit').disabled = d.job_active;
}

async function pollLogs() {
  try {
    const r = await fetch(`${API.logs}?since=${state.lastLogIdx}`, { cache: 'no-store' }); // <-- Added cache: 'no-store'
    const d = await r.json();
    if (d.logs && d.logs.length) {
      d.logs.forEach(l => {
        state.allLogs.push(l);
        appendLogToView(l);
      });
      state.lastLogIdx = d.total;
      if (state.allLogs.length > 3000) {
        state.allLogs = state.allLogs.slice(-3000);
      }
      updateRecentActivity();
    }
  } catch (e) {}
}

const LOG_ICONS = {
  ok: '✿', err: '✖', info: '❀', warn: '⚠',
  gen: '✿', act: '⚡', angel: '👑', bd: '🇧🇩', account: '❁',
};

function appendLogToView(l) {
  const view = $('log-view');
  const empty = view.querySelector('.log-empty');
  if (empty) empty.remove();

  const row = document.createElement('div');
  row.className = `log-row log-${l.level}`;
  row.innerHTML =
    `<span class="log-ts">[${l.ts}]</span>` +
    `<span class="log-lvl">${LOG_ICONS[l.level] || '•'}</span>` +
    `<span class="log-msg">${escapeHtml(l.msg)}</span>`;

  const atBottom = view.scrollTop + view.clientHeight >= view.scrollHeight - 40;
  view.appendChild(row);
  if (atBottom) view.scrollTop = view.scrollHeight;

  while (view.children.length > 1000) view.removeChild(view.firstChild);
}

function updateRecentActivity() {
  const recent = state.allLogs.slice(-8).reverse();
  const box = $('dash-recent-log');
  if (!recent.length) {
    box.innerHTML = '<div class="mini-log-empty">No activity yet. Start by generating accounts.</div>';
    return;
  }
  box.innerHTML = recent.map(l => `
    <div class="mini-log-row">
      <span class="mini-log-time">${l.ts}</span>
      <span class="mini-log-msg">${LOG_ICONS[l.level] || '•'} ${escapeHtml(l.msg)}</span>
    </div>
  `).join('');
}

function setupPresetButtons(groupId, inputId) {
  const group = $(groupId);
  const input = $(inputId);
  if (!group || !input) return;

  group.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      const val = btn.dataset.value;
      if (val === 'custom') {
        input.focus();
        input.select();
        return;
      }
      group.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      input.value = val;
    });
  });

  input.addEventListener('input', () => {
    group.querySelectorAll('button').forEach(b => {
      b.classList.toggle('active', b.dataset.value === input.value && b.dataset.value !== 'custom');
    });
  });
}

setupPresetButtons('preset-count', 'gen-target');

$('gen-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const target  = parseInt($('gen-target').value, 10);
  const workers = parseInt($('gen-workers').value, 10);
  const region  = $('gen-region').value;
  const prefix  = $('gen-prefix').value.trim() || 'SARKER';
  const password = $('gen-password').value.trim() || 'MM388401';

  // 🛑 HARD LIMIT LOCK (Client-Side)
  if (!target || target < 1) return toast('Enter a valid account count', 'err');
  if (target > 100) return toast('🛑 Safety Limit: Maximum 100 accounts per batch allowed!', 'err');
  
  if (!workers || workers < 1) return toast('Enter a valid worker count', 'err');
  if (workers > 100) return toast('🛑 Safety Limit: Maximum 100 workers allowed!', 'err');

  const btn = $('gen-submit');
  btn.disabled = true;
  btn.textContent = '⏳ Starting…';

  try {
    const r = await fetch(API.generate, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, workers, region, prefix, password }),
    });
    const d = await r.json();
    if (d.ok) {
      toast(`Generation started — ${fmt(target)} accounts`, 'ok');
    } else {
      toast(d.error || 'Failed to start', 'err');
    }
  } catch (e) {
    toast('Network error: ' + e.message, 'err');
  } finally {
    btn.disabled = false;
    btn.textContent = '▶ Start Generation';
  }
});

$('btn-stop').addEventListener('click', async () => {
  if (!confirm('Stop the current job?')) return;
  try {
    await fetch(API.stop, { method: 'POST' });
    toast('Stop requested', 'warn');
  } catch (e) {}
});

async function loadAccounts() {
  try {
    const r = await fetch(API.accounts, { cache: 'no-store' }); // <-- Added cache: 'no-store'
    const accounts = await r.json();
    state.accounts = accounts || [];
    state.accountsPage = 1;
    renderAccounts();
  } catch (e) {}
}

function renderAccounts() {
  const tbody = $('accounts-tbody');
  const pag   = $('accounts-pagination');
  const count = $('accounts-count');

  let filtered = state.accounts;
  if (state.accountsFilter === 'activated') filtered = filtered.filter(a => a.activated);
  if (state.accountsFilter === 'pending')   filtered = filtered.filter(a => !a.activated);

  const q = state.accountsSearch.toLowerCase().trim();
  if (q) {
    filtered = filtered.filter(a =>
      String(a.name || '').toLowerCase().includes(q) ||
      String(a.account_id || '').toLowerCase().includes(q) ||
      String(a.uid || '').toLowerCase().includes(q)
    );
  }

  count.textContent = `${fmt(state.accounts.length)} total · ${fmt(filtered.length)} shown`;

  const per = state.accountsPerPage;
  const totalPages = Math.max(1, Math.ceil(filtered.length / per));
  if (state.accountsPage > totalPages) state.accountsPage = totalPages;

  const start = (state.accountsPage - 1) * per;
  const page  = filtered.slice(start, start + per).reverse();

  if (!page.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-row">No accounts match the filter.</td></tr>';
  } else {
    tbody.innerHTML = page.map((a, i) => {
      const idx = start + page.length - i;
      const badge = a.activated
        ? '<span class="badge ok">ACTIVATED</span>'
        : '<span class="badge act">PENDING</span>';
      // আগের কোড: <td>${escapeHtml(a.uid || '-')}</td>
      // নতুন কোড (Copy Button সহ):
      return `
        <tr>
          <td>${idx}</td>
          <td>${escapeHtml(a.name || '-')}</td>
          <td>${escapeHtml(a.account_id || '-')}</td>
          <td>
            ${escapeHtml(a.uid || '-')}
            <button class="copy-btn" onclick="copyToClipboard('${a.uid}')" title="Copy UID">📋</button>
          </td>
          <td>
            <code style="font-family:var(--mono);font-size:11px;color:var(--text-dim)">${escapeHtml((a.password || '').slice(0, 14))}…</code>
            <button class="copy-btn" onclick="copyToClipboard('${a.password}')" title="Copy Password">📋</button>
          </td>
          <td>${escapeHtml(a.region || 'BD')}</td>
          <td>${badge}</td>
        </tr>
      `;
    }).join('');
  }

  pag.innerHTML = '';
  const maxButtons = 7;
  let startPage = Math.max(1, state.accountsPage - 3);
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);

  if (state.accountsPage > 1) {
    const b = document.createElement('button');
    b.textContent = '←';
    b.onclick = () => { state.accountsPage--; renderAccounts(); };
    pag.appendChild(b);
  }
  for (let p = startPage; p <= endPage; p++) {
    const b = document.createElement('button');
    b.textContent = p;
    if (p === state.accountsPage) b.classList.add('active');
    b.onclick = () => { state.accountsPage = p; renderAccounts(); };
    pag.appendChild(b);
  }
  if (state.accountsPage < totalPages) {
    const b = document.createElement('button');
    b.textContent = '→';
    b.onclick = () => { state.accountsPage++; renderAccounts(); };
    pag.appendChild(b);
  }
}

$('accounts-search').addEventListener('input', (e) => {
  state.accountsSearch = e.target.value;
  state.accountsPage = 1;
  renderAccounts();
});
$('accounts-filter').addEventListener('change', (e) => {
  state.accountsFilter = e.target.value;
  state.accountsPage = 1;
  renderAccounts();
});

async function loadFiles() {
  try {
    const r = await fetch(API.files, { cache: 'no-store' }); // <-- Added cache: 'no-store'
    const files = await r.json();
    const list = $('files-list');
    if (!files || !files.length) {
      list.innerHTML = '<div class="files-empty">No files yet. Generate accounts first.</div>';
      return;
    }
    list.innerHTML = files.map(f => `
      <div class="file-row">
        <div class="file-info">
          <div class="file-icon">${f.name.endsWith('.csv') ? '📊' : '📄'}</div>
          <div>
            <div class="file-name">${escapeHtml(f.name)}</div>
            <div class="file-meta">${fmtSize(f.size)} · ${new Date(f.modified * 1000).toLocaleString()}</div>
          </div>
        </div>
        <a class="btn btn-secondary btn-sm" href="/api/download/${encodeURIComponent(f.name)}">⬇ Download</a>
      </div>
    `).join('');
  } catch (e) {}
}

$('logs-clear').addEventListener('click', async () => {
  try {
    await fetch(API.clearLogs, { method: 'POST' });
    state.allLogs = [];
    state.lastLogIdx = 0;
    $('log-view').innerHTML = '<div class="log-empty">Log cleared.</div>';
    toast('Logs cleared', 'ok');
  } catch (e) {}
});

/* ══════════════════════════════════════════════════════════
   CUSTOM DROPDOWN LOGIC
   ══════════════════════════════════════════════════════════ */
function initCustomDropdown(dropdownId) {
  const dropdown = $(dropdownId);
  if (!dropdown) return;
  
  const trigger = dropdown.querySelector('.dropdown-trigger');
  const menu = dropdown.querySelector('.dropdown-menu');
  const items = dropdown.querySelectorAll('.dropdown-item');
  const hiddenInput = dropdown.querySelector('input[type="hidden"]');
  const selectedText = dropdown.querySelector('.selected-text');

  // Toggle menu
  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    // Close other dropdowns
    $$('.custom-dropdown').forEach(d => {
      if (d !== dropdown) d.classList.remove('open');
    });
    dropdown.classList.toggle('open');
  });

  // Select item
  items.forEach(item => {
    item.addEventListener('click', (e) => {
      e.stopPropagation();
      
      // Update active state
      items.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      
      // Update hidden input value
      hiddenInput.value = item.dataset.value;
      
      // ✅ Trigger change event so the filter logic works
      hiddenInput.dispatchEvent(new Event('change'));
      
      // Update trigger text (Keep flags if they exist)
      selectedText.innerHTML = item.innerHTML;
      
      // Close menu
      dropdown.classList.remove('open');
    });
  });
}

// Close dropdowns when clicking outside
document.addEventListener('click', () => {
  $$('.custom-dropdown').forEach(d => d.classList.remove('open'));
});

// Initialize the dropdowns on page load
document.addEventListener('DOMContentLoaded', () => {
  initCustomDropdown('custom-region');
  initCustomDropdown('custom-workers');
  initCustomDropdown('custom-filter'); // ✅ নতুন যোগ করা লাইন
});

document.addEventListener('DOMContentLoaded', () => {
  spawnPetals();
  navigate('dashboard');

  pollStats();
  pollLogs();
  loadFiles();

  setInterval(pollStats, 1000);
  setInterval(pollLogs, 600);

  setInterval(() => {
    if (state.currentSection === 'accounts') loadAccounts();
    if (state.currentSection === 'files')    loadFiles();
  }, 3000);

  setInterval(() => {
    if (state.currentSection === 'dashboard') updateRecentActivity();
  }, 1500);
});

// ✅ Copy to Clipboard Function
window.copyToClipboard = function(text) {
  if (!text || text === 'undefined') return;
  navigator.clipboard.writeText(text).then(() => {
    toast('Copied: ' + text, 'ok');
  }).catch(err => {
    toast('Copy failed', 'err');
  });
};