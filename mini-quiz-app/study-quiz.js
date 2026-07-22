/* ============================================================
   QuizSpark — Study Quiz Module (study-quiz.js)
   Reads PDFs from local directory → Gemini API generates
   CBSE/ICSE-style MCQs intelligently.
   ============================================================ */
console.log('[StudyQuiz] Script loaded. $:', typeof $, '$$:', typeof $$);

// ── LLM API Config ──
// Multiple free-tier providers for reliability and variety
const LLM_PROVIDERS = {
  gemini: {
    name: 'Google Gemini 2.0 Flash',
    model: 'gemini-2.0-flash',
    base: 'https://generativelanguage.googleapis.com/v1beta/models',
    keyStorage: 'quizspark_gemini_key',
    freeInfo: '15 RPM, 1M tokens/min — aistudio.google.com/apikey',
  },
  groq: {
    name: 'Groq Llama 3.3 70B',
    model: 'llama-3.3-70b-versatile',
    base: 'https://api.groq.com/openai/v1/chat/completions',
    keyStorage: 'quizspark_groq_key',
    freeInfo: '30 RPM, 14k tokens/min — console.groq.com',
  },
  cohere: {
    name: 'Cohere Command R',
    model: 'command-r',
    base: 'https://api.cohere.ai/v1/chat',
    keyStorage: 'quizspark_cohere_key',
    freeInfo: '20 RPM, 100k tokens/min — dashboard.cohere.com',
  },
};

let _activeLLM = localStorage.getItem('quizspark_active_llm') || 'gemini';

function getLLMKey(provider) {
  const p = LLM_PROVIDERS[provider || _activeLLM];
  return localStorage.getItem(p.keyStorage) || '';
}
function setLLMKey(provider, key) {
  const p = LLM_PROVIDERS[provider];
  localStorage.setItem(p.keyStorage, key);
}
function getActiveLLM() { return _activeLLM; }
function setActiveLLM(p) {
  if (LLM_PROVIDERS[p]) { _activeLLM = p; localStorage.setItem('quizspark_active_llm', p); }
}

// Backward compat
function getGeminiKey() { return getLLMKey('gemini'); }
function setGeminiKey(k) { setLLMKey('gemini', k); }

// ── IndexedDB Cache (parsed PDF text) ──
const IDB_NAME = 'quizspark_pdfs';
const IDB_VER  = 1;
const IDB_STORE = 'pages';

function openIDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_NAME, IDB_VER);
    req.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(IDB_STORE)) {
        db.createObjectStore(IDB_STORE, { keyPath: 'id' });
      }
    };
    req.onsuccess = e => resolve(e.target.result);
    req.onerror = e => reject(e.target.error);
  });
}

async function cachePDFText(fileId, fileName, lastModified, textChunks) {
  const db = await openIDB();
  const tx = db.transaction(IDB_STORE, 'readwrite');
  tx.objectStore(IDB_STORE).put({
    id: fileId,
    fileName,
    lastModified,
    textChunks,       // array of strings (one per page or section)
    parsedAt: Date.now(),
  });
  return new Promise((res, rej) => { tx.oncomplete = res; tx.onerror = rej; });
}

async function getCachedPDF(fileId, lastModified) {
  const db = await openIDB();
  const tx = db.transaction(IDB_STORE, 'readonly');
  const req = tx.objectStore(IDB_STORE).get(fileId);
  return new Promise((res, rej) => {
    req.onsuccess = () => {
      const r = req.result;
      if (r && r.lastModified === lastModified) res(r);
      else res(null);
    };
    req.onerror = () => res(null);
  });
}

async function getAllCachedPDFs() {
  const db = await openIDB();
  const tx = db.transaction(IDB_STORE, 'readonly');
  const req = tx.objectStore(IDB_STORE).getAll();
  return new Promise((res, rej) => {
    req.onsuccess = () => res(req.result || []);
    req.onerror = () => res([]);
  });
}

