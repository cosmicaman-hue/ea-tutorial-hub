/* ============================================================
   QuizSpark — AI Quiz App  (app.js)
   Sources: Open Trivia DB · jService (Jeopardy!) · The Trivia API
            Wikipedia · MyMemory Translation
   All free, no API keys required.
   ============================================================ */

// ── State ──
window.state = {
  questions: [],
  currentIdx: 0,
  score: 0,
  answers: [],        // { selected, correct, isCorrect }
  difficulty: 'easy',
  language: 'en',
  region: 'world',
  numQuestions: 10,
  categoryId: null,
  categoryName: '',
  subtopic: '',
  customTopic: '',
  sessionToken: null,
  saveType: 'class',  // class | group | personal
  saveLabel: '',
};
const state = window.state;

// ── Free API Sources ──
// 1. Open Trivia DB  — 7k+ verified questions, 24 categories
//    https://opentdb.com  (no key, max 50/batch)
// 2. jService (Jeopardy!) — 300k+ questions, 100+ categories
//    https://jservice.io   (no key, no rate limit)
// 3. The Trivia API — 4k+ questions, 8 categories, difficulty filter
//    https://the-trivia-api.com  (no key, 20/batch)
// 4. Wikipedia — unlimited custom-topic generation
//    https://en.wikipedia.org/w/api.php  (no key)
// 5. MyMemory — free translation EN→HI
//    https://api.mymemory.translated.net  (no key, 5k/day)

const STORAGE_KEY = 'quizspark_history';

// ── Sub-topic map (category name → subtopics) ──
const SUBTOPICS = {
  'Sports': [
    'Cricket', 'Football (Soccer)', 'Hockey', 'Tennis', 'Badminton',
    'Kabaddi', 'Wrestling', 'Athletics', 'Basketball', 'Boxing',
    'Swimming', 'Chess', 'Formula 1', 'Olympics',
  ],
  'Science & Nature': [
    'Physics', 'Chemistry', 'Biology', 'Astronomy', 'Ecology',
    'Human Body', 'Elements', 'Plants', 'Animals', 'Diseases',
  ],
  'Science: Computers': [
    'Programming', 'Hardware', 'Internet', 'AI & Machine Learning',
    'Cybersecurity', 'Operating Systems', 'Databases', 'Web Development',
  ],
  'History': [
    'Ancient History', 'Medieval Period', 'Modern History',
    'Indian Independence', 'World Wars', 'Cold War',
    'Mughal Empire', 'British Raj', 'Post-1947 India',
  ],
  'Geography': [
    'Countries & Capitals', 'Rivers & Lakes', 'Mountains',
    'Indian Geography', 'World Geography', 'Climate & Weather',
    'Oceans & Seas', 'Deserts', 'Maps',
  ],
  'Politics': [
    'Indian Constitution', 'Elections & Parties', 'Parliament',
    'World Politics', 'International Organizations',
  ],
  'General Knowledge': [
    'Books & Authors', 'Famous Personalities', 'Awards & Honours',
    'Indian GK', 'World GK', 'Inventions', 'Important Days',
  ],
  'Entertainment: Music': [
    'Bollywood Music', 'Classical Music', 'Western Music',
    'Instruments', 'Singers & Composers',
  ],
  'Entertainment: Film': [
    'Bollywood', 'Hollywood', 'Regional Cinema',
    'Awards (Oscars/Filmfare)', 'Directors & Actors',
  ],
  'Mythology': [
    'Hindu Mythology', 'Greek Mythology', 'Ramayana',
    'Mahabharata', 'Vedic Literature',
  ],
  'Art': [
    'Indian Art & Culture', 'Paintings', 'Sculpture',
    'World Art', 'Architecture',
  ],
};

// Category names that have sub-topics (fuzzy match)
function getSubtopicsForCategory(catName) {
  if (!catName) return null;
  // Exact match
  if (SUBTOPICS[catName]) return SUBTOPICS[catName];
  // Fuzzy: check if any key is a substring of catName or vice-versa
  for (const key of Object.keys(SUBTOPICS)) {
    if (catName.toLowerCase().includes(key.toLowerCase()) ||
        key.toLowerCase().includes(catName.toLowerCase())) {
      return SUBTOPICS[key];
    }
  }
  return null;
}

// ── DOM refs ──
window.$ = (sel) => document.querySelector(sel);
window.$$ = (sel) => document.querySelectorAll(sel);
const $ = window.$;
const $$ = window.$$;

const setupScreen  = $('#setupScreen');
const quizScreen   = $('#quizScreen');
const resultsScreen = $('#resultsScreen');
const loadingOverlay = $('#loadingOverlay');
window.loadingOverlay = loadingOverlay;

const categorySelect  = $('#categorySelect');
const customTopic     = $('#customTopic');
const numQuestions    = $('#numQuestions');
const numDisplay      = $('#numDisplay');
const quizForm        = $('#quizForm');
window.quizForm = quizForm;
const subtopicGroup   = $('#subtopicGroup');
const subtopicSelect  = $('#subtopicSelect');

// Save modal
const saveModal       = $('#saveModal');
const saveDate        = $('#saveDate');
const saveLabel       = $('#saveLabel');
const saveConfirmBtn  = $('#saveConfirmBtn');
const saveCancelBtn   = $('#saveCancelBtn');
const saveBtn         = $('#saveBtn');

// History screen
const historyScreen   = $('#historyScreen');
const historyBtn      = $('#historyBtn');
const historyBackBtn  = $('#historyBackBtn');
const historyList     = $('#historyList');
const historyEmpty    = $('#historyEmpty');

