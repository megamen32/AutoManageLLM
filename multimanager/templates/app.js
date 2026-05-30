
let S = { accs: [], active: {}, sel: null, progs: [], lang: navigator.language.startsWith('ru') ? 'ru' : 'en' };
const PI = { 'claude-code': 'C', 'claude-desktop': 'D', 'codex': 'X', 'opencode': 'O', 'cline': 'L', 'roo-code': 'R' };

const L = {
  en: {
    accounts: 'Accounts', skills: 'Skills', mcp: 'MCP Servers', programs: 'Programs', settings: 'Settings',
    running: 'Running',
    import: 'Import', from_folder: 'From Folder', sync_all: 'Sync All', refresh: 'Refresh', add: 'Add',
    rename: 'Rename', delete: 'Delete', select_account: 'Select an account',
    new_account: 'New Account', name: 'Name', base_url: 'Base URL', model: 'Model', cancel: 'Cancel', create: 'Create',
    add_mcp_server: 'Add MCP Server', args_comma: 'Args (comma)',
    no_accounts: 'No accounts. Click Import.',
    apply_to: 'Apply to', write_account: '(write account to program)', all: 'All', none: 'None', apply: 'Apply',
    no_skills: 'No skills in master yet.', click_import: 'Click to import all skills →',
    usage: 'Usage', backup_now: 'Backup Now', snapshot: 'Snapshot', shutdown: 'Shutdown',
    auto_backup: 'Auto Backup', before_changes: 'Before applying changes', history: 'History',
    versions_saved: 'versions saved on each change', raw_config: 'Raw config', no_history: 'No history yet', loading: 'Loading...',
    restore: 'Restore',
    name_required: 'Name required', nothing_selected: 'Nothing selected', synced: 'synced', errors: 'errors',
    enter_folder: 'Enter folder path:', new_name: 'New name:', delete_confirm: 'Delete this account?',
    select_programs: 'Select programs',
    default_model: 'default', active: 'Active', left: 'left', expired: 'expired', h: 'h',
    config: 'Config', file: 'File', provider: 'Provider', email: 'Email', plan: 'Plan',
    api_key: 'API Key', source: 'Source', token_expires: 'Token expires',
    refresh_ok: 'refresh &#10003;', no_refresh: 'no refresh',
    snapshot_done: 'Snapshot: {0} files', all_synced: 'All synced', done: 'Done',
    imported: 'Imported: {0}', no_new_skills: 'No new skills', created: 'Created: {0}',
    usage_refreshed: 'Usage refreshed', renamed: 'Renamed', deleted: 'Deleted',
    shutting_down: 'Shutting down', error: 'Error',
    no_refresh_token: 'no refresh', token: 'token',
    source_file: 'Source file', refresh_token: 'Refresh token', token_hours_left: 'Token: {0}h left',
    auto_import: 'Auto Import', from_file: 'From File...',
    history: 'History', version: 'version', versions: 'versions',
    diff: 'diff', vs_current: 'vs current', vs_previous: 'vs previous', close: 'Close',
  },
  ru: {
    accounts: 'Аккаунты', skills: 'Скиллы', mcp: 'MCP Серверы', programs: 'Программы', settings: 'Настройки',
    running: 'Работает',
    import: 'Импорт', from_folder: 'Из папки', sync_all: 'Синхр. все', refresh: 'Обновить', add: 'Добавить',
    rename: 'Переимен.', delete: 'Удалить', select_account: 'Выберите аккаунт',
    new_account: 'Новый аккаунт', name: 'Имя', base_url: 'Base URL', model: 'Модель', cancel: 'Отмена', create: 'Создать',
    add_mcp_server: 'Добавить MCP сервер', args_comma: 'Аргументы (через запятую)',
    no_accounts: 'Нет аккаунтов. Нажмите Импорт.',
    apply_to: 'Применить к', write_account: '(записать в программу)', all: 'Все', none: 'Ничего', apply: 'Применить',
    no_skills: 'В master нет скиллов.', click_import: 'Нажмите, чтобы импортировать →',
    usage: 'Использование', backup_now: 'Бекап', snapshot: 'Снимок', shutdown: 'Выключить',
    auto_backup: 'Автобекап', before_changes: 'Перед изменениями', history: 'История',
    versions_saved: 'версии сохраняются', raw_config: 'Конфиг', no_history: 'Истории нет', loading: 'Загрузка...',
    restore: 'Восстановить',
    name_required: 'Имя обязательно', nothing_selected: 'Ничего не выбрано', synced: 'синхр.', errors: 'ошибок',
    enter_folder: 'Путь к папке:', new_name: 'Новое имя:', delete_confirm: 'Удалить этот аккаунт?',
    select_programs: 'Выберите программы',
    default_model: 'по умолч.', active: 'Активен', left: 'осталось', expired: 'истёк', h: 'ч',
    config: 'Конфиг', file: 'Файл', provider: 'Провайдер', email: 'Email', plan: 'План',
    api_key: 'API Key', source: 'Источник', token_expires: 'Токен истекает',
    refresh_ok: 'обновление &#10003;', no_refresh: 'без обновления',
    snapshot_done: 'Снимок: {0} файлов', all_synced: 'Всё синхронизировано', done: 'Готово',
    imported: 'Импортировано: {0}', no_new_skills: 'Новых скиллов нет', created: 'Создан: {0}',
    usage_refreshed: 'Использование обновлено', renamed: 'Переименовано', deleted: 'Удалено',
    shutting_down: 'Выключение...', error: 'Ошибка',
    no_refresh_token: 'без обновления', token: 'токен',
    source_file: 'Файл источника', refresh_token: 'Обновить токен', token_hours_left: 'Токен: {0}ч осталось',
    auto_import: 'Авто-импорт', from_file: 'Из файла...',
    history: 'История', version: 'версия', versions: 'версий',
    diff: 'дифф', vs_current: 'с текущим', vs_previous: 'с предыдущей', close: 'Закрыть',
  }
};