async function deleteCachedPDF(fileId) {
  const db = await openIDB();
  const tx = db.transaction(IDB_STORE, 'readwrite');
  tx.objectStore(IDB_STORE).delete(fileId);
  return new Promise((res, rej) => { tx.oncomplete = res; tx.onerror = rej; });
}

// ── PDF.js Text Extraction ──
async function extractTextFromPDF(file) {
  // file is a File object from <input> or File System Access API
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  const textChunks = [];
  const totalPages = pdf.numPages;

  for (let i = 1; i <= totalPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const strings = content.items.map(item => item.str);
    // Join with spaces, but insert newline where y-position drops significantly
    let pageText = '';
    let lastY = null;
    for (const item of content.items) {
      if (lastY !== null && Math.abs(item.transform[5] - lastY) > 5) {
        pageText += '\n';
      }
      pageText += item.str + ' ';
      lastY = item.transform[5];
    }
    textChunks.push(pageText.trim());
  }
  return textChunks;
}

// ── File System Access API (directory picker) ──
let _dirHandle = null;

async function pickStudyDirectory() {
  if (!('showDirectoryPicker' in window)) {
    alert('Your browser does not support directory access. Please use Chrome or Edge, or use the file picker instead.');
    return null;
  }
  try {
    _dirHandle = await window.showDirectoryPicker({ mode: 'read' });
    return _dirHandle;
  } catch {
    return null; // user cancelled
  }
}

async function scanDirectoryForPDFs(dirHandle) {
  const files = [];
  for await (const entry of dirHandle.values()) {
    if (entry.kind === 'file' && entry.name.toLowerCase().endsWith('.pdf')) {
      files.push(entry);
    }
  }
  return files;
}

async function readFileHandle(fileHandle) {
  return await fileHandle.getFile();
}

// ── Parse all PDFs (with caching) ──
async function parseAllPDFs(fileEntries, onProgress) {
  const allText = [];
  let processed = 0;

  for (const entry of fileEntries) {
    const file = await readFileHandle(entry);
    const fileId = file.name + '_' + file.size;
    const lastMod = file.lastModified;

    // Check cache
    const cached = await getCachedPDF(fileId, lastMod);
    if (cached) {
      allText.push(...cached.textChunks);
      processed++;
      if (onProgress) onProgress(processed, fileEntries.length, file.name, true);
      continue;
    }

    // Extract text
    try {
      const chunks = await extractTextFromPDF(file);
      await cachePDFText(fileId, file.name, lastMod, chunks);
      allText.push(...chunks);
    } catch (e) {
      console.warn('Failed to parse PDF:', file.name, e);
    }
    processed++;
    if (onProgress) onProgress(processed, fileEntries.length, file.name, false);
  }

  return allText;
}

// Parse from FileList (fallback for browsers without directory picker)
async function parseFileListPDFs(fileList, onProgress) {
  const allText = [];
  let processed = 0;

  for (const file of fileList) {
    if (!file.name.toLowerCase().endsWith('.pdf')) continue;
    const fileId = file.name + '_' + file.size;
    const lastMod = file.lastModified;

    const cached = await getCachedPDF(fileId, lastMod);
    if (cached) {
      allText.push(...cached.textChunks);
      processed++;
      if (onProgress) onProgress(processed, fileList.length, file.name, true);
      continue;
    }

    try {
      const chunks = await extractTextFromPDF(file);
      await cachePDFText(fileId, file.name, lastMod, chunks);
      allText.push(...chunks);
    } catch (e) {
      console.warn('Failed to parse PDF:', file.name, e);
    }
    processed++;
    if (onProgress) onProgress(processed, fileList.length, file.name, false);
  }

  return allText;
}