// Detail modal
const quizDetailModal = $('#quizDetailModal');
const detailTitle     = $('#detailTitle');
const detailMeta      = $('#detailMeta');
const detailReview    = $('#detailReview');
const detailCloseBtn  = $('#detailCloseBtn');
const detailCloseBtn2 = $('#detailCloseBtn2');
const detailDeleteBtn = $('#detailDeleteBtn');

const qCurrent    = $('#qCurrent');
const qTotal      = $('#qTotal');
const liveScore   = $('#liveScore');
const progressFill = $('#progressFill');
const questionCard = $('#questionCard');
const qCategoryBadge = $('#qCategoryBadge');
const questionText = $('#questionText');
const optionsContainer = $('#optionsContainer');
const nextBtn     = $('#nextBtn');
const nextBtnText = $('#nextBtnText');

const resultsEmoji   = $('#resultsEmoji');
const resultsTitle   = $('#resultsTitle');
const resultsSubtitle = $('#resultsSubtitle');
const finalScore     = $('#finalScore');
const finalTotal     = $('#finalTotal');
const ringFill       = $('#ringFill');
const scorePercent   = $('#scorePercent');
const reviewList     = $('#reviewList');
const retryBtn       = $('#retryBtn');
const homeBtn        = $('#homeBtn');
const quitBtn        = $('#quitBtn');
const loadingMsg     = $('#loadingMsg');
window.loadingMsg = loadingMsg;

// ── Open Trivia DB helpers ──
const OTDB_BASE = 'https://opentdb.com';

// Store fetched categories for name lookup
let _categoriesCache = [];

async function fetchCategories() {
  const res = await fetch(`${OTDB_BASE}/api_category.php`);
  const data = await res.json();
  _categoriesCache = data.trivia_categories || [];
  return _categoriesCache;
}

function getCategoryNameById(id) {
  const cat = _categoriesCache.find(c => c.id === id);
  return cat ? cat.name : '';
}

async function fetchSessionToken() {
  try {
    const res = await fetch(`${OTDB_BASE}/api_token.php?command=request`);
    const data = await res.json();
    if (data.response_code === 0) state.sessionToken = data.token;
  } catch { /* non-critical */ }
}

// ── Open Trivia DB — batch fetch (supports up to 50) ──
async function fetchQuestions({ amount, category, difficulty }) {
  const BATCH = 10; // OTDB reliable batch size
  const batches = Math.ceil(amount / BATCH);
  const allQ = [];

  for (let b = 0; b < batches; b++) {
    const batchAmt = Math.min(BATCH, amount - allQ.length);
    let url = `${OTDB_BASE}/api.php?amount=${batchAmt}&type=multiple`;
    if (category) url += `&category=${category}`;
    if (difficulty && difficulty !== 'mixed') url += `&difficulty=${difficulty}`;
    if (state.sessionToken) url += `&token=${state.sessionToken}`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      if (data.response_code === 4 && state.sessionToken) {
        await fetch(`${OTDB_BASE}/api_token.php?command=reset&token=${state.sessionToken}`);
        const retry = await fetch(url);
      const retryData = await retry.json();
        if (retryData.response_code === 0) allQ.push(...(retryData.results || []));
      } else if (data.response_code === 0) {
        allQ.push(...(data.results || []));
      }
    } catch { /* skip failed batch */ }
    if (allQ.length >= amount) break;
  }
  return allQ.slice(0, amount);
}

// ── jService (Jeopardy!) — 300k+ questions, no key ──
const JSERVICE_CATS = {
  21: 'Sports', 22: 'Geography', 25: 'Science', 26: 'History',
  27: 'Art', 28: 'Politics', 30: 'Television', 31: 'Film',
  32: 'Music', 36: 'Science', 42: 'Sports', 49: 'Science',
  57: 'Nature', 67: 'History', 83: 'Science', 99: 'History',
  105: 'Science', 114: 'History', 136: 'Geography', 218: 'Science',
  268: 'History', 318: 'Science', 374: 'Science', 415: 'Art',
  442: 'Geography', 492: 'Science', 530: 'Science', 561: 'Science',
  613: 'History', 673: 'Science', 742: 'Geography', 800: 'Science',
  822: 'History', 897: 'Science', 948: 'Science', 1065: 'History',
  1122: 'Science', 1204: 'History', 1262: 'Science', 1329: 'History',
  1408: 'History', 1478: 'Science', 1545: 'History', 1605: 'Science',
  1684: 'History', 1742: 'Science', 1802: 'History', 1866: 'Science',
  1917: 'History', 1975: 'Science', 2039: 'History', 2097: 'Science',
  2157: 'History', 2216: 'Science', 2275: 'History', 2334: 'Science',
  2398: 'History', 2456: 'Science', 2515: 'History', 2574: 'Science',
};

async function fetchJserviceQuestions(amount, categoryId) {
  try {
    // Pick random Jeopardy categories for variety
    const catIds = Object.keys(JSERVICE_CATS).map(Number);
    const randomCats = shuffle([...catIds]).slice(0, 5);
    const allQ = [];

    for (const catId of randomCats) {
      if (allQ.length >= amount) break;
      try {
        const res = await fetch(`https://jservice.io/api/clues?category=${catId}&count=${Math.min(amount, 10)}`);
        const data = await res.json();
        for (const clue of data) {
          if (clue.question && clue.answer && clue.question.length > 5) {
            allQ.push({
              question: clue.question,
              correct_answer: clue.answer.replace(/<[^>]*>/g, '').replace(/^<i>|<\/i>$/g, '').trim(),
              incorrect_answers: generateDistractors(clue.answer.replace(/<[^>]*>/g, '').trim(), 'definition'),
              category: clue.category?.title || JSERVICE_CATS[catId] || 'General',
              difficulty: clue.value ? (clue.value <= 400 ? 'easy' : clue.value <= 800 ? 'medium' : 'hard') : 'medium',
              source: 'jservice',
            });
          }
        }
      } catch { /* skip */ }
    }
    shuffle(allQ);
    return allQ.slice(0, amount);
  } catch {
    return [];
  }
}