function __(k, ...a) { let s = (L[S.lang] || L.en)[k]; if (s === void 0) s = k; a.forEach((v, i) => s = s.replace(new RegExp('\\{' + i + '\\}', 'g'), v)); return s }

function applyLang() { document.querySelectorAll('[data-l]').forEach(el => { const k = el.dataset.l; const v = __(k); if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.placeholder = v; else el.innerHTML = v }) }
function setLang(l) { S.lang = l; document.getElementById('lang-sw').value = l; applyLang() }

function go(p) { document.querySelectorAll('.pg').forEach(e => e.classList.remove('on')); document.getElementById('pg-' + p).classList.add('on'); document.querySelectorAll('.ni').forEach(n => n.classList.toggle('on', n.dataset.p === p)); if (p === 'skills') loadSkills(); if (p === 'mcp') loadMcp(); if (p === 'set') loadSet(); if (p === 'progs') loadProgPage() }
function toast(m, t = '') { const e = document.createElement('div'); e.className = 'toast ' + (t === 'ok' ? 'ok' : t === 'er' ? 'er' : ''); e.textContent = m; document.getElementById('tc').appendChild(e); setTimeout(() => e.remove(), 4000) }
async function api(p, b = null) { const o = b ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) } : {}; const r = await fetch(p, o); return r.json() }
function openModal(id) { document.getElementById(id).classList.add('open') }
function closeModal(id) { document.getElementById(id).classList.remove('open') }
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML }
async function renameAcc() {
  if (!S.sel) return; const acc = S.accs.find(a => a.id === S.sel); const n = prompt(__('new_name'), acc.name); if (!n || n === acc.name) return;
  const r = await api('/api/account-update', { id: S.sel, name: n }); if (r.ok) { toast(__('renamed'), 'ok'); loadAccs() } else toast(r.error || __('error'), 'er')
}
async function deleteAcc() {
  if (!S.sel) return; if (!confirm(__('delete_confirm'))) return;
  const r = await api('/api/account-delete', { id: S.sel }); if (r.ok) { toast(__('deleted'), 'ok'); S.sel = null; loadAccs() } else toast(r.error || __('error'), 'er')
}

// ACCOUNTS
async function loadAccs() { const d = await api('/api/accounts'); S.accs = d.accounts; S.active = d.active; S.progs = d.programs; renderAccs() }
function renderAccs() {
  const c = document.getElementById('acc-cards'); if (!S.accs.length) { c.innerHTML = '<div class="empty"><p>' + __('no_accounts') + '</p></div>'; return }
  const sorted = [...S.accs].sort((a, b) => a.name.localeCompare(b.name));
  c.innerHTML = sorted.map(a => {
    const u = a._usage; const email = a.email || (u && u.email) || ''; const plan = a.plan || (u && u.plan) || '';
    return `<div class="ac ${S.sel === a.id ? 'sel' : ''}" onclick="selAcc('${a.id}')"><div class="ah"><span class="dot" style="background:${a._color}"></span><span class="an">${a.name}</span><span class="ap">${a._prov}</span></div><div class="am">${a.model || __('default_model')}${email ? ' · ' + email : ''}${plan ? ' · ' + plan : ''}</div>${usageBarHtml(u)}</div>`
  }).join('')
}