// ── LLM API — Generate CBSE/ICSE MCQs (multi-provider) ──
async function generateMCQsFromText(textContent, numQuestions, difficulty, className, subject, language) {
  // Build prompt (shared across providers) — keep modest to avoid token-heavy requests
  const MAX_CHARS = 40000;
  let text = textContent.join('\n\n---\n\n');
  if (text.length > MAX_CHARS) {
    const chunkSize = Math.floor(MAX_CHARS / 4);
    const total = text.length;
    text = [
      text.substring(0, chunkSize),
      text.substring(Math.floor(total * 0.25), Math.floor(total * 0.25) + chunkSize),
      text.substring(Math.floor(total * 0.5), Math.floor(total * 0.5) + chunkSize),
      text.substring(Math.floor(total * 0.75), Math.floor(total * 0.75) + chunkSize),
    ].join('\n\n---\n\n');
  }

  const diffInstruction = difficulty === 'mixed'
    ? 'Mix of easy (recall), medium (application), and hard (analysis/evaluation) questions roughly in 3:4:3 ratio.'
    : difficulty === 'easy' ? 'Focus on recall and basic understanding (Bloom\'s Level 1-2).'
    : difficulty === 'medium' ? 'Focus on application and analysis (Bloom\'s Level 3-4).'
    : 'Focus on higher-order thinking: analysis, evaluation, synthesis (Bloom\'s Level 4-6).';

  const langInstruction = language === 'hi'
    ? 'Generate ALL questions, options, and explanations in Hindi (Devanagari script). Use Hindi medium terminology as per NCERT/CBSE Hindi medium textbooks.'
    : 'Generate all content in English.';

  const prompt = `You are an expert CBSE/ICSE exam paper setter for Class ${className || '10'} ${subject || 'Science'}.

Given the following study material text extracted from PDFs, generate exactly ${numQuestions} multiple-choice questions (MCQs) that test a student's UNDERSTANDING of the concepts, not just rote memorization.

INSTRUCTIONS:
1. ${diffInstruction}
2. Each question must have exactly 4 options (A, B, C, D) with exactly ONE correct answer.
3. Questions should follow CBSE/ICSE examination style and tone.
4. Include different question TYPES:
   - Conceptual understanding ("Which of the following is TRUE about...")
   - Cause-effect ("What happens when...")
   - Application-based ("A student observes... What conclusion can be drawn?")
   - Assertion-Reason format ("Assertion: ... Reason: ...")
   - Fill-in-the-blank style MCQ
   - "Which is INCORRECT" type
   - Diagram/figure-based reasoning (if applicable from text)
5. Distractors (wrong options) must be PLAUSIBLE — common misconceptions, partially correct statements, near-miss values.
6. Do NOT repeat the same concept in multiple questions.
7. ${langInstruction}
8. For ANY mathematical expression, equation, formula, or symbol, use LaTeX notation wrapped in $ delimiters (e.g. $x^2$, $\\frac{3}{4}$, $\\sqrt{2}$, $\\int_0^1 x\\,dx$). Use $$...$$ for display-style equations. This is critical for proper rendering.
9. Return ONLY valid JSON — no markdown, no explanation outside JSON.

Return format (strict JSON array):
[
  {
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": 0,
    "difficulty": "easy|medium|hard",
    "explanation": "Brief explanation of why the correct answer is right",
    "category": "Topic/subtopic this question covers"
  }
]

STUDY MATERIAL:
${text}`;

  // Try active provider first, then fallback to others with keys
  const providers = [_activeLLM, ...Object.keys(LLM_PROVIDERS).filter(k => k !== _activeLLM)];
  const errors = [];

  for (const provKey of providers) {
    const prov = LLM_PROVIDERS[provKey];
    const key = getLLMKey(provKey);
    if (!key) { errors.push(`${prov.name}: No API key`); continue; }

    try {
      let questions;
      if (provKey === 'gemini') questions = await callGemini(key, prov, prompt);
      else if (provKey === 'groq') questions = await callGroq(key, prov, prompt);
      else if (provKey === 'cohere') questions = await callCohere(key, prov, prompt);

      if (questions && questions.length > 0) {
        return questions.map(q => ({
          question: q.question,
          correct_answer: q.options[q.correct] || q.options[0],
          incorrect_answers: q.options.filter((_, i) => i !== q.correct),
          category: q.category || subject || 'General',
          difficulty: q.difficulty || difficulty,
          explanation: q.explanation || '',
          source: `pdf_${provKey}`,
        }));
      }
    } catch (e) {
      errors.push(`${prov.name}: ${e.message}`);
      console.warn(`LLM ${prov.name} failed, trying next…`, e.message);
    }
  }

  throw new Error('All LLM providers failed:\n' + errors.join('\n'));
}