// ── The Trivia API — 4k+ questions, difficulty filter ──
const TRIVIA_API_CATS = [
  'arts_and_literature', 'film_and_tv', 'food_and_drink',
  'general_knowledge', 'geography', 'history', 'music',
  'science', 'society_and_culture', 'sport_and_leisure',
];

function mapOtdbToTriviaApiCat(otdbName) {
  const n = otdbName?.toLowerCase() || '';
  if (n.includes('book') || n.includes('art') || n.includes('myth')) return 'arts_and_literature';
  if (n.includes('film') || n.includes('television') || n.includes('entertainment')) return 'film_and_tv';
  if (n.includes('science') || n.includes('nature') || n.includes('computer')) return 'science';
  if (n.includes('geograph')) return 'geography';
  if (n.includes('histor')) return 'history';
  if (n.includes('music')) return 'music';
  if (n.includes('sport')) return 'sport_and_leisure';
  if (n.includes('politic') || n.includes('society')) return 'society_and_culture';
  return null; // null = all categories
}

async function fetchTriviaApiQuestions(amount, difficulty, categoryName) {
  try {
    const diff = difficulty === 'mixed' ? undefined : difficulty;
    const cat = mapOtdbToTriviaApiCat(categoryName);
    let url = `https://the-trivia-api.com/api/questions?limit=${Math.min(amount, 20)}`;
    if (diff) url += `&difficulty=${diff}`;
    if (cat) url += `&categories=${cat}`;

    const res = await fetch(url);
    const data = await res.json();
    return (data || []).map(q => ({
      question: q.question,
      correct_answer: q.correctAnswer,
      incorrect_answers: q.incorrectAnswers,
      category: q.category || categoryName || 'General',
      difficulty: q.difficulty || difficulty,
      source: 'trivia_api',
    }));
  } catch {
    return [];
  }
}

// ── Custom topic: search Wikipedia (expanded) + generate questions ──
async function fetchCustomTopicQuestions(topic, amount, difficulty, region = 'world') {
  const searchTopic = region === 'india' ? `${topic} India` : topic;
  loadingMsg.textContent = `Searching the web for "${searchTopic}"…`;

  // 1. Search Wikipedia — get 10 results (up from 5)
  const searchRes = await fetch(
    `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(searchTopic)}&srlimit=10&format=json&origin=*`
  );
  const searchData = await searchRes.json();
  const pages = searchData.query?.search || [];

  if (pages.length === 0) {
    throw new Error(`No information found for "${topic}". Try a different topic.`);
  }

  // 2. Get FULL extracts (not just summaries) — much more text = more questions
  const summaries = [];
  const pageTitles = pages.slice(0, 7).map(p => p.title);

  // Batch fetch using wiki API (prop=extracts, exintro=0 for full text)
  try {
    const titlesStr = pageTitles.join('|');
    const extRes = await fetch(
      `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(titlesStr)}&prop=extracts&exintro=0&explaintext=1&exsectionformat=plain&format=json&origin=*`
    );
    const extData = await extRes.json();
    const pageEntries = extData.query?.pages || {};
    for (const [, pg] of Object.entries(pageEntries)) {
      if (pg.extract && pg.extract.length > 100) {
        summaries.push({ title: pg.title, extract: pg.extract });
      }
    }
  } catch { /* fallback to individual summaries */ }

  // Fallback: if batch failed, try individual REST summaries
  if (summaries.length === 0) {
    for (const title of pageTitles.slice(0, 5)) {
      try {
        const sumRes = await fetch(
          `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`
        );
        const sumData = await sumRes.json();
        if (sumData.extract) {
          summaries.push({ title: sumData.title, extract: sumData.extract });
        }
      } catch { /* skip */ }
    }
  }

  if (summaries.length === 0) {
    throw new Error(`Could not extract info for "${topic}". Try a broader topic.`);
  }

  // 3. If India region, also search Hindi Wikipedia for richer India content
  if (region === 'india') {
    try {
      const hiRes = await fetch(
        `https://hi.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(topic)}&srlimit=5&format=json&origin=*`
      );
      const hiData = await hiRes.json();
      const hiPages = hiData.query?.search || [];
      const hiTitles = hiPages.slice(0, 3).map(p => p.title);
      try {
        const hiExtRes = await fetch(
          `https://hi.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(hiTitles.join('|'))}&prop=extracts&exintro=0&explaintext=1&format=json&origin=*`
        );
        const hiExtData = await hiExtRes.json();
        const hiEntries = hiExtData.query?.pages || {};
        for (const [, pg] of Object.entries(hiEntries)) {
          if (pg.extract && pg.extract.length > 100) {
            summaries.push({ title: pg.title, extract: pg.extract });
          }
        }
      } catch { /* Hindi wiki not critical */ }
    } catch { /* Hindi wiki not critical */ }
  }

  // 4. Generate quiz questions from the expanded text
  loadingMsg.textContent = 'Generating questions from search results…';
  const questions = generateQuestionsFromText(summaries, topic, amount, difficulty);
  return questions;
}