function usageBarHtml(u) {
  if (!u || u.error) { if (u && u.error) return '<div class="ub"><span class="ue">' + u.type + ': ' + u.error + '</span></div>'; return '' }
  if (u.type === 'codex') {
    const rows = []; if (u.windows && u.windows.length) { u.windows.forEach(w => { const rem = w.remaining_pct != null ? w.remaining_pct : (100 - w.used_pct); const c = rem < 20 ? 'var(--err)' : rem < 50 ? 'var(--warn)' : 'var(--ok)'; rows.push('<div class="ub"><span class="ul">' + w.label + '</span><span class="ubar"><span class="ufill" style="width:' + w.used_pct + '%;background:' + c + '"></span></span><span class="ul" style="color:' + c + ';font-weight:500">' + w.used_pct + '%</span></div>') }) }
    if (rows.length) return '<div style="display:flex;flex-direction:column;gap:2px">' + rows.join('') + '</div>'
    if (u.plan || u.email || u.token_expires_in != null) { const parts = []; if (u.email) parts.push(u.email); if (u.plan) parts.push(u.plan); if (u.token_expires_in != null) parts.push(Math.round(u.token_expires_in / 3600) + 'h'); return '<div class="ub"><span class="ul">codex</span><span class="ue">' + parts.join(' · ') + '</span></div>' }
    return ''
  }
  if (u.type === 'claude-desktop') { const h = u.expires_in_hours; const hasR = u.has_refresh; const remPct = h != null ? (h / 24 * 100) : 0; const c = remPct < 20 ? 'var(--err)' : remPct < 50 ? 'var(--warn)' : 'var(--ok)'; const label = h == null ? __('expired') : h > 1 ? Math.round(h) + __('h') : '<1' + __('h'); return '<div class="ub"><span class="ul">' + __('token') + '</span><span class="ubar"><span class="ufill" style="width:' + (u.used_pct != null ? u.used_pct : 100) + '%;background:' + c + '"></span></span><span class="ul" style="color:' + c + '">' + label + '</span>' + (hasR ? '<span class="ue">' + __('refresh_ok') + '</span>' : '<span class="ue">' + __('no_refresh') + '</span>') + '</div>' }
  if (u.type === 'claude-code') { if (u.error) return '<div class="ub"><span class="ue">claude: ' + u.error + '</span></div>'; const parts = []; if (u.org_id || u.name) parts.push((u.org_id || '') + (u.name ? ' (' + u.name + ')' : '')); if (u.balance != null) parts.push('balance: ' + u.balance); if (u.note) parts.push(u.note); if (u.usage) parts.push(JSON.stringify(u.usage).slice(0, 60)); if (!parts.length) return '<div class="ub"><span class="ul">claude-code</span><span class="ue">ok</span></div>'; return '<div class="ub"><span class="ul">claude-code</span><span class="ue">' + parts.join(' · ') + '</span></div>' }
  const pct = u.used_pct; if (pct == null) return ''; const rem = u.remaining_pct != null ? u.remaining_pct : (100 - pct); const c = rem < 20 ? 'var(--err)' : rem < 50 ? 'var(--warn)' : 'var(--ok)'; const remLbl = u.remaining !== undefined ? ' · ' + u.remaining + ' ' + __('left') : ''; return '<div class="ub"><span class="ul">' + u.type + '</span><span class="ubar"><span class="ufill" style="width:' + pct + '%;background:' + c + '"></span></span><span class="ul">' + pct + '%</span><span class="ue">' + remLbl + '</span></div>'
}
async function refreshUsage() { await api('/api/usage-refresh', {}); loadAccs(); toast(__('usage_refreshed'), 'ok') }