// ── Gemini API call (with auto-fallback across model names) ──
async function callGemini(key, prov, prompt) {
  // Try multiple model names — Google sometimes renames; this maximizes compatibility
  const models = [prov.model, 'gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-1.5-flash-latest'];
  const tried = new Set();
  let lastErr = null;

  for (const model of models) {
    if (tried.has(model)) continue;
    tried.add(model);

    const url = `${prov.base}/${model}:generateContent?key=${key}`;
    let res;
    try {
      res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.7, maxOutputTokens: 8192, responseMimeType: 'application/json' },
        }),
      });
    } catch (netErr) {
      lastErr = new Error(`Network error: ${netErr.message}`);
      continue;
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err?.error?.message || `HTTP ${res.status}`;
      console.warn(`[Gemini] model "${model}" failed: ${msg}`);
      if (res.status === 429) { lastErr = new Error('Rate limit (15/min). Wait 1 min.'); break; }
      if (res.status === 400 && /API key/i.test(msg)) { lastErr = new Error('Invalid API key.'); break; }
      if (res.status === 403) { lastErr = new Error('API key invalid or has no access. Get a new one at aistudio.google.com/apikey'); break; }
      if (res.status === 404 || /not found|not supported/i.test(msg)) {
        lastErr = new Error(`Model ${model} unavailable: ${msg}`);
        continue; // try next model
      }
      lastErr = new Error(msg);
      continue;
    }

    const data = await res.json();
    const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
    if (!text) {
      const finishReason = data?.candidates?.[0]?.finishReason;
      lastErr = new Error(`Empty response (finishReason: ${finishReason || 'unknown'})`);
      continue;
    }
    console.log(`[Gemini] ✓ Used model: ${model}`);
    return parseJSON(text);
  }

  throw lastErr || new Error('All Gemini models failed');
}

// ── Groq API call (OpenAI-compatible) ──
async function callGroq(key, prov, prompt) {
  const res = await fetch(prov.base, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
    body: JSON.stringify({
      model: prov.model,
      messages: [
        { role: 'system', content: 'You are a CBSE/ICSE exam paper setter. Return only valid JSON arrays as instructed.' },
        { role: 'user', content: prompt },
      ],
      temperature: 0.7,
      max_tokens: 8192,
      response_format: { type: 'json_object' },
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 429) throw new Error('Rate limit (30/min). Wait 1 min.');
    if (res.status === 401) throw new Error('Invalid API key.');
    throw new Error(err?.error?.message || `HTTP ${res.status}`);
  }
  const data = await res.json();
  const text = data?.choices?.[0]?.message?.content;
  if (!text) throw new Error('Empty response');
  return parseJSON(text);
}

// ── Cohere API call ──
async function callCohere(key, prov, prompt) {
  const res = await fetch(prov.base, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
    body: JSON.stringify({
      model: prov.model,
      message: prompt,
      temperature: 0.7,
      max_tokens: 4096,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 429) throw new Error('Rate limit (20/min). Wait 1 min.');
    if (res.status === 401) throw new Error('Invalid API key.');
    throw new Error(err?.message || `HTTP ${res.status}`);
  }
  const data = await res.json();
  const text = data?.text;
  if (!text) throw new Error('Empty response');
  return parseJSON(text);
}

// ── Parse JSON from LLM response (handles markdown wrapping) ──
function parseJSON(text) {
  let cleaned = text.replace(/^```json?\s*/i, '').replace(/\s*```$/i, '').trim();
  // Cohere sometimes wraps in {questions: [...]}
  try {
    const parsed = JSON.parse(cleaned);
    if (Array.isArray(parsed)) return parsed;
    // If it's an object with a questions array
    if (parsed.questions && Array.isArray(parsed.questions)) return parsed.questions;
    // If it's a single object wrapping an array
    const vals = Object.values(parsed);
    const arr = vals.find(v => Array.isArray(v));
    if (arr) return arr;
    throw new Error('Not an array');
  } catch {
    // Try extracting JSON array from text
    const match = cleaned.match(/\[[\s\S]*\]/);
    if (match) {
      try { return JSON.parse(match[0]); } catch { /* */ }
    }
    throw new Error('Invalid JSON from LLM');
  }
}

// ── Study Quiz State ──
const studyState = {
  mode: 'web',          // 'web' | 'study'
  dirHandle: null,
  pdfFiles: [],
  parsedText: [],
  className: '10',
  subject: 'Science',
  board: 'CBSE',
};

// ── Subject lists per board ──
const SUBJECTS_CBSE = {
  4: ['EVS', 'Mathematics', 'English', 'Hindi'],
  5: ['EVS', 'Mathematics', 'English', 'Hindi'],
  6: ['Science', 'Mathematics', 'Social Science', 'English', 'Hindi', 'Sanskrit'],
  7: ['Science', 'Mathematics', 'Social Science', 'English', 'Hindi', 'Sanskrit'],
  8: ['Science', 'Mathematics', 'Social Science', 'English', 'Hindi', 'Sanskrit'],
  9: ['Science', 'Mathematics', 'Social Science', 'English', 'Hindi', 'Sanskrit', 'IT'],
  10: ['Science', 'Mathematics', 'Social Science', 'English', 'Hindi', 'Sanskrit', 'IT'],
  11: ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'English', 'Hindi', 'Economics', 'Accountancy', 'Business Studies', 'History', 'Political Science', 'Geography', 'Psychology', 'Sociology', 'Computer Science', 'Physical Education'],
  12: ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'English', 'Hindi', 'Economics', 'Accountancy', 'Business Studies', 'History', 'Political Science', 'Geography', 'Psychology', 'Sociology', 'Computer Science', 'Physical Education'],
};

