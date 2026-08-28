/**
 * Excel Results Module — Standalone SPA & Cloudflare Tab Client Logic
 * Modern, colorful, responsive educational results & practice question papers
 */
(function () {
  const root = document.getElementById('excelResultsRoot');
  if (!root) return;

  function publicLoggedIn() {
    try {
      return !!JSON.parse(localStorage.getItem('ea_public_auth') || 'null');
    } catch (e) {
      return false;
    }
  }

  function publicAuthRoll() {
    try {
      const auth = JSON.parse(localStorage.getItem('ea_public_auth') || 'null');
      return String(auth && auth.roll || '').trim().toLowerCase();
    } catch (e) {
      return '';
    }
  }

  const cfg = Object.assign({
    mode: 'public',
    catalogUrl: './excel_results/catalog.json',
    filesBase: './excel_results/files/',
    requireAuthForResults: false,
    meUrl: '',
    adminCatalogUrl: '',
    uploadUrl: '',
    importResultsUrl: '',
    previewResultsUrl: '',
    importCatalogUrl: '',
    exportUrl: '',
    publishUrl: '',
  }, window.EA_EXCEL_RESULTS_CONFIG || {});

  const state = {
    catalog: null,
    adminCatalog: null,
    loading: true,
    error: null,
    canAdmin: false,
    role: '',
    route: parseRoute(),
    adminSection: 'tree',
    toast: '',
    confirm: null,
    query: '',
    sort: 'title',
    tagFilter: '',
    page: 1,
    pageSize: 12,
    resultsViewMode: localStorage.getItem('er_results_view') || 'table',
    resultQuery: '',
    resultFilters: { group: '', className: '', subject: '', exam: '', session: '' },
    previewPaper: null,
    formError: '',
    csvPreviewRows: null,
    csvFile: null,
    csrfToken: '',
  };

  function parseRoute() {
    let raw = (location.hash || '').replace(/^#/, '');
    if (cfg.mode === 'public') {
      if (raw === 'er' || raw.indexOf('er/') === 0) {
        raw = raw.replace(/^er\/?/, '');
      } else if (document.getElementById('excelResultsPanel') && !document.getElementById('excelResultsPanel').classList.contains('active')) {
        return { view: 'home' };
      }
    }
    const parts = raw.split('/').filter(Boolean);
    if (!parts.length) return { view: 'home' };
    if (parts[0] === 'results') return { view: 'results' };
    if (parts[0] === 'admin') return { view: 'admin', section: parts[1] || 'tree' };
    if (parts[0] === 'papers') {
      return {
        view: 'papers',
        group: decodeURIComponent(parts[1] || ''),
        klass: decodeURIComponent(parts[2] || ''),
        subject: decodeURIComponent(parts[3] || ''),
        paper: decodeURIComponent(parts[4] || ''),
      };
    }
    return { view: 'home' };
  }

  function go(path) {
    let hash = path.startsWith('#') ? path : '#' + path;
    if (cfg.mode === 'public') {
      const rest = hash.replace(/^#/, '');
      hash = '#er' + (rest.startsWith('/') ? rest : '/' + rest);
    }
    if (location.hash !== hash) {
      location.hash = hash;
    } else {
      state.route = parseRoute();
      render();
    }
  }

  window.addEventListener('hashchange', () => {
    state.route = parseRoute();
    state.page = 1;
    render();
  });

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function toast(msg) {
    state.toast = msg;
    render();
    setTimeout(() => {
      if (state.toast === msg) {
        state.toast = '';
        render();
      }
    }, 3200);
  }

  async function fetchJson(url, options) {
    const opts = Object.assign({ cache: 'no-store', credentials: 'same-origin' }, options || {});
    const method = String(opts.method || 'GET').toUpperCase();
    if (method !== 'GET' && method !== 'HEAD' && state.csrfToken) {
      const headers = new Headers(opts.headers || {});
      headers.set('X-CSRFToken', state.csrfToken);
      opts.headers = headers;
    }
    const resp = await fetch(url, opts);
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || data.success === false) {
      const error = new Error(data.error || ('HTTP ' + resp.status));
      error.status = resp.status;
      error.data = data;
      throw error;
    }
    return data;
  }

  function fileUrl(paper, download) {
    const remote = paper && paper.remote_url;
    if (remote) return remote;
    const key = paper && paper.storage_key;
    if (!key) return '';
    const base = cfg.filesBase.endsWith('/') ? cfg.filesBase : cfg.filesBase + '/';
    return base + encodeURIComponent(key) + (download ? '?download=1' : '');
  }

  function typeLabel(paper) {
    return String((paper && (paper.file_type || paper.original_name || '')) || '')
      .replace(/^\./, '').toUpperCase() || 'FILE';
  }

  function typeClass(paper) {
    const t = String(paper && (paper.file_type || '')).toLowerCase();
    if (t === 'pdf') return 'pdf';
    if (['html', 'htm'].includes(t)) return 'html';
    if (['doc', 'docx'].includes(t)) return 'docx';
    if (['svg', 'png', 'jpg', 'jpeg', 'webp', 'gif'].includes(t)) return 'svg';
    return 'txt';
  }

  function formatSize(bytes) {
    const n = Number(bytes || 0);
    if (!n) return '';
    if (n < 1024) return n + ' B';
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
    return (n / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function canPreview(paper) {
    const t = String(paper.file_type || '').toLowerCase();
    return paper.previewable || ['pdf', 'html', 'htm', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(t);
  }

  function findGroup(id) { return (state.catalog.groups || []).find((g) => g.id === id); }
  function findClass(group, id) { return ((group && group.classes) || []).find((c) => c.id === id); }
  function findSubject(klass, id) { return ((klass && klass.subjects) || []).find((s) => s.id === id); }
  function findPaper(subject, id) { return ((subject && subject.papers) || []).find((p) => p.id === id); }

  function crumbs(items) {
    return `
      <div class="er-crumbs-bar">
        <nav class="er-crumbs" aria-label="Breadcrumb">
          <button type="button" data-go="#/"><i class="fas fa-house"></i> Home</button>
          ${items.map((item, i) => {
            if (!item.href || i === items.length - 1) {
              return `<span class="sep"><i class="fas fa-chevron-right"></i></span><span class="current">${esc(item.label)}</span>`;
            }
            return `<span class="sep"><i class="fas fa-chevron-right"></i></span><button type="button" data-go="${esc(item.href)}">${esc(item.label)}</button>`;
          }).join('')}
        </nav>
        ${items.length > 0 && items[0].href ? `
          <button type="button" class="er-nav-back-btn" data-go="${esc(items[items.length - 2] ? items[items.length - 2].href || '#/' : '#/')}">
            <i class="fas fa-arrow-left"></i> Back
          </button>` : ''}
      </div>`;
  }

  function landing() {
    const cat = state.catalog || {};
    const groups = cat.groups || [];
    let totalClasses = 0;
    let totalSubjects = 0;
    let totalPapers = 0;

    groups.forEach((g) => {
      (g.classes || []).forEach((c) => {
        totalClasses++;
        (c.subjects || []).forEach((s) => {
          totalSubjects++;
          totalPapers += (s.papers || []).length;
        });
      });
    });

    const totalResults = (cat.results || []).length;

    const adminCard = state.canAdmin ? `
      <div class="er-landing-card admin" role="button" tabindex="0" data-go="#/admin">
        <div class="er-card-icon-wrap" aria-hidden="true"><i class="fas fa-sliders"></i></div>
        <h2>Admin Dashboard</h2>
        <p>Manage groups, classes, subjects, practice question papers, and student results. All updates publish without code changes.</p>
        <span class="er-card-cta-btn">Open Control Panel <i class="fas fa-arrow-right"></i></span>
      </div>` : '';

    return `
      <section class="er-hero">
        <div class="er-hero-content">
          <div class="er-hero-title-group">
            <h1><i class="fas fa-graduation-cap"></i> Excel Results <span class="er-hero-badge">Academic Hub</span></h1>
            <p>Access published student examination results and explore practice question papers organized by group, class, and subject.</p>
          </div>
          <div class="er-hero-stats">
            <div class="er-hero-stat-pill"><strong>${groups.length}</strong><span>Groups</span></div>
            <div class="er-hero-stat-pill"><strong>${totalSubjects}</strong><span>Subjects</span></div>
            <div class="er-hero-stat-pill"><strong>${totalPapers}</strong><span>Papers</span></div>
            <div class="er-hero-stat-pill"><strong>${totalResults}</strong><span>Results</span></div>
          </div>
        </div>
      </section>

      <div class="er-landing-grid">
        <div class="er-landing-card results" role="button" tabindex="0" data-go="#/results">
          <div class="er-card-icon-wrap" aria-hidden="true"><i class="fas fa-chart-pie"></i></div>
          <h2>Student Results</h2>
          <p>Search and look up examination scores by student name, roll number, registration number, class, or session.</p>
          <span class="er-card-cta-btn">View Examination Results <i class="fas fa-arrow-right"></i></span>
        </div>

        <div class="er-landing-card papers" role="button" tabindex="0" data-go="#/papers">
          <div class="er-card-icon-wrap" aria-hidden="true"><i class="fas fa-book-open"></i></div>
          <h2>Question Papers</h2>
          <p>Browse downloadable and interactive practice papers in PDF, HTML, Word, and Image formats across all classes.</p>
          <span class="er-card-cta-btn">Explore Question Papers <i class="fas fa-arrow-right"></i></span>
        </div>

        ${adminCard}
      </div>`;
  }

  function papersView() {
    const r = state.route;
    const groups = state.catalog.groups || [];

    // 1. Group level
    if (!r.group) {
      if (!groups.length) return crumbs([]) + empty('No published groups are available right now.');
      const filtered = groups.filter(matchesQuery);
      return crumbs([{ label: 'Question Papers' }]) +
        toolbar() +
        (filtered.length ? `<div class="er-grid">${filtered.map((g) => {
          const classCount = (g.classes || []).length;
          let pCount = 0;
          (g.classes || []).forEach((c) => (c.subjects || []).forEach((s) => { pCount += (s.papers || []).length; }));
          return `
            <div class="er-item-card" role="button" tabindex="0" data-go="#/papers/${esc(g.id)}">
              <div class="er-item-card-header">
                <div class="er-item-icon"><i class="fas fa-layer-group"></i></div>
                <div class="er-item-title-wrap">
                  <h3>${esc(g.name)}</h3>
                </div>
              </div>
              <p>${esc(g.description || `${classCount} classes available in this group.`)}</p>
              <div class="er-item-footer">
                <span class="er-badge-count"><i class="fas fa-chalkboard"></i> ${classCount} Classes</span>
                <span class="er-badge-count"><i class="fas fa-file-lines"></i> ${pCount} Papers</span>
                <span class="er-card-arrow"><i class="fas fa-arrow-right"></i></span>
              </div>
            </div>`;
        }).join('')}</div>` : empty('No groups match your search.'));
    }

    const group = findGroup(r.group);
    if (!group) return crumbs([]) + empty('That group was not found.');

    // 2. Class level
    if (!r.klass) {
      const classes = (group.classes || []).filter(matchesQuery);
      return crumbs([
        { label: 'Question Papers', href: '#/papers' },
        { label: group.name },
      ]) +
      toolbar() +
      (classes.length ? `<div class="er-grid">${classes.map((c) => {
        const subCount = (c.subjects || []).length;
        let pCount = 0;
        (c.subjects || []).forEach((s) => { pCount += (s.papers || []).length; });
        return `
          <div class="er-item-card" role="button" tabindex="0" data-go="#/papers/${esc(group.id)}/${esc(c.id)}">
            <div class="er-item-card-header">
              <div class="er-item-icon"><i class="fas fa-chalkboard-user"></i></div>
              <div class="er-item-title-wrap">
                <h3>${esc(c.name)}</h3>
              </div>
            </div>
            <p>${esc(group.name)} · Class Level Curriculum</p>
            <div class="er-item-footer">
              <span class="er-badge-count"><i class="fas fa-book"></i> ${subCount} Subjects</span>
              <span class="er-badge-count"><i class="fas fa-file-lines"></i> ${pCount} Papers</span>
              <span class="er-card-arrow"><i class="fas fa-arrow-right"></i></span>
            </div>
          </div>`;
      }).join('')}</div>` : empty('No classes in this group match your search.'));
    }

    const klass = findClass(group, r.klass);
    if (!klass) return crumbs([{ label: 'Question Papers', href: '#/papers' }]) + empty('That class was not found.');

    // 3. Subject level
    if (!r.subject) {
      const subjects = (klass.subjects || []).filter(matchesQuery);
      return crumbs([
        { label: 'Question Papers', href: '#/papers' },
        { label: group.name, href: '#/papers/' + group.id },
        { label: klass.name },
      ]) +
      toolbar() +
      (subjects.length ? `<div class="er-grid">${subjects.map((s) => {
        const pCount = (s.papers || []).length;
        return `
          <div class="er-item-card" role="button" tabindex="0" data-go="#/papers/${esc(group.id)}/${esc(klass.id)}/${esc(s.id)}">
            <div class="er-item-card-header">
              <div class="er-item-icon"><i class="fas fa-shapes"></i></div>
              <div class="er-item-title-wrap">
                <h3>${esc(s.name)}</h3>
              </div>
            </div>
            <p>${esc(group.name)} · ${esc(klass.name)}</p>
            <div class="er-item-footer">
              <span class="er-badge-count"><i class="fas fa-file-circle-check"></i> ${pCount} Practice Papers</span>
              <span class="er-card-arrow"><i class="fas fa-arrow-right"></i></span>
            </div>
          </div>`;
      }).join('')}</div>` : empty('No subjects in this class match your search.'));
    }

    const subject = findSubject(klass, r.subject);
    if (!subject) return crumbs([{ label: 'Question Papers', href: '#/papers' }]) + empty('That subject was not found.');

    // 4. Papers list
    let papers = (subject.papers || []).filter((p) => {
      const q = state.query.trim().toLowerCase();
      if (state.tagFilter && !(p.tags || []).includes(state.tagFilter)) return false;
      if (!q) return true;
      return [p.title, p.description, (p.tags || []).join(' '), p.file_type].join(' ').toLowerCase().includes(q);
    });

    papers = sortPapers(papers);
    const start = (state.page - 1) * state.pageSize;
    const pageRows = papers.slice(start, start + state.pageSize);
    const selected = r.paper ? findPaper(subject, r.paper) : null;

    // Collect all available tags in this subject
    const allTags = new Set();
    (subject.papers || []).forEach((p) => (p.tags || []).forEach((t) => allTags.add(t)));

    return crumbs([
      { label: 'Question Papers', href: '#/papers' },
      { label: group.name, href: '#/papers/' + group.id },
      { label: klass.name, href: '#/papers/' + group.id + '/' + klass.id },
      { label: subject.name },
    ]) +
    toolbar(true, Array.from(allTags)) +
    (papers.length ? `<div class="er-paper-list">${pageRows.map((p) => paperCard(p, group, klass, subject)).join('')}</div>` : empty('No practice question papers match your search or filter.')) +
    pager(papers.length) +
    (selected ? paperPreviewModal(selected, group, klass, subject) : '');
  }

  function paperCard(p, group, klass, subject) {
    const fType = typeClass(p);
    const sz = formatSize(p.size_bytes);
    return `
      <article class="er-paper-card">
        <div class="er-paper-main">
          <div class="er-format-icon ${fType}">${esc(typeLabel(p))}</div>
          <div class="er-paper-info">
            <h3>${esc(p.title)}</h3>
            <p>${esc(p.description || 'Comprehensive practice paper with questions and exercises.')}</p>
            <div class="er-paper-tags">
              <span class="er-tag-chip"><i class="fas fa-calendar-day"></i> ${esc(p.date_added || 'Recently added')}</span>
              ${sz ? `<span class="er-tag-chip"><i class="fas fa-weight-hanging"></i> ${esc(sz)}</span>` : ''}
              ${(p.tags || []).map((t) => `<span class="er-tag-chip">#${esc(t)}</span>`).join('')}
            </div>
          </div>
        </div>
        <div class="er-paper-actions">
          ${p.storage_key ? `
            <a class="er-btn" href="${esc(fileUrl(p))}" target="_blank" rel="noopener">
              <i class="fas fa-arrow-up-right-from-square"></i> Open
            </a>
            <a class="er-btn secondary" href="${esc(fileUrl(p, true))}" download>
              <i class="fas fa-download"></i> Download
            </a>` : ''}
          ${canPreview(p) && p.storage_key ? `
            <button class="er-btn ghost" type="button" data-go="#/papers/${esc(group.id)}/${esc(klass.id)}/${esc(subject.id)}/${esc(p.id)}">
              <i class="fas fa-eye"></i> Preview
            </button>` : ''}
        </div>
      </article>`;
  }

  function paperPreviewModal(p, group, klass, subject) {
    const url = fileUrl(p);
    const t = String(p.file_type || '').toLowerCase();
    let viewportHtml = '';

    if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(t)) {
      viewportHtml = `<img alt="${esc(p.title)}" src="${esc(url)}">`;
    } else if (['html', 'htm', 'txt'].includes(t)) {
      viewportHtml = `<iframe title="${esc(p.title)}" src="${esc(url)}" sandbox=""></iframe>`;
    } else if (t === 'pdf') {
      viewportHtml = `<embed type="application/pdf" src="${esc(url)}#toolbar=1&navpanes=0">`;
    } else {
      viewportHtml = `
        <div class="er-preview-fallback">
          <div class="er-preview-fallback-icon"><i class="fas fa-file-arrow-down"></i></div>
          <h3>${esc(p.title)}</h3>
          <p>This file is in <strong>.${esc(t.toUpperCase())}</strong> format. Click below to download and open it in your preferred viewer.</p>
          <div class="er-actions" style="justify-content:center;margin-top:16px;">
            <a class="er-btn secondary" href="${esc(fileUrl(p, true))}" download><i class="fas fa-download"></i> Download ${esc(t.toUpperCase())}</a>
          </div>
        </div>`;
    }

    const backHref = `#/papers/${group.id}/${klass.id}/${subject.id}`;

    return `
      <div class="er-modal-backdrop" data-close-modal="${esc(backHref)}">
        <div class="er-modal-preview-card" onclick="event.stopPropagation()">
          <div class="er-preview-header">
            <div class="er-preview-title-group">
              <h3><i class="fas fa-file-lines"></i> ${esc(p.title)}</h3>
              <p>${esc(group.name)} · ${esc(klass.name)} · ${esc(subject.name)} (${esc(typeLabel(p))})</p>
            </div>
            <div class="er-preview-actions">
              <a class="er-btn ghost" href="${esc(fileUrl(p))}" target="_blank" rel="noopener"><i class="fas fa-external-link-alt"></i> Open Tab</a>
              <a class="er-btn secondary" href="${esc(fileUrl(p, true))}" download><i class="fas fa-download"></i> Download</a>
              <button type="button" class="er-preview-close-btn" data-go="${esc(backHref)}" aria-label="Close Preview"><i class="fas fa-times"></i></button>
            </div>
          </div>
          <div class="er-preview-viewport">
            ${viewportHtml}
          </div>
        </div>
      </div>`;
  }

  function resultsView() {
    if (cfg.requireAuthForResults && !publicLoggedIn()) {
      return crumbs([{ label: 'Results' }]) + `
        <div class="er-empty-box">
          <div class="er-empty-icon"><i class="fas fa-lock"></i></div>
          <h2>Login Required to View Results</h2>
          <p>Student examination results are protected. Please log in using your Roll Number and Password via the top header button, then return here.</p>
          <div class="er-actions" style="justify-content:center;margin-top:18px;">
            <button class="er-btn results-btn" type="button" onclick="if(window.openLoginModal) window.openLoginModal();"><i class="fas fa-key"></i> Open Login Dialog</button>
          </div>
        </div>`;
    }

    const rows = filterResults(state.catalog.results || []);
    const groups = state.catalog.groups || [];
    const classes = [];
    groups.forEach((g) => (g.classes || []).forEach((c) => classes.push({ id: c.id, name: `${g.name} · ${c.name}` })));
    const sessions = state.catalog.sessions || [];
    const exams = state.catalog.examinations || [];

    // Calculate quick metrics
    let totalMarks = 0;
    let totalMaxMarks = 0;
    let validMarksCount = 0;
    let highestPct = 0;
    const gradeCounts = {};

    rows.forEach((r) => {
      const m = Number(r.marks);
      const mm = Number(r.max_marks);
      if (!isNaN(m) && !isNaN(mm) && mm > 0) {
        totalMarks += m;
        totalMaxMarks += mm;
        validMarksCount++;
        const pct = (m / mm) * 100;
        if (pct > highestPct) highestPct = pct;
      }
      if (r.grade) {
        gradeCounts[r.grade] = (gradeCounts[r.grade] || 0) + 1;
      }
    });

    const avgPct = totalMaxMarks > 0 ? ((totalMarks / totalMaxMarks) * 100).toFixed(1) : '—';
    const topPct = highestPct > 0 ? highestPct.toFixed(1) + '%' : '—';

    const start = (state.page - 1) * state.pageSize;
    const pageRows = rows.slice(start, start + state.pageSize);

    return crumbs([{ label: 'Results' }]) + `
      <div class="er-toolbar">
        <div class="er-search-box">
          <i class="fas fa-magnifying-glass"></i>
          <input aria-label="Search results" placeholder="Search by student name, roll number, registration, class, or exam..." value="${esc(state.resultQuery)}" data-result-q>
        </div>
        <select aria-label="Group filter" data-rf="group">${opt('', 'All Groups', state.resultFilters.group)}${groups.map((g) => opt(g.id, g.name, state.resultFilters.group)).join('')}</select>
        <select aria-label="Class filter" data-rf="className">${opt('', 'All Classes', state.resultFilters.className)}${classes.map((c) => opt(c.id, c.name, state.resultFilters.className)).join('')}</select>
        <select aria-label="Subject filter" data-rf="subject">${opt('', 'All Subjects', state.resultFilters.subject)}${uniqueResultSubjects(groups).map((s) => opt(s.id, s.name, state.resultFilters.subject)).join('')}</select>
        <select aria-label="Session filter" data-rf="session">${opt('', 'All Sessions', state.resultFilters.session)}${sessions.map((s) => opt(s.id, s.name, state.resultFilters.session)).join('')}</select>
        <select aria-label="Exam filter" data-rf="exam">${opt('', 'All Examinations', state.resultFilters.exam)}${exams.map((e) => opt(e.id, e.name, state.resultFilters.exam)).join('')}</select>
        <div class="er-view-toggle" aria-label="View toggle">
          <button type="button" class="er-view-toggle-btn ${state.resultsViewMode === 'table' ? 'active' : ''}" data-view-mode="table" title="Table View"><i class="fas fa-table"></i> Table</button>
          <button type="button" class="er-view-toggle-btn ${state.resultsViewMode === 'cards' ? 'active' : ''}" data-view-mode="cards" title="Cards View"><i class="fas fa-grip"></i> Cards</button>
        </div>
      </div>

      <div class="er-results-summary-bar">
        <div class="er-summary-metrics">
          <span class="er-metric-tag"><i class="fas fa-users"></i> Showing: <strong>${uniqueResultCandidates(rows)}</strong> candidates</span>
          <span class="er-metric-tag"><i class="fas fa-chart-line"></i> Average: <strong>${avgPct}%</strong></span>
          <span class="er-metric-tag"><i class="fas fa-award"></i> Top Score: <strong>${topPct}</strong></span>
        </div>
        <div class="er-summary-grades">
          ${Object.entries(gradeCounts).slice(0, 4).map(([grd, count]) => `
            <span class="er-grade-pill ${grd.replace('+', '-plus')}">${esc(grd)}: ${count}</span>
          `).join('')}
        </div>
      </div>

      ${rows.length ? (state.resultsViewMode === 'cards' ? renderResultsCards(pageRows) : renderResultsTable(pageRows)) : empty('No student examination results match the specified criteria.')}
      ${pager(rows.length)}`;
  }

  function renderResultsTable(rows) {
    return `
      <div class="er-table-wrap">
        <table class="er-table">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Roll No.</th>
              <th>Reg. No.</th>
              <th>Group</th>
              <th>Class</th>
              <th>Subject</th>
              <th>Exam</th>
              <th>Session</th>
              <th>Marks</th>
              <th>Grade</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map((r) => {
              const gClass = (r.grade || '').replace('+', '-plus');
              return `
                <tr>
                  <td><strong>${esc(r.student_name)}</strong></td>
                  <td><code>${esc(r.roll_number)}</code></td>
                  <td><small class="er-muted">${esc(r.registration_number || '—')}</small></td>
                  <td>${esc(r.group_name || '—')}</td>
                  <td>${esc(r.class_name || '—')}</td>
                  <td>${esc(r.subject_name || '—')}</td>
                  <td>${esc(r.examination_name || '—')}</td>
                  <td>${esc(r.session_name || '—')}</td>
                  <td><strong>${esc(r.marks)}</strong> / ${esc(r.max_marks)}</td>
                  <td><span class="er-grade-pill ${gClass}">${esc(r.grade || '—')}</span></td>
                </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>`;
  }

  function renderResultsCards(rows) {
    return `
      <div class="er-results-card-grid">
        ${rows.map((r) => {
          const m = Number(r.marks) || 0;
          const mm = Number(r.max_marks) || 1;
          const pct = Math.min(100, Math.round((m / mm) * 100));
          const gClass = (r.grade || '').replace('+', '-plus');
          return `
            <article class="er-student-result-card">
              <div class="er-student-card-head">
                <div class="er-student-card-title">
                  <h4>${esc(r.student_name)}</h4>
                  <span class="er-student-roll-chip">Roll: ${esc(r.roll_number)} ${r.registration_number ? `· Reg: ${esc(r.registration_number)}` : ''}</span>
                </div>
                <span class="er-grade-pill ${gClass}">${esc(r.grade || '—')}</span>
              </div>
              <div class="er-student-meta-row">
                <span class="er-tag-chip"><i class="fas fa-layer-group"></i> ${esc(r.group_name || 'Group')}</span>
                <span class="er-tag-chip"><i class="fas fa-chalkboard"></i> ${esc(r.class_name || 'Class')}</span>
                <span class="er-tag-chip"><i class="fas fa-book"></i> ${esc(r.subject_name || 'Subject')}</span>
              </div>
              <div class="er-student-meta-row">
                <span class="er-tag-chip"><i class="fas fa-file-signature"></i> ${esc(r.examination_name || 'Exam')}</span>
                <span class="er-tag-chip"><i class="fas fa-calendar"></i> ${esc(r.session_name || 'Session')}</span>
              </div>
              <div class="er-marks-progress-wrap">
                <div class="er-marks-progress-label">
                  <span>Score: <strong>${esc(r.marks)} / ${esc(r.max_marks)}</strong></span>
                  <span>${pct}%</span>
                </div>
                <div class="er-progress-track">
                  <div class="er-progress-fill" style="width: ${pct}%;"></div>
                </div>
              </div>
            </article>`;
        }).join('')}
      </div>`;
  }

  function filterResults(rows) {
    const q = state.resultQuery.trim().toLowerCase();
    const ownRoll = cfg.mode === 'public' && cfg.requireAuthForResults && cfg.resultsScope === 'own' ? publicAuthRoll() : '';
    return rows.filter((r) => {
      if (ownRoll && String(r.roll_number || '').trim().toLowerCase() !== ownRoll) return false;
      if (state.resultFilters.group && r.group_id !== state.resultFilters.group) return false;
      if (state.resultFilters.className && r.class_id !== state.resultFilters.className) return false;
      if (state.resultFilters.subject && r.subject_id !== state.resultFilters.subject) return false;
      if (state.resultFilters.session && r.session_id !== state.resultFilters.session) return false;
      if (state.resultFilters.exam && r.examination_id !== state.resultFilters.exam) return false;
      if (!q) return true;
      return [
        r.student_name,
        r.roll_number,
        r.registration_number,
        r.class_name,
        r.subject_name,
        r.examination_name,
        r.group_name,
        r.session_name,
      ].join(' ').toLowerCase().includes(q);
    });
  }

  function uniqueResultSubjects(groups) {
    const seen = new Set();
    const result = [];
    groups.forEach((g) => (g.classes || []).forEach((c) => (c.subjects || []).forEach((s) => {
      if (!seen.has(s.id)) {
        seen.add(s.id);
        result.push({ id: s.id, name: s.name });
      }
    })));
    return result.sort((a, b) => String(a.name).localeCompare(String(b.name)));
  }

  function uniqueResultCandidates(rows) {
    return new Set(rows.map((r) => String(r.roll_number || r.student_name || r.id || '').trim().toLowerCase())).size;
  }

  // ==========================================================================
  // Admin Dashboard Views
  // ==========================================================================
  function adminView() {
    if (!state.canAdmin) {
      return empty('Admin authentication is required to access the management dashboard.');
    }
    const cat = state.adminCatalog;
    if (!cat) return '<div class="er-skel"></div><div class="er-skel"></div>';
    const section = state.adminSection;

    return crumbs([{ label: 'Admin Dashboard' }]) + `
      <div class="er-admin-shell">
        <div class="er-admin-topbar">
          <div class="er-admin-nav-tabs" role="tablist">
            ${[
              ['tree', 'fas fa-sitemap', 'Structure'],
              ['papers', 'fas fa-file-circle-plus', 'Question Papers'],
              ['results', 'fas fa-table-list', 'Student Results'],
              ['sessions', 'fas fa-calendar-check', 'Sessions & Exams'],
              ['publish', 'fas fa-cloud-arrow-up', 'Publish & Backup'],
            ].map(([id, icon, label]) => `
              <button type="button" role="tab" class="er-admin-tab-btn ${section === id ? 'active' : ''}" data-admin-section="${id}">
                <i class="${icon}"></i> ${label}
              </button>
            `).join('')}
          </div>
          <div class="er-actions" style="margin:0;">
            <button class="er-btn secondary" type="button" data-save-admin><i class="fas fa-floppy-disk"></i> Save Changes</button>
          </div>
        </div>

        <div class="er-admin-body">
          ${state.formError ? `<div class="er-error" style="margin-bottom:16px;"><i class="fas fa-circle-exclamation"></i> ${esc(state.formError)}</div>` : ''}
          ${section === 'tree' ? adminTree(cat) :
            section === 'papers' ? adminPapers(cat) :
            section === 'results' ? adminResults(cat) :
            section === 'sessions' ? adminSessions(cat) :
            adminPublish(cat)}
        </div>
      </div>`;
  }

  function adminTree(cat) {
    return `
      <div class="er-actions" style="margin-bottom:18px;">
        <button class="er-btn" type="button" data-add="group"><i class="fas fa-plus"></i> Add Group</button>
      </div>
      <div class="er-tree">
        ${(cat.groups || []).map((g, gi) => `
          <details class="er-tree-node" open>
            <summary style="cursor:pointer;font-weight:700;font-size:1.1rem;display:flex;align-items:center;gap:10px;">
              <i class="fas fa-layer-group" style="color:var(--er-papers);"></i> ${esc(g.name)}
              <span class="er-badge-count" style="margin-left:auto;">${(g.classes || []).length} Classes</span>
            </summary>
            <div style="padding:14px 0 6px;">
              ${entityFields('groups.' + gi, g, ['name', 'description', 'sort_order', 'published'])}
              <div class="er-actions" style="margin:10px 0 16px;">
                <button class="er-btn ghost" type="button" data-add="class" data-gi="${gi}"><i class="fas fa-plus"></i> Add Class to ${esc(g.name)}</button>
                <button class="er-btn ghost" type="button" data-move="group" data-gi="${gi}" data-dir="-1" title="Move Up"><i class="fas fa-arrow-up"></i></button>
                <button class="er-btn ghost" type="button" data-move="group" data-gi="${gi}" data-dir="1" title="Move Down"><i class="fas fa-arrow-down"></i></button>
                <button class="er-btn danger" type="button" data-del="group" data-gi="${gi}"><i class="fas fa-trash"></i> Delete Group</button>
              </div>

              <div style="margin-left:20px;border-left:2px solid var(--er-line);padding-left:14px;">
                ${(g.classes || []).map((c, ci) => `
                  <details class="er-tree-node" open style="margin-top:10px;">
                    <summary style="cursor:pointer;font-weight:600;">
                      <i class="fas fa-chalkboard" style="color:var(--er-results);"></i> ${esc(c.name)} (${(c.subjects || []).length} Subjects)
                    </summary>
                    <div style="padding:10px 0 4px;">
                      ${entityFields('groups.' + gi + '.classes.' + ci, c, ['name', 'sort_order', 'published'])}
                      <div class="er-actions" style="margin:8px 0 14px;">
                        <button class="er-btn ghost" type="button" data-add="subject" data-gi="${gi}" data-ci="${ci}"><i class="fas fa-plus"></i> Add Subject</button>
                        <button class="er-btn danger" type="button" data-del="class" data-gi="${gi}" data-ci="${ci}"><i class="fas fa-trash"></i> Delete Class</button>
                      </div>

                      <div style="margin-left:20px;border-left:2px solid var(--er-line);padding-left:14px;">
                        ${(c.subjects || []).map((s, si) => `
                          <div class="er-tree-node" style="margin-top:8px;">
                            <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
                              <strong><i class="fas fa-book"></i> ${esc(s.name)}</strong>
                              <span class="er-badge-count">${(s.papers || []).length} Papers</span>
                            </div>
                            ${entityFields('groups.' + gi + '.classes.' + ci + '.subjects.' + si, s, ['name', 'sort_order', 'published'])}
                            <div class="er-actions" style="margin-top:6px;">
                              <button class="er-btn danger" type="button" data-del="subject" data-gi="${gi}" data-ci="${ci}" data-si="${si}"><i class="fas fa-trash"></i> Delete Subject</button>
                            </div>
                          </div>
                        `).join('')}
                      </div>
                    </div>
                  </details>
                `).join('')}
              </div>
            </div>
          </details>
        `).join('') || empty('No groups configured. Click "Add Group" to get started.')}
      </div>`;
  }

  function entityFields(prefix, obj, fields) {
    return `
      <div class="er-form-grid" style="margin:10px 0;">
        ${fields.map((f) => {
          if (f === 'published') {
            return `
              <div class="er-field" style="justify-content:center;">
                <label>Status</label>
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;text-transform:none;font-size:0.9rem;">
                  <input type="checkbox" data-path="${prefix}.${f}" ${obj[f] !== false ? 'checked' : ''}>
                  <span>Published (Visible to public)</span>
                </label>
              </div>`;
          }
          if (f === 'description') {
            return `
              <div class="er-field" style="grid-column: 1 / -1;">
                <label>Description</label>
                <textarea data-path="${prefix}.${f}" rows="2">${esc(obj[f] || '')}</textarea>
              </div>`;
          }
          return `
            <div class="er-field">
              <label>${esc(f.replace('_', ' '))}</label>
              <input data-path="${prefix}.${f}" value="${esc(obj[f] == null ? '' : obj[f])}">
            </div>`;
        }).join('')}
      </div>`;
  }

  function adminPapers(cat) {
    const subjects = [];
    (cat.groups || []).forEach((g, gi) => {
      (g.classes || []).forEach((c, ci) => {
        (c.subjects || []).forEach((s, si) => {
          subjects.push({
            gi, ci, si,
            label: `${g.name} → ${c.name} → ${s.name}`,
            subject: s,
          });
        });
      });
    });

    return `
      <p class="er-muted" style="margin-top:0;">Upload PDF, HTML, Word DOCX, Image, and other practice paper formats. Attached papers remain drafts on the LAN until marked Published.</p>
      ${subjects.map((row) => `
        <section class="er-form-card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <h3><i class="fas fa-folder-open" style="color:var(--er-papers);"></i> ${esc(row.label)}</h3>
            <label class="er-btn secondary" style="cursor:pointer;">
              <i class="fas fa-cloud-arrow-up"></i> Upload Practice Paper
              <input hidden type="file" data-new-paper="${row.gi}:${row.ci}:${row.si}">
            </label>
          </div>
          ${(row.subject.papers || []).map((p, pi) => `
            <div style="border-top:1px solid var(--er-line);padding:14px 0;display:grid;gap:10px;">
              <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;">
                <div>
                  <strong>${esc(p.title)}</strong>
                  <span class="er-tag-chip" style="margin-left:8px;">${esc(typeLabel(p))}</span>
                  <span class="er-tag-chip">${p.published !== false ? '<span style="color:#059669;">● Published</span>' : '<span style="color:#d97706;">○ Draft</span>'}</span>
                </div>
                <div class="er-actions" style="margin:0;">
                  <label class="er-btn ghost" style="cursor:pointer;padding:6px 12px;font-size:0.8rem;">
                    <i class="fas fa-repeat"></i> Replace File
                    <input hidden type="file" data-upload="${row.gi}:${row.ci}:${row.si}:${pi}">
                  </label>
                  <button class="er-btn danger" type="button" style="padding:6px 12px;font-size:0.8rem;" data-del="paper" data-gi="${row.gi}" data-ci="${row.ci}" data-si="${row.si}" data-pi="${pi}">
                    <i class="fas fa-trash"></i> Delete
                  </button>
                </div>
              </div>
              ${entityFields(`groups.${row.gi}.classes.${row.ci}.subjects.${row.si}.papers.${pi}`, p, ['title', 'description', 'date_added', 'published'])}
            </div>
          `).join('') || '<p class="er-muted">No practice papers attached to this subject yet.</p>'}
        </section>
      `).join('') || empty('Create groups, classes, and subjects in the Structure tab first.')}`;
  }

  function selectOptions(items, value, labelKey = 'name') {
    return opt('', '— Select —', value) + items.map((item) => opt(item.id, item[labelKey], value)).join('');
  }

  function adminResults(cat) {
    const preview = state.csvPreviewRows;
    const groups = cat.groups || [];
    const classes = [];
    const subjects = [];
    groups.forEach((g) => (g.classes || []).forEach((c) => {
      classes.push({ id: c.id, name: `${g.name} · ${c.name}` });
      (c.subjects || []).forEach((s) => subjects.push({ id: s.id, name: `${g.name} · ${c.name} · ${s.name}` }));
    }));
    return `
      <div class="er-actions" style="margin-bottom:18px;">
        <button class="er-btn" type="button" data-add="result"><i class="fas fa-plus"></i> Add Single Result</button>
      </div>

      <div class="er-form-card">
        <h3><i class="fas fa-file-csv"></i> Bulk CSV Import</h3>
        <p class="er-muted" style="font-size:0.88rem;margin:4px 0 12px;">
          Expected columns: <code>student_name, roll_number, registration_number, group, class, subject, examination, session, marks, max_marks, grade</code>
        </p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
          <input type="file" accept=".csv,text/csv" data-import-csv>
        </div>
        ${preview ? `
          <div class="er-import-preview" style="margin-top:14px;padding:14px;border:1px solid var(--er-line);border-radius:12px;background:var(--er-surface);">
            <strong>Import preview</strong>
            <span class="er-muted" style="margin-left:8px;">${preview.row_count} rows · ${preview.valid_count} valid</span>
            ${preview.issues.length ? `
              <div class="er-error" style="margin-top:10px;"><i class="fas fa-circle-exclamation"></i> ${esc(preview.issues.slice(0, 8).join(' · '))}${preview.issues.length > 8 ? ' …' : ''}</div>
              <p class="er-muted" style="margin:8px 0 0;">Nothing was written. Fix the CSV and preview it again.</p>
            ` : `
              <div class="er-success" style="margin-top:10px;"><i class="fas fa-circle-check"></i> All rows map to the current catalog and have valid marks.</div>
              <button class="er-btn" type="button" style="margin-top:10px;" data-confirm-csv>Import ${preview.valid_count} rows</button>
            `}
          </div>` : ''}
      </div>

      <div class="er-table-wrap">
        <table class="er-table">
          <thead>
            <tr>
              <th>Student Name</th>
              <th>Roll No.</th>
              <th>Reg. No.</th>
              <th>Group ID / Name</th>
              <th>Class ID / Name</th>
              <th>Subject ID / Name</th>
              <th>Exam ID / Name</th>
              <th>Session ID / Name</th>
              <th>Marks</th>
              <th>Max</th>
              <th>Grade</th>
              <th>Pub</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${(cat.results || []).map((r, i) => `
              <tr>
                <td><input style="min-width:120px;" data-path="results.${i}.student_name" value="${esc(r.student_name || '')}"></td>
                <td><input style="width:80px;" data-path="results.${i}.roll_number" value="${esc(r.roll_number || '')}"></td>
                <td><input style="width:80px;" data-path="results.${i}.registration_number" value="${esc(r.registration_number || '')}"></td>
                <td><select style="width:130px;" data-path="results.${i}.group_id">${selectOptions(groups, r.group_id || '')}</select></td>
                <td><select style="width:150px;" data-path="results.${i}.class_id">${selectOptions(classes, r.class_id || '')}</select></td>
                <td><select style="width:170px;" data-path="results.${i}.subject_id">${selectOptions(subjects, r.subject_id || '')}</select></td>
                <td><select style="width:130px;" data-path="results.${i}.examination_id">${selectOptions(cat.examinations || [], r.examination_id || '')}</select></td>
                <td><select style="width:110px;" data-path="results.${i}.session_id">${selectOptions(cat.sessions || [], r.session_id || '')}</select></td>
                <td><input style="width:50px;" data-path="results.${i}.marks" value="${esc(r.marks == null ? '' : r.marks)}"></td>
                <td><input style="width:50px;" data-path="results.${i}.max_marks" value="${esc(r.max_marks == null ? '' : r.max_marks)}"></td>
                <td><input style="width:50px;" data-path="results.${i}.grade" value="${esc(r.grade || '')}"></td>
                <td><input type="checkbox" data-path="results.${i}.published" ${r.published !== false ? 'checked' : ''}></td>
                <td><button class="er-btn danger" type="button" style="padding:4px 8px;" data-del="result" data-ri="${i}"><i class="fas fa-trash"></i></button></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
  }

  function adminSessions(cat) {
    return `
      <div class="er-actions" style="margin-bottom:18px;">
        <button class="er-btn" type="button" data-add="session"><i class="fas fa-plus"></i> Add Session</button>
        <button class="er-btn secondary" type="button" data-add="exam"><i class="fas fa-plus"></i> Add Examination</button>
      </div>

      <div class="er-form-card">
        <h3><i class="fas fa-calendar-days"></i> Academic Sessions</h3>
        ${(cat.sessions || []).map((s, i) => `
          <div class="er-tree-node" style="margin-top:8px;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <strong>${esc(s.name)}</strong>
              <button class="er-btn danger" type="button" style="padding:4px 8px;" data-del="session" data-si="${i}"><i class="fas fa-trash"></i> Delete</button>
            </div>
            ${entityFields('sessions.' + i, s, ['name', 'sort_order', 'published'])}
          </div>
        `).join('')}
      </div>

      <div class="er-form-card">
        <h3><i class="fas fa-file-pen"></i> Examinations</h3>
        ${(cat.examinations || []).map((e, i) => `
          <div class="er-tree-node" style="margin-top:8px;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <strong>${esc(e.name)}</strong>
              <button class="er-btn danger" type="button" style="padding:4px 8px;" data-del="exam" data-ei="${i}"><i class="fas fa-trash"></i> Delete</button>
            </div>
            ${entityFields('examinations.' + i, e, ['name', 'session_id', 'sort_order', 'published'])}
          </div>
        `).join('')}
      </div>`;
  }

  function adminPublish() {
    return `
      <div class="er-form-card">
        <h3><i class="fas fa-cloud-arrow-up" style="color:var(--er-primary);"></i> Publish to Cloudflare Public Site</h3>
        <p class="er-muted">
          Generates a sanitized <code>catalog.json</code> containing only published items and copies attached files into <code>public_site/excel_results/</code>.
          Then, click <strong>Force Publish</strong> in the LAN scoreboard header to push the update to Cloudflare Pages.
        </p>
        <div class="er-actions">
          <button class="er-btn" type="button" data-publish><i class="fas fa-rocket"></i> Update Public Snapshot</button>
        </div>
      </div>

      <div class="er-form-card">
        <h3><i class="fas fa-download"></i> Backup & Data Portability</h3>
        <p class="er-muted">Export complete Excel Results database as JSON or restore from a previously saved backup file.</p>
        <div class="er-actions">
          <a class="er-btn ghost" href="${esc(cfg.exportUrl)}" download><i class="fas fa-file-export"></i> Download Backup JSON</a>
        </div>
        <div class="er-field" style="margin-top:16px;">
          <label>Restore Database from Backup JSON</label>
          <input type="file" accept="application/json" data-import-catalog>
        </div>
      </div>`;
  }

  function matchesQuery(item) {
    const q = state.query.trim().toLowerCase();
    if (!q) return true;
    return [item.name, item.description].join(' ').toLowerCase().includes(q);
  }

  function sortPapers(papers) {
    const copy = papers.slice();
    if (state.sort === 'date') {
      copy.sort((a, b) => String(b.date_added || '').localeCompare(String(a.date_added || '')));
    } else if (state.sort === 'type') {
      copy.sort((a, b) => String(a.file_type || '').localeCompare(String(b.file_type || '')));
    } else {
      copy.sort((a, b) => String(a.title || '').localeCompare(String(b.title || '')));
    }
    return copy;
  }

  function toolbar(withSort, tags) {
    return `
      <div class="er-toolbar">
        <div class="er-search-box">
          <i class="fas fa-magnifying-glass"></i>
          <input aria-label="Search" placeholder="Search by title, description, keywords..." value="${esc(state.query)}" data-q>
        </div>
        ${withSort ? `
          <select aria-label="Sort papers" data-sort>
            <option value="title" ${state.sort === 'title' ? 'selected' : ''}>Sort: Title (A-Z)</option>
            <option value="date" ${state.sort === 'date' ? 'selected' : ''}>Sort: Newest First</option>
            <option value="type" ${state.sort === 'type' ? 'selected' : ''}>Sort: File Type</option>
          </select>` : ''}
        ${tags && tags.length ? `
          <select aria-label="Tag filter" data-tag-filter>
            <option value="">All Tags</option>
            ${tags.map((t) => `<option value="${esc(t)}" ${state.tagFilter === t ? 'selected' : ''}>#${esc(t)}</option>`).join('')}
          </select>` : ''}
      </div>`;
  }

  function pager(total) {
    const pages = Math.max(1, Math.ceil(total / state.pageSize));
    if (pages <= 1) return '';
    return `
      <div class="er-crumbs-bar" style="justify-content:center;margin-top:22px;">
        <div class="er-crumbs">
          <button class="er-btn ghost" style="box-shadow:none;padding:4px 12px;" type="button" data-page="${Math.max(1, state.page - 1)}" ${state.page <= 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i> Previous
          </button>
          <span class="current">Page ${state.page} of ${pages} (${total} total)</span>
          <button class="er-btn ghost" style="box-shadow:none;padding:4px 12px;" type="button" data-page="${Math.min(pages, state.page + 1)}" ${state.page >= pages ? 'disabled' : ''}>
            Next <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>`;
  }

  function empty(msg) {
    return `
      <div class="er-empty-box">
        <div class="er-empty-icon"><i class="fas fa-folder-open"></i></div>
        <h3>No Records Found</h3>
        <p>${esc(msg)}</p>
      </div>`;
  }

  function opt(value, label, selected) {
    return `<option value="${esc(value)}" ${value === selected ? 'selected' : ''}>${esc(label)}</option>`;
  }

  function setPath(obj, path, value) {
    const parts = path.split('.');
    let cur = obj;
    for (let i = 0; i < parts.length - 1; i++) cur = cur[parts[i]];
    cur[parts[parts.length - 1]] = value;
  }

  function uid(prefix) { return prefix + '-' + Math.random().toString(16).slice(2, 10); }

  async function saveAdmin() {
    state.formError = '';
    try {
      const data = await fetchJson(cfg.adminCatalogUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(state.adminCatalog && state.adminCatalog.revision != null ? { 'If-Match': String(state.adminCatalog.revision) } : {}),
        },
        body: JSON.stringify(state.adminCatalog),
      });
      state.adminCatalog = data.data;
      toast('Changes saved successfully! Public snapshot updated on local disk.');
      await loadPublic();
    } catch (err) {
      if (err.status === 409 && cfg.adminCatalogUrl) {
        try {
          const latest = await fetchJson(cfg.adminCatalogUrl);
          state.adminCatalog = latest.data;
          state.formError = 'Another admin saved changes first. Your editor was reloaded; review and save again.';
        } catch (reloadErr) {
          state.formError = err.message;
        }
      } else {
        state.formError = err.message;
      }
    }
    render();
  }

  async function uploadToSubject(gi, ci, si, file, replaceIndex) {
    const body = new FormData();
    body.append('file', file);
    if (replaceIndex != null) {
      const paper = state.adminCatalog.groups[gi].classes[ci].subjects[si].papers[replaceIndex];
      if (paper && paper.id) body.append('paper_id', paper.id);
    }
    try {
      const data = await fetchJson(cfg.uploadUrl, { method: 'POST', body });
      const meta = data.data;
      const subject = state.adminCatalog.groups[gi].classes[ci].subjects[si];
      subject.papers = subject.papers || [];
      const row = {
        id: meta.paper_id,
        title: file.name.replace(/\.[^.]+$/, ''),
        description: '',
        tags: [],
        file_type: meta.file_type,
        original_name: meta.original_name,
        storage_key: meta.storage_key,
        remote_url: meta.remote_url || '',
        size_bytes: meta.size_bytes,
        date_added: meta.date_added,
        published: true,
      };
      if (replaceIndex != null) {
        const prev = subject.papers[replaceIndex];
        subject.papers[replaceIndex] = Object.assign({}, prev, row, {
          title: prev.title,
          description: prev.description,
          published: prev.published,
        });
      } else {
        subject.papers.push(row);
      }
      await saveAdmin();
    } catch (err) {
      state.formError = err.message;
      render();
    }
  }

  function bind(el) {
    el.querySelectorAll('[data-go]').forEach((n) => {
      n.addEventListener('click', () => go(n.getAttribute('data-go')));
    });
    el.querySelectorAll('[data-q]').forEach((n) => {
      n.addEventListener('input', () => { state.query = n.value; state.page = 1; render(); });
    });
    el.querySelectorAll('[data-sort]').forEach((n) => {
      n.addEventListener('change', () => { state.sort = n.value; render(); });
    });
    el.querySelectorAll('[data-tag-filter]').forEach((n) => {
      n.addEventListener('change', () => { state.tagFilter = n.value; state.page = 1; render(); });
    });
    el.querySelectorAll('[data-page]').forEach((n) => {
      n.addEventListener('click', () => { state.page = Number(n.getAttribute('data-page')); render(); });
    });
    el.querySelectorAll('[data-result-q]').forEach((n) => {
      n.addEventListener('input', () => { state.resultQuery = n.value; state.page = 1; render(); });
    });
    el.querySelectorAll('[data-rf]').forEach((n) => {
      n.addEventListener('change', () => { state.resultFilters[n.getAttribute('data-rf')] = n.value; state.page = 1; render(); });
    });
    el.querySelectorAll('[data-view-mode]').forEach((n) => {
      n.addEventListener('click', () => {
        state.resultsViewMode = n.getAttribute('data-view-mode');
        localStorage.setItem('er_results_view', state.resultsViewMode);
        render();
      });
    });
    el.querySelectorAll('[data-admin-section]').forEach((n) => {
      n.addEventListener('click', () => { state.adminSection = n.getAttribute('data-admin-section'); render(); });
    });
    el.querySelectorAll('[data-path]').forEach((n) => {
      n.addEventListener('change', () => {
        const path = n.getAttribute('data-path');
        const value = n.type === 'checkbox' ? n.checked : (path.endsWith('sort_order') || path.endsWith('marks') || path.endsWith('max_marks') ? Number(n.value || 0) : n.value);
        setPath(state.adminCatalog, path, value);
      });
    });
    el.querySelectorAll('[data-save-admin]').forEach((n) => {
      n.addEventListener('click', saveAdmin);
    });
    el.querySelectorAll('[data-publish]').forEach((n) => {
      n.addEventListener('click', async () => {
        try {
          const data = await fetchJson(cfg.publishUrl, { method: 'POST' });
          toast(data.message || 'Published to public site directory.');
        } catch (err) {
          toast(err.message);
        }
      });
    });
    el.querySelectorAll('[data-add]').forEach((n) => {
      n.addEventListener('click', () => {
        const kind = n.getAttribute('data-add');
        const cat = state.adminCatalog;
        if (kind === 'group') {
          cat.groups.push({ id: uid('grp'), name: 'New Group', description: '', sort_order: cat.groups.length, published: true, classes: [] });
        }
        if (kind === 'class') {
          cat.groups[n.dataset.gi].classes.push({ id: uid('cls'), name: 'New Class', sort_order: 0, published: true, subjects: [] });
        }
        if (kind === 'subject') {
          cat.groups[n.dataset.gi].classes[n.dataset.ci].subjects.push({ id: uid('sub'), name: 'New Subject', sort_order: 0, published: true, papers: [] });
        }
        if (kind === 'session') {
          cat.sessions.push({ id: uid('ses'), name: '2026-27', sort_order: 0, published: true });
        }
        if (kind === 'exam') {
          cat.examinations.push({ id: uid('exam'), name: 'New Examination', session_id: (cat.sessions[0] || {}).id || '', sort_order: 0, published: true });
        }
        if (kind === 'result') {
          cat.results.push({ id: uid('res'), student_name: '', roll_number: '', registration_number: '', group_id: '', class_id: '', subject_id: '', examination_id: '', session_id: '', marks: '', max_marks: '', grade: '', published: true });
        }
        render();
      });
    });
    el.querySelectorAll('[data-move]').forEach((n) => {
      n.addEventListener('click', () => {
        const i = Number(n.dataset.gi);
        const dir = Number(n.dataset.dir);
        const arr = state.adminCatalog.groups;
        const j = i + dir;
        if (j < 0 || j >= arr.length) return;
        [arr[i], arr[j]] = [arr[j], arr[i]];
        arr.forEach((g, idx) => { g.sort_order = idx; });
        render();
      });
    });
    el.querySelectorAll('[data-del]').forEach((n) => {
      n.addEventListener('click', () => {
        state.confirm = {
          kind: n.getAttribute('data-del'),
          gi: n.dataset.gi, ci: n.dataset.ci, si: n.dataset.si,
          pi: n.dataset.pi, ri: n.dataset.ri, ei: n.dataset.ei,
        };
        render();
      });
    });
    el.querySelectorAll('[data-new-paper]').forEach((n) => {
      n.addEventListener('change', async () => {
        const [gi, ci, si] = n.getAttribute('data-new-paper').split(':').map(Number);
        if (n.files[0]) await uploadToSubject(gi, ci, si, n.files[0]);
      });
    });
    el.querySelectorAll('[data-upload]').forEach((n) => {
      n.addEventListener('change', async () => {
        const [gi, ci, si, pi] = n.getAttribute('data-upload').split(':').map(Number);
        if (n.files[0]) await uploadToSubject(gi, ci, si, n.files[0], pi);
      });
    });
    el.querySelectorAll('[data-import-csv]').forEach((n) => {
      n.addEventListener('change', async () => {
        if (!n.files[0]) return;
        state.csvFile = n.files[0];
        const body = new FormData();
        body.append('file', state.csvFile);
        try {
          const data = await fetchJson(cfg.previewResultsUrl || cfg.importResultsUrl, { method: 'POST', body });
          state.csvPreviewRows = data;
          state.formError = '';
          render();
        } catch (err) {
          state.formError = err.message;
          render();
        }
      });
    });
    el.querySelectorAll('[data-confirm-csv]').forEach((n) => {
      n.addEventListener('click', async () => {
        if (!state.csvFile) return;
        const body = new FormData();
        body.append('file', state.csvFile);
        try {
          const data = await fetchJson(cfg.importResultsUrl, {
            method: 'POST',
            headers: state.adminCatalog && state.adminCatalog.revision != null ? { 'If-Match': String(state.adminCatalog.revision) } : {},
            body,
          });
          state.adminCatalog = data.data;
          state.csvPreviewRows = null;
          state.csvFile = null;
          toast(`Imported ${data.imported} result records${data.skipped ? `; skipped ${data.skipped} duplicates` : ''}.`);
          render();
        } catch (err) {
          state.formError = err.message;
          render();
        }
      });
    });
    el.querySelectorAll('[data-import-catalog]').forEach((n) => {
      n.addEventListener('change', async () => {
        if (!n.files[0]) return;
        const text = await n.files[0].text();
        try {
          const data = await fetchJson(cfg.importCatalogUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(state.adminCatalog && state.adminCatalog.revision != null ? { 'If-Match': String(state.adminCatalog.revision) } : {}),
            },
            body: text,
          });
          state.adminCatalog = data.data;
          toast('Database catalog restored successfully!');
          render();
        } catch (err) {
          toast(err.message);
        }
      });
    });
    el.querySelectorAll('[data-close-modal]').forEach((n) => {
      n.addEventListener('click', (e) => {
        if (e.target === n) go(n.getAttribute('data-close-modal'));
      });
    });

    const yesBtn = el.querySelector('[data-confirm-yes]');
    if (yesBtn) {
      yesBtn.addEventListener('click', () => {
        const c = state.confirm;
        const cat = state.adminCatalog;
        if (c.kind === 'group') cat.groups.splice(Number(c.gi), 1);
        if (c.kind === 'class') cat.groups[c.gi].classes.splice(Number(c.ci), 1);
        if (c.kind === 'subject') cat.groups[c.gi].classes[c.ci].subjects.splice(Number(c.si), 1);
        if (c.kind === 'paper') cat.groups[c.gi].classes[c.ci].subjects[c.si].papers.splice(Number(c.pi), 1);
        if (c.kind === 'result') cat.results.splice(Number(c.ri), 1);
        if (c.kind === 'session') cat.sessions.splice(Number(c.si), 1);
        if (c.kind === 'exam') cat.examinations.splice(Number(c.ei), 1);
        state.confirm = null;
        render();
      });
      el.querySelector('[data-confirm-no]').addEventListener('click', () => {
        state.confirm = null;
        render();
      });
    }
  }

  function render() {
    const active = document.activeElement;
    const focusState = active && root.contains(active) && active.dataset && (active.dataset.q != null || active.dataset.resultQ != null)
      ? {
          selector: active.dataset.q != null ? '[data-q]' : '[data-result-q]',
          start: typeof active.selectionStart === 'number' ? active.selectionStart : null,
          end: typeof active.selectionEnd === 'number' ? active.selectionEnd : null,
        }
      : null;
    let body = '';
    if (state.loading) {
      body = '<div class="er-skel" aria-busy="true"></div><div class="er-skel"></div><div class="er-skel"></div>';
    } else if (state.error) {
      body = `
        <div class="er-error">
          <i class="fas fa-triangle-exclamation"></i> ${esc(state.error)}
        </div>
        <div class="er-actions" style="margin-top:16px;">
          <button class="er-btn" type="button" data-retry><i class="fas fa-rotate-right"></i> Retry</button>
        </div>`;
    } else if (state.route.view === 'results') {
      body = resultsView();
    } else if (state.route.view === 'papers') {
      body = papersView();
    } else if (state.route.view === 'admin') {
      body = adminView();
    } else {
      body = landing();
    }

    root.innerHTML = `
      <div class="er-wrap">
        ${body}
        ${state.toast ? `<div class="er-toast" role="status"><i class="fas fa-circle-check" style="color:#22c55e;"></i> ${esc(state.toast)}</div>` : ''}
        ${state.confirm ? `
          <div class="er-modal-backdrop" role="dialog" aria-modal="true">
            <div class="er-form-card" style="max-width:440px;width:100%;margin:0;">
              <h3 style="margin-top:0;color:#dc2626;"><i class="fas fa-triangle-exclamation"></i> Confirm Deletion</h3>
              <p>Are you sure you want to delete this item? This action cannot be undone once saved.</p>
              <div class="er-actions" style="justify-content:flex-end;">
                <button class="er-btn ghost" data-confirm-no>Cancel</button>
                <button class="er-btn danger" data-confirm-yes>Yes, Delete</button>
              </div>
            </div>
          </div>` : ''}
      </div>`;

    bind(root);

    if (focusState) {
      const next = root.querySelector(focusState.selector);
      if (next) {
        next.focus();
        if (focusState.start != null && typeof next.setSelectionRange === 'function') {
          next.setSelectionRange(focusState.start, focusState.end);
        }
      }
    }

    const retry = root.querySelector('[data-retry]');
    if (retry) retry.addEventListener('click', loadAll);
  }

  async function loadPublic() {
    if (cfg.mode === 'public') {
      const resp = await fetch(cfg.catalogUrl, { cache: 'no-store' });
      if (!resp.ok) throw new Error('Catalog is not available yet. Publish Excel Results from the LAN app.');
      state.catalog = await resp.json();
      return;
    }
    const data = await fetchJson(cfg.catalogUrl);
    state.catalog = data.data;
    state.canAdmin = !!data.can_admin;
  }

  async function loadAll() {
    state.loading = true;
    state.error = null;
    render();
    try {
      if (cfg.mode === 'lan' && cfg.meUrl) {
        const me = await fetchJson(cfg.meUrl);
        state.role = me.role;
        state.canAdmin = !!me.can_admin;
        state.csrfToken = me.csrf_token || '';
      }
      await loadPublic();
      if (state.canAdmin && cfg.adminCatalogUrl) {
        const admin = await fetchJson(cfg.adminCatalogUrl);
        state.adminCatalog = admin.data;
      }
    } catch (err) {
      state.error = err.message;
    } finally {
      state.loading = false;
      render();
    }
  }

  if (cfg.mode === 'lan' && localStorage.getItem('ea_theme') === 'dark') {
    document.body.classList.add('dark');
  }

  loadAll();
})();