function selAcc(id) { S.sel = id; renderAccs(); renderProgs(); renderAccDetails() }
function renderProgs() {
  document.getElementById('no-sel').style.display = 'none'; document.getElementById('pcon').style.display = 'flex';
  const acc = S.accs.find(a => a.id === S.sel); if (!acc) return;
  const pgrid = document.getElementById('pgrid');
  pgrid.innerHTML = '<div style="grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;padding:4px 0;gap:6px"><div style="font-size:12px;font-weight:500;color:var(--tx2)" title="' + __('write_account') + '">' + __('apply_to') + ' <span style="font-size:10px;color:var(--tx3);font-weight:400">' + __('write_account') + '</span></div><div style="display:flex;gap:4px"><button class="b bs" onclick="allChk(true)">' + __('all') + '</button><button class="b bs" onclick="allChk(false)">' + __('none') + '</button><button class="b bs bp" onclick="applySel()">' + __('sync_all') + '</button></div></div>' +
    S.progs.map(p => {
      const aid = S.active[p.id]; const isMe = aid === acc.id; const who = isMe ? '<span class="at" style="font-size:10px">' + __('active') + '</span>' : aid ? S.accs.find(a => a.id === aid)?.name || aid : '—';
      return `<div class="pc ${isMe ? 'chk' : ''}" onclick="tglChk(this)" style="padding:8px 10px"><div class="pt2" style="gap:6px"><div class="pi" style="width:24px;height:24px;font-size:11px">${PI[p.id] || '?'}</div><div><div class="pn" style="font-size:12px">${p.name}</div></div><div class="pa" style="font-size:10px">${who}</div></div><div class="pc2" style="margin-top:4px;gap:4px;font-size:10px"><input type="checkbox" value="${p.id}" ${isMe ? 'checked' : ''}><span>${__('apply')}</span></div></div>`
    }).join('')
}
function renderAccDetails() {
  const acc = S.accs.find(a => a.id === S.sel); if (!acc) return;
  document.getElementById('ad-dot').style.background = acc._color;
  document.getElementById('ad-name').textContent = acc.name;
  const u = acc._usage || {};
  const parts = [];
  if ('codex_provider' in acc) parts.push('import: Codex' + (acc.codex_provider ? ' (' + acc.codex_provider + ')' : ''));
  if ('claude_oauth_cred' in acc) parts.push('import: Claude Desktop OAuth (' + acc.claude_oauth_cred + ')');
  if (!('codex_provider' in acc) && !('claude_oauth_cred' in acc)) parts.push('import: manual');
  parts.push('token: ' + (acc.claude_oauth_cred ? 'OAuth (JWT)' : acc.api_key && acc.api_key.startsWith('sk-') ? 'API Key (sk-)' : acc.api_key && acc.api_key.startsWith('sk-ant-') ? 'API Key (Anthropic)' : acc.api_key ? 'API Key (custom)' : 'Codex (ChatGPT OAuth)'));
  const keyMask = acc.api_key && !acc.claude_oauth_cred ? acc.api_key.slice(0, 8) + '...' + acc.api_key.slice(-4) : '—';
  const rows = [
    [__('provider'), acc._prov],
    [__('email'), acc.email || u.email || (u.type === 'codex' ? u.email : '') || '—'],
    [__('plan'), acc.plan || u.plan || (u.type === 'codex' ? u.plan : '') || '—'],
    [__('model'), acc.model || '—'],
    [__('base_url'), acc.base_url || '—'],
    [__('api_key'), keyMask],
    [__('source'), parts.join('; ')],
    [__('source_file'), acc.source_path || '—', function (td) { if (acc.source_path) td.innerHTML += '<button class="b bs" onclick="event.stopPropagation();api(\'/api/open-folder\',{path:\'' + esc(acc.source_path) + '\'})" style="margin-left:6px;padding:2px 6px">\uD83D\uDCC2</button>' }],
  ];
  if (u.token_expires_in != null) rows.push([__('token_hours_left', Math.round(u.token_expires_in / 3600)), Math.round(u.token_expires_in / 3600) + 'h']);
  if (acc.claude_oauth_expires_in != null) rows.push([__('token_expires'), Math.round(acc.claude_oauth_expires_in / 3600) + 'h (' + (acc.claude_oauth_has_refresh ? __('refresh_ok') : __('no_refresh')) + ')']);
  if (acc.claude_oauth_has_refresh) rows.push([__('refresh_token'), '<button class="b bs bp" onclick="doRefreshToken()">' + __('refresh_token') + '</button>']);
  document.getElementById('ad-body').innerHTML = '<table style="width:100%;border-collapse:collapse">' + rows.map(r => { let val = esc(String(r[1])); if (r.length > 2 && typeof r[2] === 'function') { val = r[1]; if (typeof val === 'string') val = esc(val) } return '<tr><td style="padding:6px 10px 6px 0;color:var(--tx2);font-size:11px;white-space:nowrap;width:1px">' + esc(r[0]) + '</td><td style="padding:6px 0;font-size:12px;word-break:break-all">' + val + '</td></tr>' }).join('') + '</table>'
}

function tglChk(c) { const cb = c.querySelector('input[type=checkbox]'); cb.checked = !cb.checked; c.classList.toggle('chk', cb.checked) }
function allChk(v) { document.querySelectorAll('#pgrid input[type=checkbox]').forEach(cb => { cb.checked = v; cb.closest('.pc').classList.toggle('chk', v) }) }

async function applySel() {
  if (!S.sel) return; const pids = [...document.querySelectorAll('#pgrid input:checked')].map(c => c.value); if (!pids.length) { toast(__('select_programs')); return }
  const r = await api('/api/apply', { account_id: S.sel, programs: pids });
  r.results?.forEach(x => toast(x.message, x.ok ? 'ok' : 'er')); loadAccs()
}