// ── Question generator from text (expanded for full Wikipedia extracts) ──
function generateQuestionsFromText(summaries, topic, amount, difficulty) {
  const allQuestions = [];
  const diffVal = difficulty === 'mixed' ? undefined : difficulty;

  for (const { title, extract } of summaries) {
    // Split into paragraphs then sentences — full extracts have \n\n paragraphs
    const paragraphs = extract.split(/\n{2,}/);
    for (const para of paragraphs) {
      const sentences = para
        .replace(/\. /g, '.\n')
        .split('\n')
        .map(s => s.trim())
        .filter(s => s.length > 25);

      for (const sentence of sentences) {
        // Pattern 1: "X is/was/are Y" → "What is X?"
        const isMatch = sentence.match(/^(.+?)\s+(is|was|are)\s+(.{5,}?)$/i);
        if (isMatch) {
          const subject = isMatch[1].trim();
          const verb = isMatch[2];
          let complement = isMatch[3].replace(/\.$/, '').trim();
          // Truncate overly long complements
          if (complement.length > 120) complement = complement.substring(0, 120).replace(/\s+\S*$/, '…');
          if (subject.length > 2 && complement.length > 5 && !complement.includes('\n')) {
            allQuestions.push({
              question: `What ${verb} ${subject}?`,
              correct_answer: complement,
              incorrect_answers: generateDistractors(complement, 'definition'),
              category: topic,
              difficulty: diffVal || (complement.length > 60 ? 'hard' : 'easy'),
              source: 'wikipedia',
            });
          }
        }

        // Pattern 2: Contains a year → fill-in-the-blank
        const yearMatches = [...sentence.matchAll(/(?:in|since|from|during|around|established|founded|born|died)\s+(?:the\s+)?(?:year\s+)?(\d{3,4})/gi)];
        for (const ym of yearMatches) {
          const year = ym[1];
          const context = sentence.replace(year, '______').replace(/\.$/, '').trim();
          if (context.length > 20 && context.length < 200) {
            allQuestions.push({
              question: `Fill in the blank: ${context}`,
              correct_answer: year,
              incorrect_answers: generateYearDistractors(parseInt(year)),
              category: topic,
              difficulty: diffVal || 'hard',
              source: 'wikipedia',
            });
          }
        }

        // Pattern 3: "X includes/contains/has Y"
        const includesMatch = sentence.match(/^(.+?)\s+(includes?|contains?|consists?\s+of|has)\s+(.{5,}?)$/i);
        if (includesMatch) {
          const subject = includesMatch[1].trim();
          const verb = includesMatch[2];
          let object = includesMatch[3].replace(/\.$/, '').trim();
          if (object.length > 120) object = object.substring(0, 120).replace(/\s+\S*$/, '…');
          if (subject.length > 2 && object.length > 5 && !object.includes('\n')) {
            allQuestions.push({
              question: `What ${verb} ${subject}?`,
              correct_answer: object,
              incorrect_answers: generateDistractors(object, 'list'),
              category: topic,
              difficulty: diffVal || 'medium',
              source: 'wikipedia',
            });
          }
        }

        // Pattern 4: "X — Y" or "X: Y" (definition/clarification)
        const dashMatch = sentence.match(/^(.{5,40}?)\s*[—–:]\s*(.{10,}?)$/);
        if (dashMatch) {
          const term = dashMatch[1].trim();
          let def = dashMatch[2].replace(/\.$/, '').trim();
          if (def.length > 120) def = def.substring(0, 120).replace(/\s+\S*$/, '…');
          if (!def.includes('\n') && !term.includes('?')) {
            allQuestions.push({
              question: `What is ${term}?`,
              correct_answer: def,
              incorrect_answers: generateDistractors(def, 'definition'),
              category: topic,
              difficulty: diffVal || 'medium',
              source: 'wikipedia',
            });
          }
        }

        // Pattern 5: Number fact → "How many…"
        const numMatch = sentence.match(/(?:has|have|with|of|about|approximately|over)\s+([\d,]+(?:\s+(?:million|billion|thousand|hundred))?)\s+(.{3,20}?)/i);
        if (numMatch) {
          const num = numMatch[1];
          const unit = numMatch[2].replace(/\.$/, '').trim();
          allQuestions.push({
            question: `How many ${unit} does ${title} have?`,
            correct_answer: num,
            incorrect_answers: generateDistractors(num, 'number'),
            category: topic,
            difficulty: diffVal || 'medium',
            source: 'wikipedia',
          });
        }

        // Pattern 6: General fill-in-the-blank from longer sentences
        const words = sentence.split(/\s+/);
        if (words.length > 8 && words.length < 40) {
          const candidates = words
            .map((w, i) => ({ word: w.replace(/[.,;:!?()\[\]]/g, ''), idx: i }))
            .filter(w => w.word.length > 4 && !['which','where','there','their','these','those','about','other','after','being','would','could','should','since','while','during','before','between','through','however','although','because','therefore'].includes(w.word.toLowerCase()));

          if (candidates.length > 0) {
            const pick = candidates[Math.floor(Math.random() * candidates.length)];
            const blanked = [...words];
            blanked[pick.idx] = '______';
            const qText = blanked.join(' ').replace(/\.$/, '');
            if (qText.length < 200) {
              allQuestions.push({
                question: `Fill in the blank: ${qText}`,
                correct_answer: pick.word,
                incorrect_answers: generateDistractors(pick.word, 'word'),
                category: topic,
                difficulty: diffVal || 'easy',
                source: 'wikipedia',
              });
            }
          }
        }
      }
    }
  }

  // Dedup by question text similarity
  const seen = new Set();
  const unique = [];
  for (const q of allQuestions) {
    const key = q.question.toLowerCase().replace(/[^a-z0-9]/g, '').substring(0, 60);
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(q);
    }
  }

  shuffle(unique);
  return unique.slice(0, amount);
}

