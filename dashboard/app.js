const state = { status: null, activityFilter: 'all', focusTimer: null, focusStartedAt: null, selectedAgent: null };
const workspaceStyle = document.createElement('style');
workspaceStyle.textContent = `.agent-workspace-open .command-dock{display:none}.workspace-back{margin-bottom:22px}.workspace-header{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;padding:22px;border:1px solid #3b4250;background:linear-gradient(145deg,#1d2532,#151920);border-radius:var(--radius)}.workspace-header h2{font-size:28px;margin:9px 0 5px}.workspace-header p{margin:0}.workspace-status{display:flex;gap:8px;align-items:center;justify-content:flex-end;flex-wrap:wrap}.workspace-tabs{display:flex;gap:20px;border-bottom:1px solid var(--line);margin-top:24px;padding:0 4px}.workspace-tabs span{padding:10px 2px;color:var(--muted);font:10px 'IBM Plex Mono',monospace}.workspace-tabs .selected{color:var(--amber);border-bottom:2px solid var(--amber)}.agent-chat{min-height:390px;max-height:56vh;overflow:auto;padding:22px 0;display:grid;gap:13px}.chat-message{max-width:min(760px,88%);padding:14px 16px;border:1px solid var(--line);border-radius:10px;background:var(--surface)}.chat-message.user{justify-self:end;background:#252b37;border-color:#465064}.chat-message.agent{justify-self:start;border-left:3px solid var(--cyan)}.chat-message b{display:block;color:var(--cyan);font:10px 'IBM Plex Mono',monospace}.chat-message.user b{color:var(--amber)}.chat-message p{margin:8px 0 0;line-height:1.55;color:var(--text)}.chat-empty{color:var(--muted);font:12px 'IBM Plex Mono',monospace;padding:34px 0}.agent-composer{display:flex;gap:8px;border-top:1px solid var(--line);padding-top:15px}.agent-composer input{flex:1;min-width:0;background:var(--surface-2);border:1px solid var(--line);border-radius:9px;color:var(--text);padding:14px 16px;outline:0}.agent-composer input:focus{border-color:var(--cyan)}.agent-composer button{border:0;border-radius:9px;background:var(--cyan);color:#10201e;padding:0 20px;font-weight:700;font-size:11px}.agent-composer button:disabled{opacity:.55}@media(max-width:760px){.workspace-header{flex-direction:column}.workspace-status{justify-content:flex-start}.agent-chat{min-height:330px}.agent-composer button{padding:0 13px}}`;
document.head.append(workspaceStyle);
const workerModeStyle = document.createElement('style');
workerModeStyle.textContent = '.worker-mode .command-dock{display:none}';
document.head.append(workerModeStyle);
const $ = id => document.getElementById(id);

function escapeHtml(value) {
  const node = document.createElement('div');
  node.textContent = value == null ? '' : String(value);
  return node.innerHTML;
}

function setView(view) {
  document.querySelectorAll('.view').forEach(item => item.classList.toggle('active', item.id === `view-${view}`));
  document.querySelectorAll('.nav-item').forEach(item => item.classList.toggle('active', item.dataset.view === view));
  const labels = { overview: ['OVERVIEW / PERSONAL AI WORKSPACE', 'Good morning, Roy.', 'Your personal AI workspace is ready.'], mission: ['MISSION CONTROL / EXECUTION', 'Mission Control', 'Command, delegate, execute, report.'], agents: ['OPERATIONS / SPECIALISTS', 'AI Agents', 'Six specialists. One shared mission system.'], projects: ['MEMORY / LONG-TERM CONTEXT', 'Projects', 'Long-term entities connected to missions and activity.'], tasks: ['EXECUTION / QUEUE', 'Tasks', 'Every mission is local, visible, and actionable.'], memory: ['MEMORY / LOCAL RECORDS', 'Memory', 'Project memory, command history, and system activity remain on this machine.'], activity: ['OBSERVABILITY / AUDIT', 'Activity', 'A scan-friendly timeline of execution.'], settings: ['SYSTEM / CONFIGURATION', 'Settings', 'Local runtime information and connection boundaries.'] };
  const details = labels[view] || labels.overview;
  $('page-eyebrow').textContent = details[0]; $('page-title').textContent = details[1]; $('page-subtitle').textContent = details[2];
  document.body.classList.remove('nav-open');
  document.body.classList.toggle('worker-mode', view === 'agents');
  if (view !== 'agents' && state.selectedAgent) closeAgentWorkspace();
}