async function doImport() { const r = await api('/api/import'); toast(__('imported', r.imported?.join(', ') || 'none'), r.imported?.length ? 'ok' : ''); loadAccs() }

function toggleImportDD() { const m = document.getElementById('import-menu'); m.style.display = m.style.display === 'none' ? 'block' : 'none' }
function hideImportDD() { document.getElementById('import-menu').style.display = 'none' }
document.addEventListener('click', e => { if (!e.target.closest('#import-dd')) hideImportDD() });

async function doImportFile() { const p = prompt(__('enter_folder')); if (!p) return; const r = await api('/api/import-file', { file_path: p }); toast(__('imported', r.imported?.join(', ') || r.error || 'none'), r.imported?.length ? 'ok' : 'er'); loadAccs() }

async function doRefreshToken() { if (!S.sel) return; const r = await api('/api/refresh-token', { account_id: S.sel }); if (r.ok) { toast(__('done'), 'ok'); loadAccs() } else toast(r.error || __('error'), 'er') }

async function createAcc() {
  const n = document.getElementById('f-name').value.trim(); if (!n) { toast(__('name_required'), 'er'); return }
  const r = await api('/api/account-create', { name: n, provider: document.getElementById('f-prov').value, api_key: document.getElementById('f-key').value, base_url: document.getElementById('f-url').value, model: document.getElementById('f-model').value });
  if (r.ok) { toast(__('created', n), 'ok'); closeModal('m-create');['f-name', 'f-key', 'f-url', 'f-model'].forEach(i => document.getElementById(i).value = ''); loadAccs() } else toast(r.error, 'er')
}

// PROGRAMS
let selProg = null, selFile = 0, selVer = null, diffMode = 'current';
let _progFiles = [], _progVersions = [];
async function loadProgPage() { const d = await api('/api/programs'); renderProgCards(d.programs); if (selProg) renderProgDetail(); else { const el = document.getElementById('prog-detail'); el.style.display = 'none' } }
function renderProgCards(progs) {
  const c = document.getElementById('prog-cards');
  const list = progs || S.progs || [];
  c.innerHTML = list.map(p => `<div class="pc ${selProg === p.id ? 'chk' : ''}" onclick="showProg('${p.id}')"><div class="pt2"><div class="pi">${p.letter || '?'}</div><div><div class="pn">${p.name}</div><div class="pa" style="margin:0">${p.active_account ? '\uD83D\uDC1A ' + p.active_account : '\u2014'}</div></div></div><div style="display:flex;gap:8px;margin-top:6px;font-size:11px;color:var(--tx3)"><span>\uD83D\uDCE6 ${p.skills_count || 0} skills</span><span>\uD83D\uDD17 ${p.mcp_count || 0} MCP</span><span>${p.type}</span></div><div style="font-size:10px;color:var(--tx3);margin-top:4px;word-break:break-all">${p.config_path}</div></div>`).join('')
}
function openFolder(path) { api('/api/open-folder', { path }) }

async function showProg(id) {
  selProg = id; selFile = 0; selVer = null; diffMode = 'current';
  const r = await api('/api/program-files', { program_id: id });
  _progFiles = r.files || []; renderProgCards(null); renderProgDetail()
}

function renderProgDetail() {
  const el = document.getElementById('prog-detail'); el.style.display = '';
  const p = S.progs.find(x => x.id === selProg); if (!p) { el.innerHTML = ''; return }
  const f = _progFiles[selFile] || {};
  el.innerHTML = '<div class="pd-split">' +
    // LEFT: files + version list
    '<div class="pd-left">' +
    '<div class="pd-hdr2">' + esc(p.name) + '<span class="pd-path">' + esc(f.path || p.config_path) + '</span>' +
    '<button class="b bs" onclick="openFolder(\'' + esc(f.path || p.config_path).replace(/[^/]+$/, '') + '\')" style="padding:2px 6px">\uD83D\uDCC2</button></div>' +
    '<div class="pd-tabs" id="pd-tabs">' +
    _progFiles.map((ff, i) => '<div class="pd-tab' + (i === selFile ? ' on' : '') + '" onclick="selectFile(' + i + ')">' + esc(ff.name) + (ff.desc ? ' <span style="color:var(--tx3);font-size:10px">(' + esc(ff.desc) + ')</span>' : '') + '</div>').join('') +
    '</div>' +
    '<div id="pd-vers" class="pd-ver-list">' + __('loading') + '</div>' +
    '</div>' +
    // RIGHT: diff panel
    '<div class="pd-right hide" id="pd-right">' +
    '<div class="pd-hdr">' +
    '<span style="font-size:12px;font-weight:500" id="pd-diff-title"></span>' +
    '<div class="dmode">' +
    '<button id="dm-cur" class="on" onclick="setDiffMode(\'current\')">' + __('vs_current') + '</button>' +
    '<button id="dm-prev" onclick="setDiffMode(\'previous\')">' + __('vs_previous') + '</button>' +
    '<button class="b bs" onclick="closeDiff()" style="margin-left:4px">\u2715</button>' +
    '</div>' +
    '</div>' +
    '<div class="pd-scroll diff-wrap" id="pd-diff"></div>' +
    '</div>' +
    '</div>';
  // load versions for the selected file
  loadVersions()
}