// Generate wrong answer options (distractors)
function generateDistractors(correct, type) {
  const distractors = [];
  const correctLower = correct.toLowerCase();

  if (type === 'definition') {
    // Generic wrong definitions
    const generic = [
      'A type of musical instrument',
      'A chemical compound found in nature',
      'An ancient philosophical concept',
      'A mathematical theorem',
      'A form of traditional art',
      'A rare geological formation',
      'A method of transportation',
      'A type of computer algorithm',
    ];
    shuffle(generic);
    for (const g of generic) {
      if (g.toLowerCase() !== correctLower && distractors.length < 3) distractors.push(g);
    }
  } else if (type === 'list') {
    // Modify the correct answer slightly
    const words = correct.split(/,\s*/);
    if (words.length >= 2) {
      // Remove one item
      const shortened = words.slice(1).join(', ');
      distractors.push(shortened);
      // Shuffle items
      const shuffled = [...words];
      shuffle(shuffled);
      distractors.push(shuffled.join(', '));
      // Add generic
      distractors.push('Various unrelated elements');
    } else {
      distractors.push('None of the above', 'Various unknown items', 'Not applicable');
    }
    while (distractors.length < 3) distractors.push('Unknown');
  } else if (type === 'number') {
    // Number distractors — multiply/divide
    const num = parseFloat(correct.replace(/,/g, ''));
    if (!isNaN(num)) {
      const multipliers = [0.5, 1.5, 2, 0.25, 3, 0.75, 1.2, 0.8];
      shuffle(multipliers);
      for (const m of multipliers) {
        if (distractors.length >= 3) break;
        const fake = Math.round(num * m);
        if (fake !== num && fake > 0) distractors.push(fake.toLocaleString());
      }
    }
    while (distractors.length < 3) distractors.push(String(Math.round(num * (distractors.length + 2))));
  } else {
    // Word-level distractors
    const prefixes = ['un', 'non', 'anti', 'pre', 'post', 'sub', 'meta', 'pseudo'];
    for (const p of prefixes) {
      if (distractors.length >= 3) break;
      const fake = p + correctLower;
      if (fake !== correctLower) distractors.push(fake.charAt(0).toUpperCase() + fake.slice(1));
    }
    while (distractors.length < 3) {
      distractors.push(`Option ${distractors.length + 2}`);
    }
  }

  return distractors.slice(0, 3);
}

function generateYearDistractors(year) {
  const offsets = [-50, -20, -10, 10, 20, 50, 100, -100];
  shuffle(offsets);
  return offsets.slice(0, 3).map(o => String(year + o));
}

// ── Multi-source aggregator with dedup ──
async function fetchFromAllSources(amount, categoryId, categoryName, difficulty, region, subtopic, customTopic) {
  const effectiveTopic = customTopic || (subtopic || categoryName) || 'general knowledge';
  const isCustomOrIndia = (subtopic && categoryId) || (region === 'india' && categoryId) || (customTopic && !categoryId);

  const allQuestions = [];
  const errors = [];

  // Source 1: Open Trivia DB (batch up to 50)
  loadingMsg.textContent = 'Fetching from Open Trivia DB…';
  try {
    const otdbQ = await fetchQuestions({ amount, category: categoryId, difficulty });
    otdbQ.forEach(q => { q.source = 'otdb'; });
    allQuestions.push(...otdbQ);
  } catch (e) { errors.push('OTDB: ' + e.message); }

  // Source 2: The Trivia API (up to 20)
  if (allQuestions.length < amount) {
    loadingMsg.textContent = 'Fetching from The Trivia API…';
    try {
      const triviaQ = await fetchTriviaApiQuestions(Math.min(amount, 20), difficulty, categoryName);
      allQuestions.push(...triviaQ);
    } catch (e) { errors.push('TriviaAPI: ' + e.message); }
  }

  // Source 3: jService / Jeopardy! (up to 50)
  if (allQuestions.length < amount) {
    loadingMsg.textContent = 'Fetching from Jeopardy! database…';
    try {
      const jsQ = await fetchJserviceQuestions(Math.min(amount, 50), categoryId);
      allQuestions.push(...jsQ);
    } catch (e) { errors.push('jService: ' + e.message); }
  }

  // Source 4: Wikipedia custom topic (if custom/India/subtopic)
  if (isCustomOrIndia || allQuestions.length < amount) {
    loadingMsg.textContent = 'Searching Wikipedia for custom questions…';
    try {
      const wikiQ = await fetchCustomTopicQuestions(effectiveTopic, amount, difficulty, region);
      allQuestions.push(...wikiQ);
    } catch (e) { errors.push('Wikipedia: ' + e.message); }
  }

  // Dedup across sources by normalized question text
  const seen = new Set();
  const unique = [];
  for (const q of allQuestions) {
    const key = q.question.toLowerCase().replace(/[^a-z0-9]/g, '').substring(0, 60);
    if (!seen.has(key) && q.question.length > 5) {
      seen.add(key);
      unique.push(q);
    }
  }

  shuffle(unique);
  return unique.slice(0, amount);
}

// ── Translation (English → Hindi) via MyMemory ──
async function translateToHindi(text) {
  try {
    const res = await fetch(
      `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=en|hi`
    );
    const data = await res.json();
    if (data.responseStatus === 200 && data.responseData?.translatedText) {
      return data.responseData.translatedText;
    }
    return text; // fallback to English
  } catch {
    return text;
  }
}