function renderAgents(agents) {
  const cards = agents.map((agent, index) => {
    const working = agent.status === 'working';
    const icon = ['✦', '◌', '□', '∿', '◈', '⌘'][index] || '•';
    const log = agent.log.length ? agent.log[agent.log.length - 1].message : 'Awaiting command';
    return `<article class="agent-card ${index === 0 ? 'featured' : ''}"><div class="agent-card-top"><span class="agent-icon">${icon}</span><span class="agent-ready ${working ? 'working' : ''}">● ${working ? 'WORKING' : 'READY'}</span></div><h3>${escapeHtml(agent.name)}</h3><p>${escapeHtml(agent.description)}</p><div class="agent-activity"><span>${escapeHtml(log)}</span><i class="agent-line ${working ? 'active' : ''}"></i></div><button class="text-button" data-go="mission">Open agent →</button></article>`;
  }).join('');
  $('overview-agents').innerHTML = cards;
  $('agents-grid').innerHTML = cards;
  document.querySelectorAll('#agents-grid .text-button').forEach((button, index) => {
    button.removeAttribute('data-go');
    button.dataset.agentOpen = agents[index].key;
    button.textContent = 'Open workspace →';
  });
}

function renderWorkspaceAgents(agents) {
  const cards = (directory) => agents.map((agent, index) => {
    const working = agent.status === 'working';
    const icon = ['✦', '◌', '□', '∿', '◈', '⌘'][index] || '•';
    const log = agent.log.length ? agent.log[agent.log.length - 1].message : 'Awaiting command';
    const action = directory ? `data-agent-open="${escapeHtml(agent.key)}"` : 'data-go="agents"';
    const label = directory ? 'Open agent →' : 'View agent →';
    return `<article class="agent-card ${index === 0 ? 'featured' : ''}"><div class="agent-card-top"><span class="agent-icon">${icon}</span><span class="agent-ready ${working ? 'working' : ''}">&#9679; ${working ? 'WORKING' : 'READY'}</span></div><h3>${escapeHtml(agent.name)}</h3><p>${escapeHtml(agent.description)}</p><div class="agent-activity"><span>${escapeHtml(log)}</span><i class="agent-line ${working ? 'active' : ''}"></i></div><button class="text-button" ${action}>${label}</button></article>`;
  }).join('');
  $('overview-agents').innerHTML = cards(false);
  $('agents-grid').innerHTML = cards(true);
}

function renderWorkspaceHeader(agent) {
  if (!agent) return;
  const activeTasks = (state.status?.missions || []).filter(mission => {
    const category = String(mission.category || '').toLowerCase();
    return mission.status !== 'completed' && mission.status !== 'failed' &&
      ((agent.key === 'study' && (category === 'acca' || category === 'university')) ||
       (agent.key === 'quant' && category === 'quant finance') ||
       (agent.key === 'developer' && (category === 'programming' || category === 'hackathon')) ||
       mission.assigned_agent === agent.name);
  }).length;
  $('workspace-agent-name').textContent = agent.name;
  $('workspace-agent-description').textContent = agent.description;
  $('workspace-agent-status').textContent = agent.status === 'working' ? 'WORKING' : 'ONLINE';
  $('workspace-agent-work').textContent = agent.status === 'working' ? 'WORKING' : 'IDLE';
  $('workspace-agent-tasks').textContent = activeTasks;
  $('agent-message-input').placeholder = `Message ${agent.name}...`;
}

function renderAgentChat(messages) {
  $('agent-chat').innerHTML = messages.length ? messages.map(message => {
    const role = message.role === 'user' ? 'USER' : state.selectedAgent?.name?.toUpperCase() || 'AGENT';
    const type = message.role === 'user' ? 'user' : 'agent';
    return `<article class="chat-message ${type}"><b>${escapeHtml(role)}</b><p>${escapeHtml(message.content).replaceAll('\n', '<br>')}</p></article>`;
  }).join('') : '<div class="chat-empty">No messages yet. Start a direct conversation with this worker.</div>';
  $('agent-chat').scrollTop = $('agent-chat').scrollHeight;
}

