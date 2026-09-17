/* Excel Study Notes: Group -> Class -> Subject -> PDF reader. */
(function () {
  'use strict';

  const config = window.EA_EXCEL_STUDY_NOTES_CONFIG || {};
  const root = document.getElementById('excelStudyNotesRoot');
  if (!root) return;

  const state = {
    catalog: null,
    adminCatalog: null,
    role: '',
    canAdmin: false,
    csrf: '',
    groupId: '',
    classId: '',
    subjectId: '',
    search: '',
    status: '',
    statusType: '',
    loading: true,
    readerNote: null,
  };

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch];
    });
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function id(prefix) {
    if (window.crypto && crypto.randomUUID) return prefix + '-' + crypto.randomUUID().replace(/-/g, '').slice(0, 10);
    return prefix + '-' + Math.random().toString(36).slice(2, 12);
  }

  function currentCatalog() {
    return state.canAdmin && state.adminCatalog ? state.adminCatalog : state.catalog;
  }

  function findById(items, wanted) {
    return (items || []).find(function (item) { return item.id === wanted; }) || null;
  }

  function selectedNodes() {
    const catalog = currentCatalog() || { groups: [] };
    let group = findById(catalog.groups, state.groupId);
    if (!group) group = (catalog.groups || [])[0] || null;
    if (group) state.groupId = group.id;
    let klass = group && findById(group.classes, state.classId);
    if (!klass) klass = group && (group.classes || [])[0] || null;
    if (klass) state.classId = klass.id;
    let subject = klass && findById(klass.subjects, state.subjectId);
    if (!subject) subject = klass && (klass.subjects || [])[0] || null;
    if (subject) state.subjectId = subject.id;
    return { catalog: catalog, group: group, klass: klass, subject: subject };
  }

  function setStatus(message, type) {
    state.status = message || '';
    state.statusType = type || '';
    const el = root.querySelector('[data-status]');
    if (el) {
      el.textContent = state.status;
      el.className = 'sn-status ' + state.statusType;
    }
  }

  async function fetchJson(url, options) {
    const response = await fetch(url, Object.assign({ cache: 'no-store' }, options || {}));
    const body = await response.json().catch(function () { return {}; });
    if (!response.ok || body.success === false) {
      const error = new Error(body.error || ('Request failed (' + response.status + ').'));
      error.status = response.status;
      error.body = body;
      throw error;
    }
    return body;
  }

  function isPublicAuthenticated() {
    if (typeof config.isAuthenticated === 'function') {
      try { return !!config.isAuthenticated(); } catch (e) {}
    }
    const authKey = String(config.authStorageKey || 'ea_public_auth');
    try { return !!JSON.parse(localStorage.getItem(authKey) || 'null'); } catch (e) { return false; }
  }

  function fileUrl(storageKey) {
    const base = String(config.filesBase || '');
    return base + encodeURIComponent(String(storageKey || ''));
  }

  function formatSize(bytes) {
    const value = Number(bytes || 0);
    if (!value) return 'PDF';
    if (value < 1024 * 1024) return Math.max(1, Math.round(value / 1024)) + ' KB';
    return (value / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function visibleNotes(subject) {
    const notes = (subject && subject.notes) || [];
    const query = state.search.trim().toLowerCase();
    if (!query) return notes;
    return notes.filter(function (note) {
      return [note.title, note.description, (note.tags || []).join(' ')].join(' ').toLowerCase().includes(query);
    });
  }

  function renderGate() {
    const loginAction = config.loginUrl
      ? '<p><a class="sn-btn primary" href="' + esc(config.loginUrl) + '">Sign in on the main site</a></p>'
      : '';
    root.innerHTML = '<div class="sn-gate"><h1>Excel Study Notes</h1><p>Sign in to read the academy\'s published PDF notes. Notes open inside the protected reader and are not offered as ordinary downloads.</p>' + loginAction + '<p class="sn-privacy">The browser must receive PDF pixels to display them. Copying, printing, download controls, and context menus are deterred, but no browser can absolutely prevent screenshots or determined network capture.</p></div>';
  }

  function renderLoading() {
    root.innerHTML = '<div class="sn-gate"><h1>Excel Study Notes</h1><p>Loading your study library…</p></div>';
  }

  function groupList(nodes) {
    const groups = (nodes.catalog.groups || []);
    if (!groups.length) return '<div class="sn-empty">No groups have been added yet.</div>';
    return groups.map(function (group) {
      const active = group.id === nodes.group.id;
      return '<button type="button" class="sn-side-btn ' + (active ? 'active' : '') + '" data-sn-group="' + esc(group.id) + '"><span>' + esc(group.name) + '</span><small>' + (group.classes || []).length + '</small></button>';
    }).join('');
  }

  function classList(nodes) {
    const classes = (nodes.group && nodes.group.classes) || [];
    if (!classes.length) return '<div class="sn-empty">No classes in this group.</div>';
    return classes.map(function (klass) {
      const active = klass.id === nodes.klass.id;
      return '<button type="button" class="sn-side-btn ' + (active ? 'active' : '') + '" data-sn-class="' + esc(klass.id) + '"><span>' + esc(klass.name) + '</span><small>' + (klass.subjects || []).length + '</small></button>';
    }).join('');
  }

  function subjectTabs(nodes) {
    const subjects = (nodes.klass && nodes.klass.subjects) || [];
    if (!subjects.length) return '<div class="sn-empty">No subjects in this class.</div>';
    return subjects.map(function (subject) {
      return '<button type="button" class="sn-subject-tab ' + (subject.id === nodes.subject.id ? 'active' : '') + '" data-sn-subject="' + esc(subject.id) + '">' + esc(subject.name) + '</button>';
    }).join('');
  }

  function notesGrid(nodes) {
    const notes = visibleNotes(nodes.subject);
    if (!nodes.subject) return '<div class="sn-empty">Choose a subject to see its PDFs.</div>';
    if (!notes.length) return '<div class="sn-empty">No published PDF notes in this subject yet.</div>';
    return '<div class="sn-notes-grid">' + notes.map(function (note) {
      const tags = (note.tags || []).map(function (tag) { return '<span class="sn-chip">' + esc(tag) + '</span>'; }).join('');
      return '<article class="sn-note"><div><h3 title="' + esc(note.title) + '">' + esc(note.title) + '</h3>' +
        '<p>' + esc(note.description || 'PDF study material for ' + nodes.subject.name + '.') + '</p></div>' +
        '<div><div class="sn-note-meta"><span class="sn-chip">PDF</span><span class="sn-chip">' + formatSize(note.size_bytes) + '</span>' + tags + '</div>' +
        '<button type="button" class="sn-btn primary" data-open-note="' + esc(note.id) + '" style="width:100%;margin-top:10px">Open full-page reader</button></div></article>';
    }).join('') + '</div>';
  }

  function selectOptions(items, selected) {
    return (items || []).map(function (item) {
      return '<option value="' + esc(item.id) + '" ' + (item.id === selected ? 'selected' : '') + '>' + esc(item.name) + '</option>';
    }).join('');
  }

  function renderLibrary(nodes) {
    const subjectName = nodes.subject ? nodes.subject.name : 'Select a subject';
    return '<div class="sn-toolbar">' +
      '<div class="sn-field"><label for="snGroupSelect">Group</label><select id="snGroupSelect" data-select-group>' + selectOptions(nodes.catalog.groups, nodes.group && nodes.group.id) + '</select></div>' +
      '<div class="sn-field"><label for="snClassSelect">Class</label><select id="snClassSelect" data-select-class>' + selectOptions(nodes.group && nodes.group.classes, nodes.klass && nodes.klass.id) + '</select></div>' +
      '<div class="sn-field"><label for="snSubjectSelect">Subject</label><select id="snSubjectSelect" data-select-subject>' + selectOptions(nodes.klass && nodes.klass.subjects, nodes.subject && nodes.subject.id) + '</select></div>' +
      '<div class="sn-field"><label for="snSearch">Search notes</label><input id="snSearch" data-search type="search" value="' + esc(state.search) + '" placeholder="Title, tag…"></div>' +
      '</div>' +
      '<div class="sn-crumbs"><span>Library</span><span>›</span><strong>' + esc(nodes.group ? nodes.group.name : 'No group') + '</strong><span>›</span><strong>' + esc(nodes.klass ? nodes.klass.name : 'No class') + '</strong><span>›</span><strong>' + esc(subjectName) + '</strong></div>' +
      '<div class="sn-layout"><aside class="sn-card"><h2>Groups</h2><div class="sn-side-list">' + groupList(nodes) + '</div><h2 style="margin-top:17px">Classes</h2><div class="sn-side-list">' + classList(nodes) + '</div></aside>' +
      '<main class="sn-card"><h2>' + esc(subjectName) + '</h2><div class="sn-subject-tabs">' + subjectTabs(nodes) + '</div>' + notesGrid(nodes) + '</main></div>';
  }

  function editableRow(kind, item) {
    return '<div class="sn-admin-row"><div class="sn-admin-row-main"><input data-edit="' + kind + '-name" data-id="' + esc(item.id) + '" value="' + esc(item.name) + '" aria-label="' + esc(kind) + ' name"><input data-edit="' + kind + '-sort" data-id="' + esc(item.id) + '" type="number" value="' + Number(item.sort_order || 0) + '" aria-label="sort order"></div><div class="sn-admin-row-actions"><label class="sn-check"><input data-edit="' + kind + '-published" data-id="' + esc(item.id) + '" type="checkbox" ' + (item.published !== false ? 'checked' : '') + '> Published</label><button type="button" class="sn-btn danger small" data-action="delete-' + kind + '" data-id="' + esc(item.id) + '">Delete</button></div></div>';
  }

  function adminNotes(nodes) {
    if (!nodes.subject) return '<div class="sn-empty">Add a subject first.</div>';
    const notes = nodes.subject.notes || [];
    const rows = notes.length ? notes.map(function (note) {
      return '<div class="sn-note-admin"><div class="sn-note-admin-main"><input data-note-field="title" data-note-id="' + esc(note.id) + '" value="' + esc(note.title) + '" aria-label="Note title"><input data-note-field="description" data-note-id="' + esc(note.id) + '" value="' + esc(note.description || '') + '" placeholder="Description" aria-label="Note description"><input data-note-field="tags" data-note-id="' + esc(note.id) + '" value="' + esc((note.tags || []).join(', ')) + '" placeholder="Tags" aria-label="Note tags"><small>' + esc(note.original_name || 'PDF not uploaded') + ' · ' + formatSize(note.size_bytes) + '</small></div><div class="sn-admin-row-actions"><label class="sn-check"><input data-note-field="published" data-note-id="' + esc(note.id) + '" type="checkbox" ' + (note.published !== false ? 'checked' : '') + '> Published</label><label class="sn-btn small">Replace PDF<input type="file" accept="application/pdf,.pdf" data-replace-note="' + esc(note.id) + '" hidden></label><button type="button" class="sn-btn danger small" data-action="delete-note" data-id="' + esc(note.id) + '">Delete</button></div></div>';
    }).join('') : '<div class="sn-empty">No notes in this subject yet.</div>';
    return '<form class="sn-upload-form" data-upload-form>' +
      '<div class="sn-field"><label>Title</label><input name="title" maxlength="200" required placeholder="e.g. Fractions — Revision Notes"></div>' +
      '<div class="sn-field"><label>Description / tags</label><input name="description" maxlength="2000" placeholder="Short description · comma-separated tags in the next field"></div>' +
      '<div class="sn-field"><label>PDF file</label><input name="file" type="file" accept="application/pdf,.pdf" required></div>' +
      '<div class="sn-field"><label>Tags</label><input name="tags" maxlength="500" placeholder="algebra, revision"></div>' +
      '<button class="sn-btn primary" type="submit">Upload PDF</button>' +
      '</form>' + rows;
  }

  function adminPanel(nodes) {
    const groups = nodes.catalog.groups || [];
    const classes = nodes.group ? nodes.group.classes || [] : [];
    const subjects = nodes.klass ? nodes.klass.subjects || [] : [];
    return '<section class="sn-card sn-admin"><div class="sn-admin-head"><div><h2>Administrator controls</h2><div style="color:var(--sn-muted);font-size:.76rem">Edit the hierarchy, upload PDF-only notes, then Save Changes. Revision ' + Number(nodes.catalog.revision || 0) + '.</div></div><div class="sn-admin-actions"><button type="button" class="sn-btn primary" data-action="save">Save Changes</button><button type="button" class="sn-btn gold" data-action="publish">Publish public snapshot</button><a class="sn-btn" href="' + esc(config.exportUrl || '#') + '">Export catalog JSON</a></div></div>' +
      '<div class="sn-structure"><div><h3>Groups <button type="button" class="sn-btn small" data-action="add-group">+ Add</button></h3><div class="sn-admin-list">' + (groups.length ? groups.map(function (item) { return editableRow('group', item); }).join('') : '<div class="sn-empty">No groups yet.</div>') + '</div></div>' +
      '<div><h3>Classes in ' + esc(nodes.group ? nodes.group.name : 'selected group') + ' <button type="button" class="sn-btn small" data-action="add-class" ' + (nodes.group ? '' : 'disabled') + '>+ Add</button></h3><div class="sn-admin-list">' + (classes.length ? classes.map(function (item) { return editableRow('class', item); }).join('') : '<div class="sn-empty">No classes yet.</div>') + '</div></div>' +
      '<div><h3>Subjects in ' + esc(nodes.klass ? nodes.klass.name : 'selected class') + ' <button type="button" class="sn-btn small" data-action="add-subject" ' + (nodes.klass ? '' : 'disabled') + '>+ Add</button></h3><div class="sn-admin-list">' + (subjects.length ? subjects.map(function (item) { return editableRow('subject', item); }).join('') : '<div class="sn-empty">No subjects yet.</div>') + '</div></div></div>' +
      '<div style="margin-top:16px"><h3>PDF notes in ' + esc(nodes.subject ? nodes.subject.name : 'selected subject') + '</h3>' + adminNotes(nodes) + '</div></section>';
  }

  function readerMarkup() {
    return '<div class="sn-reader" id="snReader" hidden role="dialog" aria-modal="true" aria-label="PDF study note reader"><div class="sn-reader-bar"><div class="sn-reader-title" id="snReaderTitle">Study note</div><div class="sn-reader-actions"><button type="button" data-reader-fullscreen>⛶ Full screen</button><button type="button" data-reader-close>✕ Close</button></div></div><div class="sn-reader-stage" id="snReaderStage"><iframe id="snPdfFrame" class="sn-pdf-frame" title="PDF study note" referrerpolicy="no-referrer" allow="fullscreen"></iframe><div class="sn-reader-watermark">Excel Academy · Study Notes</div><div class="sn-reader-hint">Pinch or use your browser’s zoom controls to enlarge · download and print controls are disabled where supported</div></div></div>';
  }

  function render() {
    if (state.loading) return renderLoading();
    if (!state.catalog) return renderGate();
    const nodes = selectedNodes();
    root.innerHTML = '<div class="sn-shell"><header class="sn-hero"><div><div class="sn-kicker">Excel Academy · Focused learning</div><h1>Excel Study Notes</h1><p>Open published PDF notes by Group → Class → Subject. Read comfortably in the full-page viewer with pinch zoom.</p></div><div class="sn-hero-badge">▣ PDF-only library</div></header><div data-status class="sn-status ' + esc(state.statusType) + '">' + esc(state.status) + '</div>' + renderLibrary(nodes) + '<div class="sn-privacy">Reader protections are intentionally layered: authenticated LAN delivery, inline no-cache responses, no download links, disabled host-page copy/print/context-menu actions, and a visible watermark. Screen capture and determined network extraction cannot be technically prevented by a normal browser.</div>' + (state.canAdmin ? adminPanel(nodes) : '') + '</div>' + readerMarkup();
    if (state.readerNote) openReader(state.readerNote, true);
  }

  function updateSelection(type, value) {
    if (type === 'group') { state.groupId = value; state.classId = ''; state.subjectId = ''; }
    if (type === 'class') { state.classId = value; state.subjectId = ''; }
    if (type === 'subject') state.subjectId = value;
    render();
  }

  function getAdminNode(kind, wanted) {
    const catalog = state.adminCatalog;
    if (!catalog) return null;
    if (kind === 'group') return findById(catalog.groups, wanted);
    for (const group of catalog.groups || []) {
      if (kind === 'class') {
        const found = findById(group.classes, wanted);
        if (found) return found;
      }
      for (const klass of group.classes || []) {
        if (kind === 'subject') {
          const found = findById(klass.subjects, wanted);
          if (found) return found;
        }
      }
    }
    return null;
  }

  function getAdminNote(wanted) {
    const catalog = state.adminCatalog;
    if (!catalog) return null;
    for (const group of catalog.groups || []) {
      for (const klass of group.classes || []) {
        for (const subject of klass.subjects || []) {
          const note = findById(subject.notes, wanted);
          if (note) return note;
        }
      }
    }
    return null;
  }

  function addGroup() {
    state.adminCatalog.groups.push({ id: id('grp'), name: 'New Group', description: '', sort_order: state.adminCatalog.groups.length, published: true, classes: [] });
    state.groupId = state.adminCatalog.groups[state.adminCatalog.groups.length - 1].id;
    state.classId = ''; state.subjectId = '';
    render();
  }

  function addClass() {
    const nodes = selectedNodes();
    if (!nodes.group) return;
    nodes.group.classes = nodes.group.classes || [];
    nodes.group.classes.push({ id: id('cls'), name: 'New Class', sort_order: nodes.group.classes.length, published: true, subjects: [] });
    state.classId = nodes.group.classes[nodes.group.classes.length - 1].id; state.subjectId = '';
    render();
  }

  function addSubject() {
    const nodes = selectedNodes();
    if (!nodes.klass) return;
    nodes.klass.subjects = nodes.klass.subjects || [];
    nodes.klass.subjects.push({ id: id('sub'), name: 'New Subject', sort_order: nodes.klass.subjects.length, published: true, notes: [] });
    state.subjectId = nodes.klass.subjects[nodes.klass.subjects.length - 1].id;
    render();
  }

  function deleteNode(kind, wanted) {
    if (!window.confirm('Delete this ' + kind + ' and its nested content? Save Changes will remove it from the catalog and clean its PDF files.')) return;
    const catalog = state.adminCatalog;
    if (kind === 'group') catalog.groups = (catalog.groups || []).filter(function (item) { return item.id !== wanted; });
    if (kind === 'class') catalog.groups.forEach(function (group) { group.classes = (group.classes || []).filter(function (item) { return item.id !== wanted; }); });
    if (kind === 'subject') catalog.groups.forEach(function (group) { (group.classes || []).forEach(function (klass) { klass.subjects = (klass.subjects || []).filter(function (item) { return item.id !== wanted; }); }); });
    if (kind === 'note') catalog.groups.forEach(function (group) { (group.classes || []).forEach(function (klass) { (klass.subjects || []).forEach(function (subject) { subject.notes = (subject.notes || []).filter(function (item) { return item.id !== wanted; }); }); }); });
    state.groupId = ''; state.classId = ''; state.subjectId = ''; state.readerNote = null;
    render();
  }

  async function uploadFile(file, noteId) {
    if (!file || !String(file.name || '').toLowerCase().endsWith('.pdf')) throw new Error('Choose a PDF file only.');
    const form = new FormData();
    form.append('file', file);
    if (noteId) form.append('note_id', noteId);
    const body = await fetchJson(config.uploadUrl, { method: 'POST', headers: { 'X-CSRFToken': state.csrf }, body: form });
    return body.data;
  }

  async function saveCatalog() {
    if (!state.adminCatalog) return;
    setStatus('Saving catalog…', '');
    try {
      const body = await fetchJson(config.adminCatalogUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': state.csrf, 'If-Match': String(state.adminCatalog.revision || 0) },
        body: JSON.stringify(state.adminCatalog),
      });
      state.adminCatalog = body.data;
      eaLearningBridge.reset();
      state.catalog = await fetchJson(config.catalogUrl).then(function (response) {
        return response && response.data ? response.data : response;
      });
      state.status = 'Saved. Published visibility has been refreshed.';
      state.statusType = 'success';
      render();
    } catch (error) {
      state.status = error.status === 409 ? 'Another admin changed the catalog. Reload before saving again.' : error.message;
      state.statusType = 'error';
      render();
    }
  }

  async function publishPublic() {
    setStatus('Writing public snapshot…', '');
    try {
      const body = await fetchJson(config.publishUrl, { method: 'POST', headers: { 'X-CSRFToken': state.csrf } });
      setStatus(body.message || 'Public snapshot updated.', 'success');
    } catch (error) { setStatus(error.message, 'error'); }
  }

  function openReader(note, preserveMarkup) {
    const reader = root.querySelector('#snReader');
    const frame = root.querySelector('#snPdfFrame');
    const title = root.querySelector('#snReaderTitle');
    if (!reader || !frame || !note) return;
    state.readerNote = note;
    title.textContent = note.title || 'Study note';
    frame.src = fileUrl(note.storage_key) + '#toolbar=0&navpanes=0&scrollbar=1&view=FitH';
    reader.hidden = false;
    document.body.classList.add('sn-reading');
    if (!preserveMarkup) reader.querySelector('[data-reader-close]').focus();
  }

  function closeReader() {
    const reader = root.querySelector('#snReader');
    const frame = root.querySelector('#snPdfFrame');
    if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(function () {});
    if (frame) frame.src = 'about:blank';
    if (reader) reader.hidden = true;
    state.readerNote = null;
    document.body.classList.remove('sn-reading');
  }

  async function toggleFullscreen() {
    const stage = root.querySelector('#snReaderStage');
    if (!stage) return;
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (stage.requestFullscreen) await stage.requestFullscreen();
    } catch (error) { setStatus('Full-screen mode is unavailable in this browser.', 'error'); }
  }

  root.addEventListener('click', function (event) {
    const group = event.target.closest('[data-sn-group]');
    if (group) return updateSelection('group', group.dataset.snGroup);
    const klass = event.target.closest('[data-sn-class]');
    if (klass) return updateSelection('class', klass.dataset.snClass);
    const subject = event.target.closest('[data-sn-subject]');
    if (subject) return updateSelection('subject', subject.dataset.snSubject);
    const open = event.target.closest('[data-open-note]');
    if (open) {
      const note = (selectedNodes().subject && selectedNodes().subject.notes || []).find(function (item) { return item.id === open.dataset.openNote; });
      if (note) openReader(note, false);
      return;
    }
    const action = event.target.closest('[data-action]');
    if (action) {
      const name = action.dataset.action;
      if (name === 'add-group') return addGroup();
      if (name === 'add-class') return addClass();
      if (name === 'add-subject') return addSubject();
      if (name === 'delete-group' || name === 'delete-class' || name === 'delete-subject' || name === 'delete-note') return deleteNode(name.slice(7), action.dataset.id);
      if (name === 'save') return saveCatalog();
      if (name === 'publish') return publishPublic();
    }
    if (event.target.closest('[data-reader-close]')) return closeReader();
    if (event.target.closest('[data-reader-fullscreen]')) return toggleFullscreen();
  });

  root.addEventListener('change', async function (event) {
    const target = event.target;
    if (target.matches('[data-select-group]')) return updateSelection('group', target.value);
    if (target.matches('[data-select-class]')) return updateSelection('class', target.value);
    if (target.matches('[data-select-subject]')) return updateSelection('subject', target.value);
    if (target.matches('[data-note-field]')) {
      const note = getAdminNote(target.dataset.noteId);
      if (note) {
        if (target.dataset.noteField === 'published') note.published = target.checked;
        else if (target.dataset.noteField === 'tags') note.tags = target.value.split(',').map(function (tag) { return tag.trim(); }).filter(Boolean).slice(0, 12);
        else note[target.dataset.noteField] = target.value;
      }
      return;
    }
    const edit = target.dataset.edit;
    if (edit) {
      const kind = edit.split('-')[0];
      const field = edit.slice(kind.length + 1);
      const node = getAdminNode(kind, target.dataset.id);
      if (node) node[field === 'sort' ? 'sort_order' : field] = target.type === 'checkbox' ? target.checked : (field === 'sort' ? Number(target.value || 0) : target.value);
      return;
    }
    const replaceId = target.dataset.replaceNote;
    if (replaceId && target.files && target.files[0]) {
      try {
        setStatus('Uploading replacement PDF…', '');
        const meta = await uploadFile(target.files[0], replaceId);
        const note = getAdminNote(replaceId);
        if (note) Object.assign(note, meta);
        setStatus('Replacement uploaded. Save Changes to commit it.', 'success');
        render();
      } catch (error) { setStatus(error.message, 'error'); }
    }
  });

  root.addEventListener('input', function (event) {
    if (!event.target.matches('[data-search]')) return;
    const value = event.target.value;
    const position = event.target.selectionStart || value.length;
    state.search = value;
    render();
    const search = root.querySelector('[data-search]');
    if (search) { search.focus(); search.setSelectionRange(position, position); }
  });

  root.addEventListener('submit', async function (event) {
    const form = event.target.closest('[data-upload-form]');
    if (!form) return;
    event.preventDefault();
    const nodes = selectedNodes();
    if (!nodes.subject) return setStatus('Select a subject before uploading a PDF.', 'error');
    const file = form.elements.file.files[0];
    try {
      setStatus('Uploading PDF…', '');
      const meta = await uploadFile(file);
      const tags = String(form.elements.tags.value || '').split(',').map(function (tag) { return tag.trim(); }).filter(Boolean).slice(0, 12);
      nodes.subject.notes = nodes.subject.notes || [];
      nodes.subject.notes.push({ id: meta.id, title: String(form.elements.title.value || meta.original_name).trim(), description: String(form.elements.description.value || '').trim(), tags: tags, file_type: 'pdf', original_name: meta.original_name, storage_key: meta.storage_key, size_bytes: meta.size_bytes, date_added: meta.date_added, published: true });
      form.reset();
      setStatus('PDF uploaded. Save Changes to add it to the catalog.', 'success');
      render();
    } catch (error) { setStatus(error.message, 'error'); }
  });

  document.addEventListener('contextmenu', function (event) {
    if (event.target.closest && event.target.closest('.sn-reader')) event.preventDefault();
  });
  ['copy', 'cut', 'dragstart', 'selectstart'].forEach(function (name) {
    document.addEventListener(name, function (event) {
      if (event.target.closest && event.target.closest('.sn-reader')) event.preventDefault();
    });
  });
  document.addEventListener('keydown', function (event) {
    const reader = root.querySelector('#snReader');
    if (!reader || reader.hidden) return;
    if ((event.ctrlKey || event.metaKey) && ['c', 'p', 's', 'u'].includes(String(event.key).toLowerCase())) event.preventDefault();
    if (event.key === 'PrintScreen') event.preventDefault();
    if (event.key === 'Escape') closeReader();
  });
  async function load() {
    state.loading = true;
    state.catalog = null;
    state.adminCatalog = null;
    render();
    if (config.mode === 'public' && config.requireAuthForNotes && !isPublicAuthenticated()) {
      state.loading = false;
      return renderGate();
    }
    try {
      if (config.mode !== 'public') {
        const me = await fetchJson(config.meUrl);
        state.role = me.role || '';
        state.canAdmin = !!me.can_admin;
        state.csrf = me.csrf_token || '';
        if (state.canAdmin) state.adminCatalog = (await fetchJson(config.adminCatalogUrl)).data;
      }
      const catData = await fetchJson(config.catalogUrl);
      state.catalog = catData && catData.data ? catData.data : catData;
      state.loading = false;
      eaLearningBridge.reset();
      render();
    } catch (error) {
      state.loading = false;
      root.innerHTML = '<div class="sn-gate"><h1>Excel Study Notes</h1><p class="sn-status error">' + esc(error.message) + '</p><button type="button" class="sn-btn primary" data-retry>Try again</button></div>';
    }
  }

  root.addEventListener('click', function (event) { if (event.target.closest('[data-retry]')) load(); });
  if (config.mode === 'public' && config.requireAuthForNotes) {
    window.addEventListener('ea-auth-changed', load);
    window.addEventListener('storage', function (event) {
      if (event.key === String(config.authStorageKey || 'ea_public_auth')) load();
    });
  }
  // EA_LEARNING_BRIDGE_BEGIN