const SUBJECTS_ICSE = {
  4: ['EVS', 'Mathematics', 'English', 'Hindi', 'General Science'],
  5: ['EVS', 'Mathematics', 'English', 'Hindi', 'General Science'],
  6: ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'History & Civics', 'Geography', 'English', 'Hindi'],
  7: ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'History & Civics', 'Geography', 'English', 'Hindi'],
  8: ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'History & Civics', 'Geography', 'English', 'Hindi'],
  9: ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'History & Civics', 'Geography', 'English', 'Hindi', 'Computer Applications'],
  10: ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'History & Civics', 'Geography', 'English', 'Hindi', 'Computer Applications'],
  11: ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'English', 'Hindi', 'Economics', 'Commerce', 'Accounts', 'History', 'Political Science', 'Geography', 'Sociology', 'Psychology', 'Computer Science'],
  12: ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'English', 'Hindi', 'Economics', 'Commerce', 'Accounts', 'History', 'Political Science', 'Geography', 'Sociology', 'Psychology', 'Computer Science'],
};

function getSubjectsForClass(cls, board) {
  const map = board === 'ICSE' ? SUBJECTS_ICSE : SUBJECTS_CBSE;
  return map[cls] || SUBJECTS_CBSE[10];
}

// ══════════════════════════════════════════════════════════
// ── UI EVENT HANDLERS ──
// ══════════════════════════════════════════════════════════

// $ and $$ already defined in app.js

