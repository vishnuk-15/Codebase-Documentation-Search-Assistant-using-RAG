const form = document.getElementById('askForm');
const input = document.getElementById('questionInput');
const askBtn = document.getElementById('askBtn');

const emptyState = document.getElementById('emptyState');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const errorText = document.getElementById('errorText');
const resultArea = document.getElementById('resultArea');

const answerText = document.getElementById('answerText');
const confidencePill = document.getElementById('confidencePill');
const latencyPill = document.getElementById('latencyPill');
const sourcesList = document.getElementById('sourcesList');
const sourcesCount = document.getElementById('sourcesCount');

function showState(state) {
  emptyState.hidden = state !== 'empty';
  loadingState.hidden = state !== 'loading';
  errorState.hidden = state !== 'error';
  resultArea.hidden = state !== 'result';
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function highlightSnippet(snippet, spanAnswer) {
  const escaped = escapeHtml(snippet);
  if (!spanAnswer || spanAnswer.length < 2) return escaped;
  const escapedSpan = escapeHtml(spanAnswer);
  const idx = escaped.toLowerCase().indexOf(escapedSpan.toLowerCase());
  if (idx === -1) return escaped;
  return escaped.slice(0, idx) + '<mark>' + escaped.slice(idx, idx + escapedSpan.length) + '</mark>' + escaped.slice(idx + escapedSpan.length);
}

function badgeLabel(matchedVia) {
  if (matchedVia === 'both') return 'semantic + keyword';
  return matchedVia;
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('statDocs').textContent = data.documents;
    document.getElementById('statChunks').textContent = data.chunks;
  } catch (e) {
    // stats are non-critical, fail silently
  }
}

async function runQuery(question) {
  showState('loading');
  askBtn.disabled = true;

  try {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    if (!res.ok) {
      if (res.status === 503) {
        throw new Error('the models are still warming up — wait a few seconds and try again');
      }
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ? JSON.stringify(body.detail) : `Request failed (${res.status})`);
    }

    const data = await res.json();
    renderResult(data);
    showState('result');
  } catch (err) {
    errorText.textContent = 'Something went wrong: ' + err.message + '. The model may still be warming up on first load — try again in a few seconds.';
    showState('error');
  } finally {
    askBtn.disabled = false;
  }
}

function renderResult(data) {
  answerText.textContent = data.answer;
  confidencePill.textContent = `confidence ${(data.confidence * 100).toFixed(0)}%`;
  latencyPill.textContent = `${data.latency_ms} ms`;

  sourcesCount.textContent = `${data.sources.length} chunk${data.sources.length === 1 ? '' : 's'} retrieved`;
  sourcesList.innerHTML = '';

  data.sources.forEach((s) => {
    const card = document.createElement('div');
    card.className = 'source-card';

    const relevancePct = Math.round(s.relevance * 100);

    card.innerHTML = `
      <div class="source-file-row">
        <span class="source-file">
          <span class="path">${escapeHtml(s.file)}</span>
          <span class="heading-sep">›</span>
          <span>${escapeHtml(s.heading)}</span>
        </span>
        <span class="match-badge ${s.matched_via}">
          <span class="dot"></span>${badgeLabel(s.matched_via)}
        </span>
      </div>
      <div class="source-snippet">${highlightSnippet(s.snippet, s.span_answer)}</div>
      <div class="source-footer">
        <span>relevance</span>
        <span class="relevance-bar"><span class="relevance-fill" style="width:${relevancePct}%"></span></span>
        <span>${relevancePct}%</span>
      </div>
    `;
    sourcesList.appendChild(card);
  });
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (q.length < 3) return;
  runQuery(q);
});

document.querySelectorAll('.chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    const q = chip.dataset.q;
    input.value = q;
    runQuery(q);
  });
});

loadStats();