/* Browse-only bridge embedded inside each learning module's existing closure. */
function eaInstallLearningBridge(adapter) {
  let dirty = false, baseline = '';
  const reset = () => { dirty = false; baseline = JSON.stringify(adapter.adminCatalog() || null); };
  ['input', 'change'].forEach(type => root.addEventListener(type, event => {
    if (adapter.isEditor(event.target)) dirty = true;
  }));
  window.EA_WORKSPACE_LEARNING_APPLY = context => {
    if (!adapter.ready()) return {ok:false, error:'Sign in and wait for the library catalog to load.'};
    if (adapter.editing() || dirty || JSON.stringify(adapter.adminCatalog() || null) !== baseline) {
      return {ok:false, error:'Save or reload the library editor before applying shared browse context.'};
    }
    const normalize = (value, prefix) => String(value || '').trim().toLowerCase().replace(prefix, '');
    const klass = normalize(context.className, /^class\s*/);
    const subject = normalize(context.subject, /^$/);
    const group = normalize(context.group, /^group\s*/);
    if (!klass) return {ok:false, error:'Choose a class first.'};
    const matches = [];
    const catalog = adapter.catalog();
    (Array.isArray(catalog?.groups) ? catalog.groups : []).forEach(g => {
      if (!g || group && group !== normalize(g.name, /^group\s*/) && group !== normalize(g.id, /^group\s*/)) return;
      (Array.isArray(g.classes) ? g.classes : []).forEach(c => {
        if (!c || klass !== normalize(c.name, /^class\s*/) && klass !== normalize(c.id, /^class\s*/)) return;
        if (!subject) matches.push({group:g, klass:c, subject:null});
        else (Array.isArray(c.subjects) ? c.subjects : []).forEach(s => {
          if (s && subject === normalize(s.name, /^$/)) matches.push({group:g, klass:c, subject:s});
        });
      });
    });
    if (matches.length !== 1) return {ok:false, error:matches.length ? 'More than one catalog match. Specify the library group.' : 'Class or subject is unavailable in the published catalog. Existing selection was retained.'};
    adapter.apply(matches[0]);
    return {ok:true};
  };
  return {reset};
}
  // EA_LEARNING_BRIDGE_END
  const eaLearningBridge = eaInstallLearningBridge({
    catalog: () => state.catalog,
    adminCatalog: () => state.adminCatalog,
    ready: () => !state.loading && !!state.catalog && (config.mode !== 'public' || !config.requireAuthForNotes || isPublicAuthenticated()),
    editing: () => !!root.querySelector('.sn-status.error'),
    isEditor: target => !!target.closest('.sn-admin'),
    apply: nodes => {
      state.groupId = nodes.group.id; state.classId = nodes.klass.id;
      state.subjectId = nodes.subject ? nodes.subject.id : ''; state.search = '';
      state.readerNote = null; render();
    }
  });
  load();
}());