// ── PDF.js worker config ──
if (typeof pdfjsLib !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

// ── DOM refs (use # prefix since $ = querySelector) ──
// Avoid re-declaring vars from app.js (quizForm, loadingMsg, loadingOverlay)
const studyQuizForm  = $('#studyQuizForm');
const modeTabs       = $$('.mode-tab');
const classSelect    = $('#classSelect');
const subjectSelect  = $('#subjectSelect');
const openDirBtn     = $('#openDirBtn');
const pickFilesBtn   = $('#pickFilesBtn');
const pdfFileInput   = $('#pdfFileInput');
const pdfFileList    = $('#pdfFileList');
const pdfFileCount   = $('#pdfFileCount');
const pdfFileNameList = $('#pdfFileNameList');
const clearPdfsBtn   = $('#clearPdfsBtn');
const studyNumQ      = $('#studyNumQuestions');
const studyNumDisp   = $('#studyNumDisplay');
const studyStartBtn  = $('#studyStartBtn');
const geminiModal    = $('#geminiModal');
const geminiKeyInput = $('#geminiKeyInput');
const geminiSaveBtn  = $('#geminiSaveBtn');
const geminiCancelBtn = $('#geminiCancelBtn');

// Safety: if critical elements missing, log and skip
if (!studyQuizForm) console.error('Study Quiz: #studyQuizForm not found in DOM');
if (!classSelect) console.error('Study Quiz: #classSelect not found in DOM');
if (!studyStartBtn) console.error('Study Quiz: #studyStartBtn not found in DOM');
console.log('[StudyQuiz] DOM refs loaded — form:', !!studyQuizForm, 'btn:', !!studyStartBtn, 'classSelect:', !!classSelect);

// ── Mode Tab Switching ──
modeTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    modeTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const mode = tab.dataset.mode;
    studyState.mode = mode;
    if (mode === 'web') {
      if (quizForm) quizForm.classList.remove('hidden');
      if (studyQuizForm) studyQuizForm.classList.add('hidden');
    } else {
      if (quizForm) quizForm.classList.add('hidden');
      if (studyQuizForm) studyQuizForm.classList.remove('hidden');
      populateSubjects();
    }
  });
});

// ── Board chips ──
$$('.board-chips .chip').forEach(chip => {
  chip.addEventListener('click', () => {
    $$('.board-chips .chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    studyState.board = chip.dataset.value;
    populateSubjects();
  });
});

// ── Class selector ──
if (classSelect) classSelect.addEventListener('change', () => {
  studyState.className = classSelect.value;
  populateSubjects();
});

function populateSubjects() {
  const cls = parseInt(classSelect.value);
  const board = studyState.board;
  const subjects = getSubjectsForClass(cls, board);
  subjectSelect.innerHTML = '';
  subjects.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s;
    opt.textContent = s;
    subjectSelect.appendChild(opt);
  });
  studyState.subject = subjects[0] || 'Science';
}

if (subjectSelect) subjectSelect.addEventListener('change', () => {
  studyState.subject = subjectSelect.value;
});