async function selectFile(i) {
  selFile = i; selVer = null;
  document.querySelectorAll('.pd-tab').forEach((t, idx) => t.classList.toggle('on', idx === i));
  document.getElementById('pd-right').classList.add('hide');
  loadVersions()
}

async function loadVersions() {
  const el = document.getElementById('pd-vers'); if (!el) return;
  const f = _progFiles[selFile]; if (!f || !f.path) { el.innerHTML = '<div style="padding:14px;color:var(--tx3);font-size:12px">—</div>'; return }
  const r = await api('/api/history-list', { file_path: f.path });
  _progVersions = r.versions || [];
  if (!_progVersions.length) { el.innerHTML = '<div style="padding:14px;color:var(--tx3);font-size:12px">' + __('no_history') + '</div>'; return }
  el.innerHTML = _progVersions.map(v => {
    const d = new Date(v.created_at * 1000); const ts = d.toLocaleString();
    const lbl = v.label ? '<span class="vlb">' + esc(v.label) + '</span>' : '<span class="vlb" style="font-style:italic;color:var(--tx3)">' + __('version') + ' #' + v.id + '</span>';
    return '<div class="pd-ver' + (selVer === v.id ? ' sel' : '') + '" data-id="' + v.id + '" onclick="showDiff(' + v.id + ')"><span class="vts">' + ts + '</span>' + lbl + '<button class="vb" onclick="event.stopPropagation();showDiff(' + v.id + ')">' + __('diff') + '</button></div>'
  }).join('')
}

async function showDiff(verId, mode) {
  selVer = verId; if (mode) diffMode = mode;
  document.getElementById('pd-right').classList.remove('hide');
  document.getElementById('pd-diff').innerHTML = __('loading');
  // highlight selected version
  document.querySelectorAll('.pd-ver').forEach(v => v.classList.toggle('sel', parseInt(v.dataset.id) === verId));
  const r = await api('/api/history-diff', { version_id: verId, compare_to: diffMode });
  document.getElementById('pd-diff-title').textContent = r.left_title + ' ↔ ' + r.right_title;
  document.getElementById('pd-diff').innerHTML = r.html || '<div style="padding:20px;color:var(--tx3)">—</div>';
  document.getElementById('dm-cur').classList.toggle('on', diffMode === 'current');
  document.getElementById('dm-prev').classList.toggle('on', diffMode === 'previous')
}

function setDiffMode(m) { diffMode = m; if (selVer) showDiff(selVer, m) }
function closeDiff() { document.getElementById('pd-right').classList.add('hide') }

// SKILLS
async function loadSkills() {
  const d = await api('/api/skills');
  const head = document.getElementById('sk-head'); const body = document.getElementById('sk-body');
  const pids = S.progs.map(p => p.id); const pnames = {}; S.progs.forEach(p => pnames[p.id] = p.name);
  const sel = document.getElementById('sk-import-prog'); sel.innerHTML = S.progs.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
  head.innerHTML = `<tr><th>Skill</th>${pids.map(id => `<th style="text-align:center">${pnames[id]}</th>`).join('')}</tr>`;
  const rows = d.master.map(sk => {
    const checks = pids.map(pid => { const has = sk.name in Object.fromEntries((d.programs[pid] || []).map(n => [n, true])); return `<td style="text-align:center"><input type="checkbox" data-sk="${sk.name}" data-prog="${pid}" ${has ? 'checked' : ''} onchange="skDirty()"></td>` }).join('');
    return `<tr><td class="sn">${sk.name}${sk.in_master ? '<span class="master-tag">master</span>' : ''}<div class="sd">${sk.has_md ? 'SKILL.md' : '—'}</div></td>${checks}</tr>`
  }).join('');
  if (!rows) {
    const ip = S.progs.map(p => `<div class="pc" onclick="importSkillsFromProgram('${p.id}')" style="cursor:pointer"><div class="pt2"><div class="pi">${p.letter || '?'}</div><div><div class="pn">${p.name}</div><div class="sd">${p.id}</div></div></div><div style="font-size:11px;color:var(--tx3)">${__('click_import')}</div></div>`).join('');
    body.innerHTML = `<tr><td colspan="99"><div style="padding:20px;text-align:center;color:var(--tx3)">${__('no_skills')}</div><div style="padding:0 20px 20px"><div style="font-size:13px;font-weight:500;margin-bottom:8px;color:var(--tx2)">${__('import')}:</div><div class="pgrid" style="grid-template-columns:repeat(auto-fill,minmax(200px,1fr))">${ip}</div><div style="margin-top:12px;display:flex;gap:8px;align-items:center"><button class="b" onclick="importSkillsFromFolder()">📁 ${__('from_folder')}</button></div></div></td></tr>`
  }
  else { body.innerHTML = rows; skDirty() }
}
async function importSkillsFromProgram(pid) { if (!pid) pid = document.getElementById('sk-import-prog').value; const r = await api('/api/skills-import-from-program', { program: pid }); if (r.imported?.length) toast(__('imported', r.imported.join(', ')), 'ok'); else toast(__('no_new_skills'), ''); loadSkills() }
async function importSkillsFromFolder() { const p = prompt(__('enter_folder')); if (!p) return; const r = await api('/api/skills-import-from-folder', { folder: p }); if (r.imported?.length) toast(__('imported', r.imported.join(', ')), 'ok'); else toast(__('no_new_skills'), 'er'); loadSkills() }