// Batch translate questions to Hindi
async function translateQuestionsToHindi(questions) {
  loadingMsg.textContent = 'Translating questions to Hindi…';
  const translated = [];
  for (let i = 0; i < questions.length; i++) {
    const q = questions[i];
    const [question, correct, ...incorrect] = await Promise.all([
      translateToHindi(decodeHtml(q.question)),
      translateToHindi(decodeHtml(q.correct_answer)),
      ...q.incorrect_answers.map(a => translateToHindi(decodeHtml(a))),
    ]);
    translated.push({
      ...q,
      question,
      correct_answer: correct,
      incorrect_answers: incorrect,
    });
    // Small delay to avoid rate limiting
    if (i % 5 === 4) await sleep(300);
  }
  return translated;
}

// ── HTML entity decoder ──
function decodeHtml(html) {
  const txt = document.createElement('textarea');
  txt.innerHTML = html;
  return txt.value;
}

// ── Utility ──
function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── KaTeX Math Rendering ──
// Call after injecting HTML that may contain LaTeX ($...$ or $$...$$)
function renderMath(el) {
  if (typeof renderMathInElement === 'function') {
    renderMathInElement(el || document.body, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
      ],
      throwOnError: false,
    });
  }
}

function showScreen(screen) {
  [setupScreen, quizScreen, resultsScreen, historyScreen].forEach(s => s.classList.remove('active'));
  screen.classList.add('active');
}

function showLoading(msg) {
  loadingMsg.textContent = msg || 'Loading…';
  loadingOverlay.classList.remove('hidden');
}
function hideLoading() { loadingOverlay.classList.add('hidden'); }

// ── Initialize categories dropdown ──
async function initCategories() {
  try {
    const cats = await fetchCategories();
    cats.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      categorySelect.appendChild(opt);
    });
  } catch {
    // If API fails, add some defaults
    const defaults = [
      { id: 9, name: 'General Knowledge' },
      { id: 17, name: 'Science & Nature' },
      { id: 18, name: 'Computers' },
      { id: 21, name: 'Sports' },
      { id: 23, name: 'History' },
      { id: 22, name: 'Geography' },
    ];
    defaults.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      categorySelect.appendChild(opt);
    });
  }
}