// ── Study difficulty chips ──
$$('.study-difficulty-chips .chip').forEach(chip => {
  chip.addEventListener('click', () => {
    $$('.study-difficulty-chips .chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
  });
});

// ── Study language chips ──
$$('.study-lang-chips .chip').forEach(chip => {
  chip.addEventListener('click', () => {
    $$('.study-lang-chips .chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
  });
});

// ── Number slider ──
if (studyNumQ) studyNumQ.addEventListener('input', () => {
  studyNumDisp.textContent = studyNumQ.value;
});

// ── Open Directory (File System Access API) ──
let _selectedFileHandles = [];
let _selectedFileList = null;

if (openDirBtn) openDirBtn.addEventListener('click', async () => {
  const dirHandle = await pickStudyDirectory();
  if (!dirHandle) return;
  studyState.dirHandle = dirHandle;
  _selectedFileHandles = await scanDirectoryForPDFs(dirHandle);

  if (_selectedFileHandles.length === 0) {
    alert('No PDF files found in this folder.');
    return;
  }
  showPDFList(_selectedFileHandles.map(h => h.name));
});

// ── Pick Files (fallback) ──
if (pickFilesBtn) pickFilesBtn.addEventListener('click', () => {
  pdfFileInput.click();
});

if (pdfFileInput) pdfFileInput.addEventListener('change', () => {
  _selectedFileList = pdfFileInput.files;
  const names = [];
  for (const f of _selectedFileList) {
    if (f.name.toLowerCase().endsWith('.pdf')) names.push(f.name);
  }
  if (names.length === 0) {
    alert('No PDF files selected.');
    return;
  }
  showPDFList(names);
});

function showPDFList(names) {
  pdfFileCount.textContent = `${names.length} PDF${names.length !== 1 ? 's' : ''} selected`;
  pdfFileNameList.innerHTML = '';
  names.forEach(n => {
    const li = document.createElement('li');
    li.textContent = n;
    pdfFileNameList.appendChild(li);
  });
  pdfFileList.classList.remove('hidden');
}

if (clearPdfsBtn) clearPdfsBtn.addEventListener('click', () => {
  _selectedFileHandles = [];
  _selectedFileList = null;
  studyState.dirHandle = null;
  pdfFileList.classList.add('hidden');
  pdfFileInput.value = '';
});

// ── Gemini Settings Modal ──
const groqKeyInput  = $('#groqKeyInput');
const cohereKeyInput = $('#cohereKeyInput');

function openGeminiSettings() {
  geminiKeyInput.value = getLLMKey('gemini');
  groqKeyInput.value = getLLMKey('groq');
  cohereKeyInput.value = getLLMKey('cohere');
  // Highlight active provider chip
  $$('.llm-provider-chips .chip').forEach(c => {
    c.classList.toggle('active', c.dataset.llm === _activeLLM);
  });
  geminiModal.classList.remove('hidden');
}
function closeGeminiSettings() {
  geminiModal.classList.add('hidden');
}

// Provider chip selection in settings
$$('.llm-provider-chips .chip').forEach(chip => {
  chip.addEventListener('click', () => {
    $$('.llm-provider-chips .chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
  });
});

const gemBtn1 = $('#geminiSettingsBtn');
const gemBtn2 = $('#geminiSettingsBtn2');
if (gemBtn1) gemBtn1.addEventListener('click', openGeminiSettings);
if (gemBtn2) gemBtn2.addEventListener('click', openGeminiSettings);
if (geminiCancelBtn) geminiCancelBtn.addEventListener('click', closeGeminiSettings);
if (geminiSaveBtn) geminiSaveBtn.addEventListener('click', () => {
  // Save all keys
  const gemKey = geminiKeyInput.value.trim();
  const groqKey = groqKeyInput.value.trim();
  const cohereKey = cohereKeyInput.value.trim();

  if (gemKey) setLLMKey('gemini', gemKey);
  if (groqKey) setLLMKey('groq', groqKey);
  if (cohereKey) setLLMKey('cohere', cohereKey);

  // Save active provider
  const activeChip = document.querySelector('.llm-provider-chips .chip.active');
  if (activeChip) setActiveLLM(activeChip.dataset.llm);

  // Validate at least one key exists
  if (!getLLMKey('gemini') && !getLLMKey('groq') && !getLLMKey('cohere')) {
    alert('Please enter at least one API key.');
    return;
  }

  closeGeminiSettings();
  geminiSaveBtn.textContent = '✅ Saved!';
  setTimeout(() => { geminiSaveBtn.textContent = '💾 Save All'; }, 1500);
});

// ── History button (study mode) ──
const historyBtn2 = $('#historyBtn2');
if (historyBtn2) historyBtn2.addEventListener('click', () => {
  // Reuse existing history screen
  if (typeof renderHistory === 'function') renderHistory();
  if (typeof showScreen === 'function') showScreen($('#historyScreen'));
});

// ── Study Quiz Generate Button (click, NOT form submit) ──
if (studyStartBtn) studyStartBtn.addEventListener('click', async () => {
  console.log('[StudyQuiz] Generate button clicked!');

  // Validate: need PDFs
  const hasDir = _selectedFileHandles.length > 0;
  const hasFiles = _selectedFileList && _selectedFileList.length > 0;
  if (!hasDir && !hasFiles) {
    alert('Please select PDF files or open a folder first.');
    return;
  }

  // Validate: need at least one LLM key
  if (!getLLMKey('gemini') && !getLLMKey('groq') && !getLLMKey('cohere')) {
    openGeminiSettings();
    return;
  }

  // Read study form values
  const numQ = parseInt(studyNumQ.value);
  const diffChip = document.querySelector('.study-difficulty-chips .chip.active');
  const difficulty = diffChip ? diffChip.dataset.value : 'medium';
  const langChip = document.querySelector('.study-lang-chips .chip.active');
  const language = langChip ? langChip.dataset.value : 'en';
  const className = classSelect.value;
  const subject = subjectSelect.value;

  // Update shared state so quiz/results screens work
  state.difficulty = difficulty;
  state.language = language;
  state.numQuestions = numQ;
  state.categoryName = subject;
  state.customTopic = `${subject} (Class ${className})`;

  // ── Immediate visual feedback on button ──
  const btn = studyStartBtn;
  const origHTML = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<span class="btn-text">⏳ Preparing quiz…</span>';

  // Show loading overlay directly (don't rely on app.js function)
  const overlay = document.getElementById('loadingOverlay');
  const msgEl = document.getElementById('loadingMsg');
  if (overlay) overlay.classList.remove('hidden');
  if (msgEl) msgEl.textContent = 'Parsing PDF files…';

  try {
    // Step 1: Parse PDFs
    let parsedText;
    if (hasDir) {
      parsedText = await parseAllPDFs(_selectedFileHandles, (done, total, name, cached) => {
        if (msgEl) msgEl.textContent = `Parsing ${name}… (${done}/${total})${cached ? ' [cached]' : ''}`;
      });
    } else {
      parsedText = await parseFileListPDFs(_selectedFileList, (done, total, name, cached) => {
        if (msgEl) msgEl.textContent = `Parsing ${name}… (${done}/${total})${cached ? ' [cached]' : ''}`;
      });
    }

    if (parsedText.length === 0 || parsedText.every(t => t.trim().length < 20)) {
      throw new Error('Could not extract readable text from the PDFs. The files may be scanned images (OCR not supported) or empty.');
    }

    // Step 2: Generate questions via LLM
    if (msgEl) msgEl.textContent = 'Generating CBSE/ICSE questions with AI…';
    btn.innerHTML = '<span class="btn-text">🤖 AI is crafting questions…</span>';
    const questions = await generateMCQsFromText(parsedText, numQ, difficulty, className, subject, language);

    if (questions.length === 0) {
      throw new Error('No questions could be generated. Try with different or more detailed PDF content.');
    }

    // Step 3: Feed into existing quiz engine
    if (overlay) overlay.classList.add('hidden');
    btn.innerHTML = origHTML;
    btn.disabled = false;
    startQuizWithQuestions(questions);

  } catch (err) {
    if (overlay) overlay.classList.add('hidden');
    btn.innerHTML = origHTML;
    btn.disabled = false;
    alert('Error: ' + err.message);
    console.error('Study Quiz error:', err);
  }
});

// ── Bridge: feed generated questions into the existing quiz engine ──
function startQuizWithQuestions(questions) {
  // Decode HTML entities (same as web quiz flow)
  questions = questions.map(q => ({
    ...q,
    question: typeof decodeHtml === 'function' ? decodeHtml(q.question) : q.question,
    correct_answer: typeof decodeHtml === 'function' ? decodeHtml(q.correct_answer) : q.correct_answer,
    incorrect_answers: q.incorrect_answers.map(a => typeof decodeHtml === 'function' ? decodeHtml(a) : a),
  }));

  // Shuffle options into the 4-option format the quiz engine expects
  state.questions = questions.map(q => {
    const allOpts = [q.correct_answer, ...q.incorrect_answers].slice(0, 4);
    // Shuffle
    for (let i = allOpts.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [allOpts[i], allOpts[j]] = [allOpts[j], allOpts[i]];
    }
    return {
      ...q,
      options: allOpts,
    };
  });

  state.currentIdx = 0;
  state.score = 0;
  state.answers = [];

  // Use existing quiz rendering functions if available
  if (typeof showScreen === 'function') showScreen($('#quizScreen'));
  if (typeof renderQuestion === 'function') renderQuestion();
}

// ── Init (safe wrap) ──
try {
  populateSubjects();
} catch (e) {
  console.warn('Study Quiz init error:', e);
}