function skDirty() {
  const btn = document.querySelector('#pg-skills [onclick*="syncAllSkills"]'); if (!btn) return
  const all = document.querySelectorAll('#sk-body input[type=checkbox]'); let dirty = false
  all.forEach(cb => { if (dirty) return; if (typeof cb.dataset.orig === 'string') { if ((cb.checked && cb.dataset.orig === '0') || (!cb.checked && cb.dataset.orig === '1')) dirty = true } })
  if (!dirty) { all.forEach(cb => { if (typeof cb.dataset.orig !== 'string') cb.dataset.orig = cb.checked ? '1' : '0' }) }
  btn.disabled = !dirty
}
async function syncAllSkills() {
  const rows = {}; document.querySelectorAll('#sk-body input:checked').forEach(cb => { const sk = cb.dataset.sk; const pid = cb.dataset.prog; if (!rows[sk]) rows[sk] = []; if (!rows[sk].includes(pid)) rows[sk].push(pid) }); const names = Object.keys(rows); if (!names.length) { toast(__('nothing_selected'), 'er'); return }
  let ok = 0, err = 0; for (const name of names) { const r = await api('/api/skill-sync', { skill: name, programs: rows[name] }); if (r.ok) ok++; else err++ }
  toast(ok + ' ' + __('synced') + (err ? ' · ' + err + ' ' + __('errors') : ''), err ? 'er' : 'ok'); loadSkills()
}

// MCP
async function loadMcp() {
  const d = await api('/api/mcp');
  const head = document.getElementById('mcp-head'); const body = document.getElementById('mcp-body');
  const pids = Object.keys(d.program_names); const pnames = d.program_names;
  head.innerHTML = `<tr><th>Server</th>${pids.map(id => `<th style="text-align:center">${pnames[id]}</th>`).join('')}</tr>`;
  body.innerHTML = d.servers.map(s => {
    const checks = pids.map(pid => `<td style="text-align:center"><input type="checkbox" data-srv="${s.name}" data-prog="${pid}" ${s.programs[pid] ? 'checked' : ''} onchange="mcpDirty()"></td>`).join('');
    const info = s.config?.url || [s.config?.command || '', ...(s.config?.args || [])].join(' ');
    return `<tr><td class="sn">${s.name}${s.in_master ? '<span class="master-tag">master</span>' : ''}<div class="sd">${info}</div></td>${checks}</tr>`
  }).join('');
  mcpDirty()
}