// ── Chip selection logic ──
function initChips() {
  $$('.difficulty-chips .chip').forEach(chip => {
    chip.addEventListener('click', () => {
      $$('.difficulty-chips .chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.difficulty = chip.dataset.value;
    });
  });

  $$('.lang-chips .chip').forEach(chip => {
    chip.addEventListener('click', () => {
      $$('.lang-chips .chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.language = chip.dataset.value;
    });
  });

  $$('.region-chips .chip').forEach(chip => {
    chip.addEventListener('click', () => {
      $$('.region-chips .chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.region = chip.dataset.value;
    });
  });
}

// ── Dynamic sub-topic dropdown ──
function updateSubtopics() {
  const catId = categorySelect.value;
  const catName = catId ? getCategoryNameById(parseInt(catId)) : '';
  const subtopics = getSubtopicsForCategory(catName);

  if (subtopics) {
    subtopicGroup.classList.remove('hidden');
    subtopicSelect.innerHTML = '<option value="">— All sub-topics —</option>';
    subtopics.forEach(st => {
      const opt = document.createElement('option');
      opt.value = st;
      opt.textContent = st;
      subtopicSelect.appendChild(opt);
    });
  } else {
    subtopicGroup.classList.add('hidden');
    subtopicSelect.innerHTML = '<option value="">— All sub-topics —</option>';
  }
}

categorySelect.addEventListener('change', updateSubtopics);

// Clear category when typing custom topic
customTopic.addEventListener('input', () => {
  if (customTopic.value.trim()) {
    categorySelect.value = '';
    subtopicGroup.classList.add('hidden');
  }
});
// Clear custom topic when selecting category
categorySelect.addEventListener('change', () => {
  if (categorySelect.value) {
    customTopic.value = '';
  }
});

// ── Slider ──
numQuestions.addEventListener('input', () => {
  numDisplay.textContent = numQuestions.value;
  state.numQuestions = parseInt(numQuestions.value);
});

// ── Form submit ──
quizForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const catId = categorySelect.value;
  const custom = customTopic.value.trim();

  if (!catId && !custom) {
    categorySelect.focus();
    categorySelect.style.borderColor = 'var(--danger)';
    setTimeout(() => categorySelect.style.borderColor = '', 2000);
    return;
  }

  state.categoryId = catId ? parseInt(catId) : null;
  state.categoryName = catId ? getCategoryNameById(parseInt(catId)) : '';
  state.subtopic = subtopicSelect.value;
  state.customTopic = custom;
  state.numQuestions = parseInt(numQuestions.value);

  showLoading('Generating your quiz…');

  try {
    // Always use multi-source aggregator for maximum question count
    let questions = await fetchFromAllSources(
      state.numQuestions,
      state.categoryId,
      state.categoryName,
      state.difficulty,
      state.region,
      state.subtopic,
      state.customTopic
    );

    if (questions.length === 0) {
      throw new Error('No questions available for this combination. Try a different topic or reduce the number of questions.');
    }

    // Decode HTML entities
    questions = questions.map(q => ({
      ...q,
      question: decodeHtml(q.question),
      correct_answer: decodeHtml(q.correct_answer),
      incorrect_answers: q.incorrect_answers.map(a => decodeHtml(a)),
    }));

    // Translate to Hindi if needed
    if (state.language === 'hi') {
      questions = await translateQuestionsToHindi(questions);
    }

    // Shuffle options for each question
    state.questions = questions.map(q => {
      const options = [q.correct_answer, ...q.incorrect_answers];
      shuffle(options);
      return { ...q, options };
    });

    state.currentIdx = 0;
    state.score = 0;
    state.answers = [];

    hideLoading();
    startQuiz();
  } catch (err) {
    hideLoading();
    alert(err.message || 'Failed to generate quiz. Please try again.');
  }
});

// ── Quiz flow ──
function startQuiz() {
  qTotal.textContent = state.questions.length;
  showScreen(quizScreen);
  renderQuestion();
}

function renderQuestion() {
  const q = state.questions[state.currentIdx];
  const idx = state.currentIdx;

  qCurrent.textContent = idx + 1;
  liveScore.textContent = state.score;
  progressFill.style.width = `${((idx) / state.questions.length) * 100}%`;

  qCategoryBadge.textContent = q.category || state.customTopic || 'Quiz';
  questionText.textContent = q.question;
  renderMath(questionText);

  // Re-animate card
  questionCard.style.animation = 'none';
  questionCard.offsetHeight; // reflow
  questionCard.style.animation = '';

  // Render options
  const letters = ['A', 'B', 'C', 'D'];
  optionsContainer.innerHTML = '';

  q.options.forEach((opt, i) => {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.innerHTML = `<span class="option-letter">${letters[i]}</span><span class="option-text">${opt}</span>`;
    btn.addEventListener('click', () => handleAnswer(i));
    optionsContainer.appendChild(btn);
  });
  renderMath(optionsContainer);

  nextBtn.classList.add('hidden');
  nextBtnText.textContent = idx < state.questions.length - 1 ? 'Next Question' : 'See Results';
}

function handleAnswer(selectedIdx) {
  const q = state.questions[state.currentIdx];
  const correctIdx = q.options.indexOf(q.correct_answer);
  const isCorrect = selectedIdx === correctIdx;

  if (isCorrect) state.score++;

  state.answers.push({
    question: q.question,
    selected: q.options[selectedIdx],
    correct: q.correct_answer,
    isCorrect,
  });

  // Visual feedback
  const btns = optionsContainer.querySelectorAll('.option-btn');
  btns.forEach((btn, i) => {
    btn.classList.add('disabled');
    if (i === correctIdx) btn.classList.add('correct');
    if (i === selectedIdx && !isCorrect) btn.classList.add('wrong');
  });

  liveScore.textContent = state.score;
  nextBtn.classList.remove('hidden');
}

nextBtn.addEventListener('click', () => {
  state.currentIdx++;
  if (state.currentIdx >= state.questions.length) {
    showResults();
  } else {
    renderQuestion();
  }
});

// ── Quit ──
quitBtn.addEventListener('click', () => {
  if (confirm('Quit quiz? Your progress will be lost.')) {
    showScreen(setupScreen);
  }
});

// ── Results ──
function showResults() {
  const total = state.questions.length;
  const pct = Math.round((state.score / total) * 100);

  finalScore.textContent = state.score;
  finalTotal.textContent = total;
  scorePercent.textContent = `${pct}%`;

  // Emoji & title
  if (pct >= 90) { resultsEmoji.textContent = '🏆'; resultsTitle.textContent = 'Outstanding!'; }
  else if (pct >= 70) { resultsEmoji.textContent = '🎉'; resultsTitle.textContent = 'Great Job!'; }
  else if (pct >= 50) { resultsEmoji.textContent = '👍'; resultsTitle.textContent = 'Good Effort!'; }
  else if (pct >= 30) { resultsEmoji.textContent = '📚'; resultsTitle.textContent = 'Keep Learning!'; }
  else { resultsEmoji.textContent = '💪'; resultsTitle.textContent = 'Don\'t Give Up!'; }

  // Animate ring
  const circumference = 2 * Math.PI * 52; // ~326.73
  const offset = circumference - (pct / 100) * circumference;
  ringFill.style.strokeDashoffset = offset;

  // Ring color
  if (pct >= 70) ringFill.style.stroke = 'var(--success)';
  else if (pct >= 40) ringFill.style.stroke = 'var(--warning)';
  else ringFill.style.stroke = 'var(--danger)';

  // Review list
  reviewList.innerHTML = '';
  state.answers.forEach((a, i) => {
    const div = document.createElement('div');
    div.className = `review-item ${a.isCorrect ? 'review-correct' : 'review-wrong'}`;
    div.innerHTML = `
      <div class="review-q">${i + 1}. ${a.question}</div>
      <div class="review-answer">
        ${a.isCorrect
          ? `<span class="your-ans">✅ ${a.selected}</span>`
          : `<span class="your-ans">❌ ${a.selected}</span> → <strong>✅ ${a.correct}</strong>`
        }
      </div>
    `;
    reviewList.appendChild(div);
  });
  renderMath(reviewList);

  showScreen(resultsScreen);
}

// ── Retry / Home ──
retryBtn.addEventListener('click', () => {
  showLoading('Regenerating quiz…');
  quizForm.dispatchEvent(new Event('submit'));
});

homeBtn.addEventListener('click', () => {
  showScreen(setupScreen);
});

// ══════════════════════════════════════════════════════════
// ── SAVE SYSTEM (date-wise, class/group/personal) ──
// ══════════════════════════════════════════════════════════

function getSavedQuizzes() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveQuizToStorage(entry) {
  const quizzes = getSavedQuizzes();
  quizzes.unshift(entry); // newest first
  // Keep max 100 saved quizzes
  if (quizzes.length > 100) quizzes.length = 100;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(quizzes));
  } catch {
    // Storage full — remove oldest
    quizzes.pop();
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(quizzes)); } catch { /* give up */ }
  }
}

function deleteQuizFromStorage(id) {
  const quizzes = getSavedQuizzes().filter(q => q.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(quizzes));
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) +
    ' ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