async function openAgentWorkspace(agentKey) {
  try {
    const response = await fetch(`/api/agents/${encodeURIComponent(agentKey)}/chat`);
    const data = await response.json();
    if (data.error) throw new Error(data.error);
    state.selectedAgent = data.agent;
    $('agent-directory').hidden = true;
    $('agent-workspace').hidden = false;
    document.body.classList.add('agent-workspace-open');
    renderWorkspaceHeader(data.agent);
    renderAgentChat(data.messages || []);
  } catch (error) { alert(`Could not open agent workspace: ${error.message}`); }
}

function closeAgentWorkspace() {
  state.selectedAgent = null;
  $('agent-directory').hidden = false;
  $('agent-workspace').hidden = true;
  document.body.classList.remove('agent-workspace-open');
}

async function submitAgentMessage(text) {
  const message = text.trim();
  if (!message || !state.selectedAgent) return;
  $('agent-message-input').value = '';
  $('agent-send-btn').disabled = true;
  $('agent-send-btn').textContent = 'WORKING…';
  try {
    const response = await fetch(`/api/agents/${encodeURIComponent(state.selectedAgent.key)}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message }) });
    const data = await response.json();
    if (data.error) throw new Error(data.error);
    renderAgentChat(data.messages || []);
  } catch (error) { alert(`Could not send message: ${error.message}`); }
  finally { $('agent-send-btn').disabled = false; $('agent-send-btn').innerHTML = 'SEND <span>↗</span>'; refreshStatus(); }
}

function renderMission(data) {
  const mission = data.next_action;
  const analysis = mission && mission.priority_analysis;
  const progress = mission ? Number(mission.progress || 0) : 0;
  $('current-mission').textContent = mission ? mission.title : 'No active missions.';
  $('mission-meta').textContent = mission ? `${mission.category} / ${mission.status.replace('_', ' ').toUpperCase()} / ${mission.priority.toUpperCase()} / ${mission.estimated_minutes || 'Unestimated'} min` : 'Mission Control is waiting for your next command.';
  $('mission-progress-label').textContent = `${progress}%`; $('mission-progress').style.width = `${progress}%`;
  $('assigned-agent').textContent = `ASSIGNED AGENT / ${mission && mission.assigned_agent ? mission.assigned_agent.toUpperCase() : 'UNASSIGNED'}`;
  $('complete-btn').hidden = !mission; $('complete-btn').dataset.id = mission ? mission.id : '';
  $('next-action').textContent = mission ? mission.title : 'No active missions.'; $('next-reason').textContent = analysis ? analysis.reason : 'The priority engine is awaiting stored work.';
  $('next-score').textContent = analysis ? `${analysis.score} / 10` : '-- / 10'; $('execute-next').hidden = !mission; $('execute-next').dataset.command = mission ? `Continue ${mission.title}` : '';
  $('mission-objective').textContent = mission && mission.objective ? mission.objective : 'No objective recorded.'; $('mission-phase').textContent = mission && mission.current_phase ? mission.current_phase : 'Awaiting mission.';
  $('progress-number').textContent = `${progress}%`; $('intelligence-progress').style.width = `${progress}%`; $('intelligence-status').textContent = mission ? mission.status.replace('_', ' ').toUpperCase() : 'NO ACTIVE MISSION';
  $('priority-score').textContent = analysis ? `${analysis.score} / 10` : '-- / 10';
  $('priority-factors').innerHTML = analysis ? [['Urgency', analysis.urgency], ['Impact', analysis.impact], ['Momentum', analysis.momentum], ['Effort', analysis.effort]].map(([label, value]) => `<div><span>${label}</span><b>${value}/10</b></div>`).join('') : 'No priority analysis.';
  const subtasks = mission && mission.subtasks ? mission.subtasks : [];
  $('subtask-list').innerHTML = subtasks.length ? subtasks.map(task => `<div class="subtask ${task.status === 'completed' ? 'done' : ''}"><span>${task.status === 'completed' ? '✓' : '→'}</span>${escapeHtml(task.title)}</div>`).join('') : 'No subtasks recorded.';
  $('focus-mission').textContent = mission ? mission.title : 'No active mission'; $('focus-objective').textContent = mission && mission.objective ? mission.objective : 'No objective recorded.'; $('focus-next-action').textContent = mission ? (mission.current_phase || mission.title) : 'Awaiting mission'; $('focus-progress-fill').style.width = `${progress}%`;
}

function renderActivity(activity) {
  const items = activity.filter(item => { const text = `${item.agent} ${item.message}`.toLowerCase(); if (state.activityFilter === 'all') return true; if (state.activityFilter === 'missions') return text.includes('mission'); if (state.activityFilter === 'agents') return text.includes('agent'); if (state.activityFilter === 'errors') return text.includes('error'); return text.includes('mission control') || text.includes('system'); }).slice(0, 15);
  const html = items.length ? items.map(item => `<div class="activity-line"><time>${new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time><strong>${escapeHtml(item.agent).toUpperCase()}</strong><span>${escapeHtml(item.message)}</span></div>`).join('') : 'No activity recorded.';
  $('activity-list').innerHTML = html; $('activity-page-list').innerHTML = html;
}

function renderProjects(projects) {
  const html = projects.length ? projects.map(project => `<button class="project-card" data-project-id="${project.id}"><div class="project-card-head"><h3>${escapeHtml(project.name)}</h3><span>${escapeHtml(project.status).toUpperCase()}</span></div><p>${escapeHtml(project.description || project.objective || 'No description recorded.')}</p><div class="project-meta">${escapeHtml(project.technologies || 'TECH STACK NOT RECORDED')}</div><small>NEXT ACTION / ${escapeHtml(project.next_action || 'Not recorded')}</small></button>`).join('') : 'No projects recorded.';
  $('projects-grid').innerHTML = html;
  document.querySelectorAll('[data-project-id]').forEach(item => item.addEventListener('click', async () => { const response = await fetch(`/api/projects/${item.dataset.projectId}`); const detail = await response.json(); if (!detail.error) alert(`${detail.project.name}\n\n${detail.project.objective || 'No objective recorded.'}\n\nMissions: ${detail.missions.length}\nNext action: ${detail.project.next_action || 'Not recorded'}`); }));
}

function renderTasks(missions) {
  $('tasks-list').innerHTML = missions.length ? missions.map(mission => {
    const status = String(mission.status || 'queued');
    const actions = mission.category !== 'Programming' ? '' : ({
      queued: `<button class="outline-button small-button" data-mission-action="analyze" data-mission-id="${mission.id}">Analyze</button>`,
      analyzing: '<small>Inspecting architecture...</small>',
      planned: `<button class="outline-button small-button" data-mission-action="plan" data-mission-id="${mission.id}">View Plan</button>`,
      awaiting_approval: `<button class="outline-button small-button" data-mission-action="plan" data-mission-id="${mission.id}">View Plan</button><button class="amber-button small-button" data-mission-action="approve" data-mission-id="${mission.id}">Approve Implementation</button>`,
      implementing: `<button class="amber-button small-button" data-mission-action="implement" data-mission-id="${mission.id}">Start Implementation</button>`,
      validating: '<small>Validation running...</small>',
      completed: `<button class="outline-button small-button" data-mission-action="results" data-mission-id="${mission.id}">View Results</button>`,
      failed: `<button class="outline-button small-button" data-mission-action="results" data-mission-id="${mission.id}">View Results</button><button class="outline-button small-button" data-mission-action="analyze" data-mission-id="${mission.id}">Analyze Again</button>`,
    }[status] || '');
    return `<article class="task-row"><div><span class="task-category">${escapeHtml(mission.category)}</span><h3>${escapeHtml(mission.title)}</h3><p>${escapeHtml(mission.objective || 'No objective recorded.')}</p><small>${escapeHtml(mission.current_phase || status).toUpperCase()}</small></div><div class="task-progress"><strong>${mission.progress || 0}%</strong><div class="progress-track"><div style="width:${mission.progress || 0}%"></div></div><small>${escapeHtml(status).replaceAll('_', ' ').toUpperCase()}</small><div class="task-actions">${actions}</div></div></article>`;
  }).join('') : 'No active missions.';
}

function renderSystem(data) {
  const system = data.system || {}; const count = data.agents.length; const active = (data.active_missions || []).length; const completed = (data.completed_today || []).length;
  $('overview-agent-count').textContent = count; $('stat-agents').textContent = count; $('stat-missions').textContent = active; $('stat-completed').textContent = completed;
  $('system-facts').innerHTML = `Agents: ${count} / ${count}<br>Active missions: ${active}<br>Completed today: ${completed}<br>Memory: ${(system.memory || 'inactive').toUpperCase()}`;
  $('top-system').textContent = system.online ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'; $('top-model').textContent = system.local_model || 'fallback API'; $('sidebar-model').textContent = system.online ? 'READY' : 'OFFLINE'; $('settings-model').textContent = system.local_model || 'fallback API'; $('settings-network').textContent = system.lan_addresses && system.lan_addresses.length ? 'LAN + LOCALHOST' : 'LOCALHOST'; $('settings-server').textContent = `${location.hostname}:${location.port || '80'}`;
  renderMobileAccess(system.mobile_url, system.lan_addresses || []);
  $('memory-project-count').textContent = data.projects.length; $('memory-command-count').textContent = data.history.length; $('memory-activity-count').textContent = data.activity.length;
}

function renderMobileAccess(url, addresses) {
  const urlElement = $('mobile-access-url');
  const message = $('mobile-access-message');
  const copyButton = $('copy-mobile-url');
  const qr = $('mobile-access-qr');
  const empty = $('mobile-access-qr-empty');
  if (!url) {
    urlElement.textContent = 'No LAN address detected';
    message.textContent = 'Connect this computer to Wi-Fi or Ethernet, then refresh Settings.';
    copyButton.disabled = true;
    qr.hidden = true;
    empty.hidden = false;
    return;
  }
  urlElement.textContent = url;
  message.textContent = `Available on this private network${addresses.length > 1 ? ` (${addresses.length} addresses detected)` : ''}. Scan the QR code or copy the URL.`;
  copyButton.disabled = false;
  copyButton.dataset.url = url;
  qr.src = `/api/network/qr?url=${encodeURIComponent(url)}`;
  qr.hidden = false;
  empty.hidden = true;
}

async function refreshStatus() {
  try { const response = await fetch('/api/status'); state.status = await response.json(); renderAgents(state.status.agents); renderMission(state.status); renderActivity(state.status.activity || []); renderProjects(state.status.projects || []); renderTasks(state.status.missions || []); renderSystem(state.status); if (state.selectedAgent) renderWorkspaceHeader(state.status.agents.find(agent => agent.key === state.selectedAgent.key) || state.selectedAgent); } catch (error) { $('top-system').textContent = 'SYSTEM OFFLINE'; console.error(error); }
}

async function refreshStatus() {
  try {
    const [statusResponse, directoryResponse] = await Promise.all([fetch('/api/status'), fetch('/api/agents')]);
    state.status = await statusResponse.json();
    const directory = await directoryResponse.json();
    const agents = directory.agents || state.status.agents;
    renderWorkspaceAgents(agents);
    renderMission(state.status);
    renderActivity(state.status.activity || []);
    renderProjects(state.status.projects || []);
    renderTasks(state.status.missions || []);
    renderSystem(state.status);
    if (state.selectedAgent) renderWorkspaceHeader(agents.find(agent => agent.key === state.selectedAgent.key) || state.selectedAgent);
  } catch (error) { $('top-system').textContent = 'SYSTEM OFFLINE'; console.error(error); }
}

function appendMessage(role, text, agent) { const feed = document.querySelector('.command-dock'); const node = document.createElement('div'); node.className = `toast-message ${role}`; node.innerHTML = role === 'agent' ? `<b>${escapeHtml(agent || 'AGENT')}</b><span>${escapeHtml(text)}</span>` : `<b>COMMAND</b><span>${escapeHtml(text)}</span>`; feed.before(node); setTimeout(() => node.remove(), 10000); }
async function submitCommand(text) { const command = text.trim(); if (!command) return; appendMessage('user', command); $('task-input').value = ''; $('send-btn').disabled = true; $('send-btn').innerHTML = 'EXECUTING…'; try { const response = await fetch('/api/task', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: command }) }); const data = await response.json(); (data.results || []).forEach(result => appendMessage('agent', result.reply, result.agent)); } catch (error) { appendMessage('agent', 'Could not reach the local server.', 'SYSTEM'); } finally { $('send-btn').disabled = false; $('send-btn').innerHTML = 'EXECUTE <span>↗</span>'; refreshStatus(); } }

async function runMissionAction(action, missionId) {
  const paths = { analyze: `/api/missions/${missionId}/analyze`, approve: `/api/missions/${missionId}/approve`, implement: `/api/missions/${missionId}/implement` };
  if (action === 'plan' || action === 'results') {
    const response = await fetch(`/api/missions/${missionId}/${action}`);
    const data = await response.json();
    alert(action === 'plan' ? (data.plan || 'No plan recorded.') : `${data.implementation_result || 'No implementation result recorded.'}\n\n${data.validation_result || 'No validation result recorded.'}`);
    return;
  }
  const options = { method: 'POST', headers: { 'Content-Type': 'application/json' } };
  if (action === 'approve') options.body = JSON.stringify({ approved_by: 'user', changes: [] });
  const response = await fetch(paths[action], options);
  const data = await response.json();
  if (data.error) alert(data.error);
  refreshStatus();
}

$('nav').addEventListener('click', event => { const item = event.target.closest('.nav-item'); if (!item) return; if (item.dataset.view === 'agents' && state.selectedAgent) closeAgentWorkspace(); setView(item.dataset.view); });
document.addEventListener('click', event => { const target = event.target.closest('[data-go]'); if (target) setView(target.dataset.go); });
document.addEventListener('click', event => { const target = event.target.closest('[data-agent-open]'); if (target) openAgentWorkspace(target.dataset.agentOpen); });
document.addEventListener('click', event => { const target = event.target.closest('[data-mission-action]'); if (target) runMissionAction(target.dataset.missionAction, target.dataset.missionId); });
$('mobile-menu').addEventListener('click', () => document.body.classList.toggle('nav-open'));
$('composer').addEventListener('submit', event => { event.preventDefault(); submitCommand($('task-input').value); });
$('agent-composer').addEventListener('submit', event => { event.preventDefault(); submitAgentMessage($('agent-message-input').value); });
$('agent-workspace-back').addEventListener('click', closeAgentWorkspace);
document.querySelectorAll('.suggestions button').forEach(button => button.addEventListener('click', () => { $('task-input').value = button.dataset.command; $('task-input').focus(); }));
document.querySelector('[data-focus-command]').addEventListener('click', () => { setView('mission'); $('task-input').focus(); });
$('execute-next').addEventListener('click', event => submitCommand(event.currentTarget.dataset.command));
$('complete-btn').addEventListener('click', async event => { await fetch(`/api/missions/${event.currentTarget.dataset.id}/complete`, { method: 'POST' }); refreshStatus(); });
$('briefing-btn').addEventListener('click', async () => { const response = await fetch('/api/briefing'); const data = await response.json(); appendMessage('agent', data.briefing, 'MISSION CONTROL'); });
document.querySelectorAll('#activity-filters button').forEach(button => button.addEventListener('click', () => { state.activityFilter = button.dataset.filter; document.querySelectorAll('#activity-filters button').forEach(item => item.classList.toggle('selected', item === button)); renderActivity(state.status ? state.status.activity || [] : []); }));
$('focus-btn').addEventListener('click', () => { if (!state.status || !state.status.next_action) return; state.focusStartedAt = Date.now(); document.body.classList.add('focus-mode'); clearInterval(state.focusTimer); state.focusTimer = setInterval(() => { const seconds = Math.floor((Date.now() - state.focusStartedAt) / 1000); $('focus-timer').textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`; }, 1000); });
$('focus-complete').addEventListener('click', async () => { const mission = state.status && state.status.next_action; if (mission) await fetch(`/api/missions/${mission.id}/complete`, { method: 'POST' }); closeFocus(); refreshStatus(); });
$('focus-skip').addEventListener('click', async () => { const mission = state.status && state.status.next_action; if (mission) await fetch(`/api/missions/${mission.id}/status`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'paused' }) }); closeFocus(); refreshStatus(); });
$('focus-replan').addEventListener('click', () => { closeFocus(); $('task-input').value = 'Replan my current mission'; $('task-input').focus(); });
$('focus-exit').addEventListener('click', closeFocus); document.addEventListener('keydown', event => { if (event.key === 'Escape') closeFocus(); });
$('copy-mobile-url').addEventListener('click', async event => { const url = event.currentTarget.dataset.url; if (!url) return; try { await navigator.clipboard.writeText(url); event.currentTarget.textContent = 'Copied'; setTimeout(() => { event.currentTarget.textContent = 'Copy URL'; }, 1500); } catch { event.currentTarget.textContent = 'Copy failed'; } });
function closeFocus() { document.body.classList.remove('focus-mode'); clearInterval(state.focusTimer); }

setView('overview'); refreshStatus(); setInterval(refreshStatus, 5000);