function mcpDirty() {
  const btn = document.querySelector('#pg-mcp [onclick*="syncAllMcp"]'); if (!btn) return
  const all = document.querySelectorAll('#mcp-body input[type=checkbox]'); let dirty = false
  all.forEach(cb => { if (dirty) return; if (typeof cb.dataset.orig === 'string') { if ((cb.checked && cb.dataset.orig === '0') || (!cb.checked && cb.dataset.orig === '1')) dirty = true } })
  if (!dirty) { all.forEach(cb => { if (typeof cb.dataset.orig !== 'string') cb.dataset.orig = cb.checked ? '1' : '0' }) }
  btn.disabled = !dirty
}
async function syncAllMcp() {
  const rows = {}; document.querySelectorAll('#mcp-body input:checked').forEach(cb => { const srv = cb.dataset.srv; const pid = cb.dataset.prog; if (!rows[srv]) rows[srv] = []; if (!rows[srv].includes(pid)) rows[srv].push(pid) }); const names = Object.keys(rows); if (!names.length) { toast(__('nothing_selected'), 'er'); return }
  let ok = 0, err = 0; for (const name of names) { const r = await api('/api/mcp-sync', { name, programs: rows[name] }); if (r.ok) ok++; else err++ }
  toast(ok + ' ' + __('synced') + (err ? ' · ' + err + ' ' + __('errors') : ''), err ? 'er' : 'ok'); loadMcp()
}
async function addMcp() {
  const name = document.getElementById('mf-name').value.trim(); if (!name) { toast(__('name_required'), 'er'); return }
  const args = document.getElementById('mf-args').value.split(',').map(s => s.trim()).filter(Boolean);
  const pids = [...document.querySelectorAll(`input[data-srv="${name}"]:checked`)].map(c => c.dataset.prog);
  await api('/api/mcp-add', { name, command: document.getElementById('mf-cmd').value, args, url: document.getElementById('mf-url').value, programs: pids });
  closeModal('m-mcp'); toast(__('done'), 'ok'); loadMcp()
}

// SETTINGS
async function loadSet() {
  const c = document.getElementById('set-con'); const cfg = await api('/api/get-settings');
  const hLabel = cfg.auto_backup !== false ? __('versions_saved') : '';
  c.innerHTML = `<div style="margin-bottom:16px"><div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--brd)"><div><div style="font-size:13px">${__('auto_backup')}</div><div style="font-size:11px;color:var(--tx3)">${__('before_changes')}</div></div><input type="checkbox" ${cfg.auto_backup !== false ? 'checked' : ''} onchange="api('/api/set-auto-backup',{enabled:this.checked})"></div></div>
<div style="display:flex;gap:8px;margin-bottom:16px"><button class="b" onclick="doBackupNow()">${__('backup_now')}</button><button class="b" onclick="snapshotNow()">${__('snapshot')}</button><button class="b bd" onclick="doShutdown()">${__('shutdown')}</button></div>
<details style="margin-bottom:16px"><summary style="cursor:pointer;color:var(--tx2);font-size:12px;margin-bottom:8px">${__('history')} (${hLabel})</summary><div id="hist-list" style="max-height:300px;overflow:auto">${__('loading') || 'Loading...'}</div></details>
<details><summary style="cursor:pointer;color:var(--tx2);font-size:12px;margin-bottom:8px">${__('raw_config')}</summary><pre style="background:var(--card);padding:12px;border-radius:var(--r);font-size:11px;overflow:auto;max-height:300px;color:var(--tx2)">${JSON.stringify(cfg, null, 2)}</pre></details>`;
  loadHistory()
}
async function snapshotNow() { const r = await api('/api/history-snapshot', { label: 'manual' }); toast(__('snapshot_done', r.count), 'ok') }
async function loadHistory() {
  const el = document.getElementById('hist-list'); if (!el) return;
  const r = await api('/api/history-list', {}); const v = r.versions || [];
  if (!v.length) { el.innerHTML = '<div style="color:var(--tx3);font-size:12px">' + __('no_history') + '</div>'; return }
  const groups = {}; v.forEach(x => { if (!groups[x.file_path]) groups[x.file_path] = []; groups[x.file_path].push(x) })
  el.innerHTML = Object.entries(groups).map(([fp, vers]) => '<div style="margin-bottom:8px"><div style="font-size:11px;font-weight:500;color:var(--tx2);margin-bottom:4px;word-break:break-all">' + esc(fp) + '</div>' +
    vers.slice(0, 10).map(x => {
      const d = new Date(x.created_at * 1000); const ts = d.toLocaleString();
      const label = x.label ? '<span style="color:var(--tx3);font-size:10px">' + esc(x.label) + '</span>' : '';
      return '<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 6px;font-size:11px;border-bottom:1px solid var(--brd)"><span>' + ts + ' ' + label + '</span><button class="b bs" onclick="restoreVersion(' + x.id + ')">' + __('restore') + '</button></div>'
    }).join('') +
    '</div>').join('')
}
async function restoreVersion(id) {
  if (!confirm('Restore this version? Current content will be saved first.')) return;
  const r = await api('/api/history-restore', { version_id: id }); toast(r.message, r.ok ? 'ok' : 'er'); loadHistory()
}
async function doBackupNow() { const r = await api('/api/backup-now', {}); if (r.ok) toast(__('done'), 'ok'); else toast(r.error || __('error'), 'er') }
async function doShutdown() { await api('/api/shutdown'); toast(__('shutting_down')); setTimeout(() => location.reload(), 1500) }

// INIT
document.getElementById('lang-sw').value = S.lang
applyLang()
loadAccs().then(() => { if (!S.accs.length) doImport() });