// ── Save modal ──
saveBtn.addEventListener('click', () => {
  const now = new Date();
  saveDate.value = formatDate(now.toISOString());
  state.saveType = 'class';
  state.saveLabel = '';
  saveLabel.value = '';
  // Reset chips
  $$('.save-as-chips .chip').forEach(c => c.classList.remove('active'));
  $$('.save-as-chips .chip')[0].classList.add('active');
  saveModal.classList.remove('hidden');
});

saveCancelBtn.addEventListener('click', () => {
  saveModal.classList.add('hidden');
});

$$('.save-as-chips .chip').forEach(chip => {
  chip.addEventListener('click', () => {
    $$('.save-as-chips .chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    state.saveType = chip.dataset.value;
  });
});

saveConfirmBtn.addEventListener('click', () => {
  const label = saveLabel.value.trim() || state.saveType;
  const entry = {
    id: Date.now() + Math.random(),
    date: new Date().toISOString(),
    saveType: state.saveType,
    label: label,
    topic: state.customTopic || state.categoryName || 'Quiz',
    subtopic: state.subtopic || '',
    region: state.region,
    difficulty: state.difficulty,
    language: state.language,
    score: state.score,
    total: state.questions.length,
    pct: Math.round((state.score / state.questions.length) * 100),
    questions: state.questions.map((q, i) => ({
      question: q.question,
      correct_answer: q.correct_answer,
      options: q.options,
      category: q.category,
      difficulty: q.difficulty,
      source: q.source || 'unknown',
      answer: state.answers[i] || null,
    })),
  };

  saveQuizToStorage(entry);
  saveModal.classList.add('hidden');

  // Brief visual feedback
  saveBtn.textContent = '✅ Saved!';
  setTimeout(() => { saveBtn.textContent = '💾 Save Quiz'; }, 2000);
});

// ── History screen ──
historyBtn.addEventListener('click', () => {
  renderHistory();
  showScreen(historyScreen);
});

historyBackBtn.addEventListener('click', () => {
  showScreen(setupScreen);
});

function renderHistory() {
  const quizzes = getSavedQuizzes();
  historyList.innerHTML = '';

  if (quizzes.length === 0) {
    historyEmpty.classList.remove('hidden');
    return;
  }
  historyEmpty.classList.add('hidden');

  quizzes.forEach(q => {
    const pctClass = q.pct >= 70 ? 'good' : q.pct >= 40 ? 'mid' : 'low';
    const typeIcon = q.saveType === 'class' ? '🏫' : q.saveType === 'group' ? '👥' : '👤';
    const div = document.createElement('div');
    div.className = 'history-card';
    div.innerHTML = `
      <div class="history-card-top">
        <span class="history-card-date">${formatDate(q.date)}</span>
        <span class="history-card-score ${pctClass}">${q.score}/${q.total} (${q.pct}%)</span>
      </div>
      <div class="history-card-info">
        <strong>${q.topic}</strong>${q.subtopic ? ' › ' + q.subtopic : ''} · ${q.difficulty} · ${q.region === 'india' ? '🇮🇳' : '🌍'}
      </div>
      <div class="history-card-tags">
        <span class="detail-tag">${typeIcon} ${q.label}</span>
        ${q.language === 'hi' ? '<span class="detail-tag">हिन्दी</span>' : ''}
      </div>
    `;
    div.addEventListener('click', () => showQuizDetail(q));
    historyList.appendChild(div);
  });
}

// ── Quiz detail modal ──
let _currentDetailId = null;

function showQuizDetail(q) {
  _currentDetailId = q.id;
  const typeIcon = q.saveType === 'class' ? '🏫' : q.saveType === 'group' ? '👥' : '👤';
  detailTitle.textContent = `${q.topic} — ${q.subtopic || 'All'}`;
  detailMeta.innerHTML = `
    <span class="detail-tag">📅 ${formatDate(q.date)}</span>
    <span class="detail-tag">${typeIcon} ${q.label}</span>
    <span class="detail-tag">🎯 ${q.difficulty}</span>
    <span class="detail-tag">${q.region === 'india' ? '🇮🇳 India' : '🌍 World'}</span>
    <span class="detail-tag">✅ ${q.score}/${q.total} (${q.pct}%)</span>
  `;

  detailReview.innerHTML = '';
  q.questions.forEach((qq, i) => {
    const a = qq.answer;
    const isCorrect = a?.isCorrect;
    const div = document.createElement('div');
    div.className = `review-item ${isCorrect ? 'review-correct' : 'review-wrong'}`;
    div.innerHTML = `
      <div class="review-q">${i + 1}. ${qq.question}</div>
      <div class="review-answer">
        ${a
          ? (isCorrect
            ? `<span class="your-ans">✅ ${a.selected}</span>`
            : `<span class="your-ans">❌ ${a.selected}</span> → <strong>✅ ${a.correct}</strong>`)
          : `<span style="color:var(--text-muted)">Answer: <strong>${qq.correct_answer}</strong></span>`
        }
      </div>
    `;
    detailReview.appendChild(div);
  });
  renderMath(detailReview);

  quizDetailModal.classList.remove('hidden');
}

function closeDetailModal() {
  quizDetailModal.classList.add('hidden');
  _currentDetailId = null;
}

detailCloseBtn.addEventListener('click', closeDetailModal);
detailCloseBtn2.addEventListener('click', closeDetailModal);

detailDeleteBtn.addEventListener('click', () => {
  if (_currentDetailId && confirm('Delete this saved quiz?')) {
    deleteQuizFromStorage(_currentDetailId);
    closeDetailModal();
    renderHistory();
  }
});

// ── Boot ──
(async function init() {
  initChips();
  await initCategories();
  await fetchSessionToken();
})();
