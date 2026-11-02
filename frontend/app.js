/**
 * AERIS-RAG — Research Demonstration Dashboard Client
 * Handles real-time API communication, evidence visualization, and telemetry.
 */

// State
const state = {
  activeDocumentId: 'test_document',
  documents: [],
  sampleQueries: [],
  currentResult: null,
  activeEvidenceFilter: 'cited', // 'cited' or 'all'
  timerInterval: null,
  timerSeconds: 0,
};

// DOM Elements
const elements = {
  backendStatusPill: document.getElementById('backendStatusPill'),
  backendStatusText: document.getElementById('backendStatusText'),
  modelNameText: document.getElementById('modelNameText'),
  activeDocText: document.getElementById('activeDocText'),
  documentSelect: document.getElementById('documentSelect'),
  docMetadataBox: document.getElementById('docMetadataBox'),
  sampleButtons: document.getElementById('sampleButtons'),
  questionInput: document.getElementById('questionInput'),
  charCount: document.getElementById('charCount'),
  clearBtn: document.getElementById('clearBtn'),
  submitBtn: document.getElementById('submitBtn'),
  btnSpinner: document.getElementById('btnSpinner'),
  btnText: document.getElementById('btnText'),
  timerDisplay: document.getElementById('timerDisplay'),
  loadingState: document.getElementById('loadingState'),
  errorCard: document.getElementById('errorCard'),
  errorMessage: document.getElementById('errorMessage'),
  answerCard: document.getElementById('answerCard'),
  answerStatusBadge: document.getElementById('answerStatusBadge'),
  confidenceBadge: document.getElementById('confidenceBadge'),
  execDurationBadge: document.getElementById('execDurationBadge'),
  answerText: document.getElementById('answerText'),
  insufficiencyBox: document.getElementById('insufficiencyBox'),
  insufficiencyText: document.getElementById('insufficiencyText'),
  downgradeBox: document.getElementById('downgradeBox'),
  downgradeReasonsList: document.getElementById('downgradeReasonsList'),
  citationsPills: document.getElementById('citationsPills'),
  tabBtnEvidence: document.getElementById('tabBtnEvidence'),
  tabBtnRequirements: document.getElementById('tabBtnRequirements'),
  tabBtnTelemetry: document.getElementById('tabBtnTelemetry'),
  evidenceTab: document.getElementById('evidenceTab'),
  requirementsTab: document.getElementById('requirementsTab'),
  telemetryTab: document.getElementById('telemetryTab'),
  evidenceList: document.getElementById('evidenceList'),
  evidenceCountBadge: document.getElementById('evidenceCountBadge'),
  citedCountText: document.getElementById('citedCountText'),
  allCandidateCountText: document.getElementById('allCandidateCountText'),
  filterCitedOnly: document.getElementById('filterCitedOnly'),
  filterAllCandidates: document.getElementById('filterAllCandidates'),
  reqBadge: document.getElementById('reqBadge'),
  requirementsContent: document.getElementById('requirementsContent'),
  telemetryBadge: document.getElementById('telemetryBadge'),
  telemetryTotalTime: document.getElementById('telemetryTotalTime'),
  telemetryContent: document.getElementById('telemetryContent'),
  footerDoc: document.getElementById('footerDoc'),
  toggleUploadBtn: document.getElementById('toggleUploadBtn'),
  uploadDrawer: document.getElementById('uploadDrawer'),
  uploadDropZone: document.getElementById('uploadDropZone'),
  pdfFileInput: document.getElementById('pdfFileInput'),
  browseFileBtn: document.getElementById('browseFileBtn'),
  selectedFileInfo: document.getElementById('selectedFileInfo'),
  selectedFileName: document.getElementById('selectedFileName'),
  indexDocBtn: document.getElementById('indexDocBtn'),
  indexSpinner: document.getElementById('indexSpinner'),
  indexBtnText: document.getElementById('indexBtnText'),
  uploadStatusBox: document.getElementById('uploadStatusBox'),
};

// --------------------------------------------------------------------------
// Initialization
// --------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  checkHealth();
  loadDocuments();
  loadSampleQueries();
  setInterval(checkHealth, 10000); // Heartbeat every 10s
});

function setupEventListeners() {
  // Input character counter
  elements.questionInput.addEventListener('input', () => {
    const len = elements.questionInput.value.length;
    elements.charCount.textContent = len;
  });

  // Clear button
  elements.clearBtn.addEventListener('click', () => {
    elements.questionInput.value = '';
    elements.charCount.textContent = '0';
    document.querySelectorAll('.sample-btn').forEach(btn => btn.classList.remove('active'));
    elements.questionInput.focus();
  });

  // Submit button
  elements.submitBtn.addEventListener('click', () => {
    submitQuery();
  });

  // Keyboard shortcut Ctrl+Enter to submit
  elements.questionInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      submitQuery();
    }
  });

  // Document select change
  elements.documentSelect.addEventListener('change', (e) => {
    state.activeDocumentId = e.target.value;
    elements.activeDocText.textContent = state.activeDocumentId;
    elements.footerDoc.textContent = state.activeDocumentId;
    updateDocMetadata();
  });

  // Tab switching
  [elements.tabBtnEvidence, elements.tabBtnRequirements, elements.tabBtnTelemetry].forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTabId = btn.getAttribute('data-tab');
      switchTab(targetTabId);
    });
  });

  // Evidence filter buttons
  elements.filterCitedOnly.addEventListener('click', () => {
    state.activeEvidenceFilter = 'cited';
    elements.filterCitedOnly.classList.add('active');
    elements.filterAllCandidates.classList.remove('active');
    renderEvidenceList();
  });

  elements.filterAllCandidates.addEventListener('click', () => {
    state.activeEvidenceFilter = 'all';
    elements.filterAllCandidates.classList.add('active');
    elements.filterCitedOnly.classList.remove('active');
    renderEvidenceList();
  });

  // Toggle upload drawer
  elements.toggleUploadBtn.addEventListener('click', () => {
    const isVisible = elements.uploadDrawer.style.display !== 'none';
    elements.uploadDrawer.style.display = isVisible ? 'none' : 'flex';
    elements.toggleUploadBtn.innerHTML = isVisible ? '<span>+ Upload PDF</span>' : '<span>&times; Close</span>';
    if (!isVisible) resetUploadUI();
  });

  // Browse file button
  elements.browseFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    elements.pdfFileInput.click();
  });

  elements.uploadDropZone.addEventListener('click', () => {
    elements.pdfFileInput.click();
  });

  // Drag and drop handlers
  elements.uploadDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
  });

  elements.uploadDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  elements.pdfFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  // Index document button
  elements.indexDocBtn.addEventListener('click', () => {
    uploadAndIndexDocument();
  });
}

// --------------------------------------------------------------------------
// Document Upload & Ingestion Logic
// --------------------------------------------------------------------------

let selectedUploadFile = null;

function handleFileSelected(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    setUploadStatus('Please select a valid PDF (.pdf) file.', 'error');
    return;
  }
  selectedUploadFile = file;
  elements.selectedFileName.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
  elements.selectedFileInfo.style.display = 'flex';
  elements.uploadDropZone.style.display = 'none';
  elements.uploadStatusBox.style.display = 'none';
}

function resetUploadUI() {
  selectedUploadFile = null;
  elements.pdfFileInput.value = '';
  elements.selectedFileInfo.style.display = 'none';
  elements.uploadDropZone.style.display = 'flex';
  elements.uploadStatusBox.style.display = 'none';
  elements.indexDocBtn.disabled = false;
  elements.indexSpinner.style.display = 'none';
  elements.indexBtnText.textContent = 'Build Index';
}

function setUploadStatus(msg, type) {
  elements.uploadStatusBox.style.display = 'block';
  elements.uploadStatusBox.className = `upload-status-box status-${type}`;
  elements.uploadStatusBox.textContent = msg;
}

async function uploadAndIndexDocument() {
  if (!selectedUploadFile) return;

  elements.indexDocBtn.disabled = true;
  elements.indexSpinner.style.display = 'inline-block';
  elements.indexBtnText.textContent = 'Indexing...';
  setUploadStatus('Extracting text & building dense index with nomic-embed-text. This may take 20–45s...', 'indexing');

  const formData = new FormData();
  formData.append('file', selectedUploadFile);

  try {
    const res = await fetch('/api/upload_document', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Upload failed (HTTP ${res.status})`);
    }

    setUploadStatus(`Index built successfully! Document '${data.document_id}' ready (${data.total_chunks} chunks).`, 'success');
    await loadDocuments();

    // Automatically select newly indexed document
    if (elements.documentSelect) {
      elements.documentSelect.value = data.document_id;
      state.activeDocumentId = data.document_id;
      elements.activeDocText.textContent = data.document_id;
      elements.footerDoc.textContent = data.document_id;
      updateDocMetadata();
    }

    setTimeout(() => {
      elements.uploadDrawer.style.display = 'none';
      elements.toggleUploadBtn.innerHTML = '<span>+ Upload PDF</span>';
      resetUploadUI();
    }, 2500);

  } catch (err) {
    console.error('Document upload error:', err);
    setUploadStatus(`Indexing error: ${err.message}`, 'error');
    elements.indexDocBtn.disabled = false;
    elements.indexSpinner.style.display = 'none';
    elements.indexBtnText.textContent = 'Retry Build Index';
  }
}

function switchTab(targetTabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

  const activeBtn = document.querySelector(`.tab-btn[data-tab="${targetTabId}"]`);
  const activeContent = document.getElementById(targetTabId);

  if (activeBtn) activeBtn.classList.add('active');
  if (activeContent) activeContent.classList.add('active');
}

// --------------------------------------------------------------------------
// Health & Environment Polling
// --------------------------------------------------------------------------

async function checkHealth() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.controller_initialized && data.ollama.ollama_running) {
      elements.backendStatusPill.className = 'status-pill status-ready';
      elements.backendStatusText.textContent = 'Controller Ready';
      elements.backendStatusPill.title = `Controller initialized in ${Number(data.controller_init_time_seconds || 0).toFixed(1)}s`;
    } else if (!data.controller_initialized) {
      elements.backendStatusPill.className = 'status-pill status-degraded';
      elements.backendStatusText.textContent = 'Controller Initializing...';
      elements.backendStatusPill.title = data.controller_init_error || 'Loading controller weights...';
    } else {
      elements.backendStatusPill.className = 'status-pill status-degraded';
      elements.backendStatusText.textContent = 'Ollama Degraded';
      elements.backendStatusPill.title = data.ollama.error || 'Ollama unavailable';
    }

    if (data.ollama.generation_model) {
      elements.modelNameText.textContent = data.ollama.generation_model.replace(':latest', '');
    }
  } catch (err) {
    elements.backendStatusPill.className = 'status-pill status-connecting';
    elements.backendStatusText.textContent = 'Offline / Connecting';
    elements.backendStatusPill.title = err.message;
  }
}

// --------------------------------------------------------------------------
// Document Loading
// --------------------------------------------------------------------------

async function loadDocuments() {
  try {
    const res = await fetch('/api/documents');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const docs = await res.json();
    state.documents = docs;

    elements.documentSelect.innerHTML = '';
    docs.forEach(doc => {
      const opt = document.createElement('option');
      opt.value = doc.document_id;
      opt.textContent = `${doc.document_id} — ${doc.title}`;
      elements.documentSelect.appendChild(opt);
    });

    if (docs.length > 0) {
      state.activeDocumentId = docs[0].document_id;
      elements.activeDocText.textContent = state.activeDocumentId;
      elements.footerDoc.textContent = state.activeDocumentId;
      updateDocMetadata();
    }
  } catch (err) {
    console.error('Failed to load documents:', err);
    elements.docMetadataBox.innerHTML = `<span class="meta-tag">Failed to load document metadata.</span>`;
  }
}

function updateDocMetadata() {
  const doc = state.documents.find(d => d.document_id === state.activeDocumentId);
  if (!doc) return;

  elements.docMetadataBox.innerHTML = `
    <span class="meta-tag"><strong>Chunks:</strong> ${doc.chunk_count}</span>
    <span class="meta-tag"><strong>Pages:</strong> ${doc.total_pages}</span>
    <span class="meta-tag"><strong>Embedding:</strong> ${doc.embedding_model.replace(':latest', '')}</span>
    <span class="meta-tag"><strong>Status:</strong> ${doc.status}</span>
  `;
}

// --------------------------------------------------------------------------
// Sample Presets Loading
// --------------------------------------------------------------------------

async function loadSampleQueries() {
  try {
    const res = await fetch('/api/sample_queries');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const queries = await res.json();
    state.sampleQueries = queries;

    elements.sampleButtons.innerHTML = '';
    queries.forEach((sample, idx) => {
      const btn = document.createElement('button');
      btn.className = 'sample-btn';
      btn.title = `${sample.description} (Expected: ${sample.expected_status})`;

      let catClass = 'cat-fact';
      if (sample.category.includes('Comparative')) catClass = 'cat-comparative';
      else if (sample.category.includes('Conservative') || sample.category.includes('Unanswerable')) catClass = 'cat-refusal';
      else if (sample.category.includes('Method') || sample.category.includes('Partial')) catClass = 'cat-method';

      btn.innerHTML = `
        <span class="sample-category-tag ${catClass}">${sample.category.split('/')[0].trim()}</span>
        <span>${escapeHtml(sample.question)}</span>
      `;

      btn.addEventListener('click', () => {
        document.querySelectorAll('.sample-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        elements.questionInput.value = sample.question;
        elements.charCount.textContent = sample.question.length;
        elements.questionInput.focus();
      });

      elements.sampleButtons.appendChild(btn);
    });
  } catch (err) {
    console.error('Failed to load sample queries:', err);
    elements.sampleButtons.innerHTML = `<span class="meta-tag">Could not load sample queries.</span>`;
  }
}

// --------------------------------------------------------------------------
// Query Submission & Pipeline Execution
// --------------------------------------------------------------------------

async function submitQuery() {
  const question = elements.questionInput.value.trim();
  if (question.length < 3) {
    showError('Please enter a question with at least 3 characters.');
    return;
  }

  // Set UI loading state
  setExecutionState(true);
  hideError();
  elements.answerCard.style.display = 'none';

  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: state.activeDocumentId,
        question: question,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      const errDetail = data.detail || `Server error (HTTP ${res.status})`;
      throw new Error(errDetail);
    }

    if (data.answer_status === 'FAILED' || data.error) {
      showError(data.error || 'Pipeline execution failed without result.');
      setExecutionState(false);
      return;
    }

    // Success: store result and render
    state.currentResult = data;
    renderQueryResult(data);
    setExecutionState(false);
  } catch (err) {
    console.error('Query execution error:', err);
    showError(err.message || 'Network error occurred while calling the AERIS API.');
    setExecutionState(false);
  }
}

function setExecutionState(isExecuting) {
  if (isExecuting) {
    elements.submitBtn.disabled = true;
    elements.btnSpinner.style.display = 'inline-block';
    elements.btnText.textContent = 'Processing Pipeline...';
    elements.loadingState.style.display = 'flex';
    elements.timerDisplay.style.display = 'inline-block';

    // Start stopwatch timer
    state.timerSeconds = 0;
    elements.timerDisplay.textContent = '00:00';
    clearInterval(state.timerInterval);
    state.timerInterval = setInterval(() => {
      state.timerSeconds++;
      const mins = String(Math.floor(state.timerSeconds / 60)).padStart(2, '0');
      const secs = String(state.timerSeconds % 60).padStart(2, '0');
      elements.timerDisplay.textContent = `${mins}:${secs}`;
    }, 1000);
  } else {
    elements.submitBtn.disabled = false;
    elements.btnSpinner.style.display = 'none';
    elements.btnText.textContent = 'Execute AERIS Pipeline';
    elements.loadingState.style.display = 'none';
    clearInterval(state.timerInterval);
  }
}

function showError(msg) {
  elements.errorCard.style.display = 'block';
  elements.errorMessage.textContent = msg;
}

function hideError() {
  elements.errorCard.style.display = 'none';
}

// --------------------------------------------------------------------------
// Result Rendering
// --------------------------------------------------------------------------

function renderQueryResult(result) {
  elements.answerCard.style.display = 'block';

  // 1. Status Badge
  const status = result.answer_status || 'UNKNOWN';
  elements.answerStatusBadge.textContent = status.replace('_', ' ');
  elements.answerCard.className = 'card answer-card';

  if (status === 'SUPPORTED') {
    elements.answerStatusBadge.className = 'badge badge-supported';
    elements.answerCard.classList.add('status-supported');
  } else if (status === 'PARTIALLY_SUPPORTED') {
    elements.answerStatusBadge.className = 'badge badge-partial';
    elements.answerCard.classList.add('status-partial');
  } else if (status === 'INSUFFICIENT_EVIDENCE') {
    elements.answerStatusBadge.className = 'badge badge-insufficient';
    elements.answerCard.classList.add('status-insufficient');
  } else if (status === 'CONFLICTED') {
    elements.answerStatusBadge.className = 'badge badge-conflicted';
    elements.answerCard.classList.add('status-conflicted');
  } else {
    elements.answerStatusBadge.className = 'badge badge-failed';
    elements.answerCard.classList.add('status-failed');
  }

  // 2. Confidence & Execution Duration
  if (result.answer_confidence !== null && result.answer_confidence !== undefined) {
    elements.confidenceBadge.style.display = 'inline-block';
    elements.confidenceBadge.textContent = `Confidence: ${(result.answer_confidence * 100).toFixed(0)}%`;
  } else {
    elements.confidenceBadge.style.display = 'none';
  }

  elements.execDurationBadge.textContent = `${Number(result.total_execution_seconds || 0).toFixed(1)}s`;

  // 3. Render Answer with Clickable Citations
  renderAnswerWithCitations(result.final_answer || 'No answer text generated.', result.citations);

  // 4. Insufficiency Callout
  if (result.insufficiency_information && status === 'INSUFFICIENT_EVIDENCE') {
    elements.insufficiencyBox.style.display = 'block';
    elements.insufficiencyText.textContent = result.insufficiency_information;
  } else {
    elements.insufficiencyBox.style.display = 'none';
  }

  // 5. Downgrade Callout
  if (result.downgrade_reasons && result.downgrade_reasons.length > 0 && status === 'PARTIALLY_SUPPORTED') {
    elements.downgradeBox.style.display = 'block';
    elements.downgradeReasonsList.innerHTML = '';
    result.downgrade_reasons.forEach(r => {
      const li = document.createElement('li');
      li.textContent = r;
      elements.downgradeReasonsList.appendChild(li);
    });
  } else {
    elements.downgradeBox.style.display = 'none';
  }

  // 6. Citations Strip
  renderCitationsStrip(result.citations);

  // 7. Populate Tabs
  renderEvidenceList();
  renderRequirementsTab(result);
  renderTelemetryTab(result);
}

function renderAnswerWithCitations(rawAnswer, citations) {
  // Regex to detect [chunk_id] or [p.X, chunk_id] or chunk ID tokens in answer
  // We replace chunk references with interactive clickable citation pills
  let formatted = escapeHtml(rawAnswer);

  citations.forEach(c => {
    const chunkId = c.chunk_id;
    const pageNum = (c.pages && c.pages.length > 0) ? c.pages[0] : '?';
    const pillHtml = `<a class="citation-link" href="#chunk-${chunkId}" data-chunk-id="${chunkId}">[p.${pageNum}, ${chunkId}]</a>`;

    // Replace occurrences of chunkId
    const regex = new RegExp(`\\[?p?\\.?\\s*${chunkId}\\]?`, 'g');
    formatted = formatted.replace(regex, pillHtml);
  });

  elements.answerText.innerHTML = formatted;

  // Add click listeners to citation links
  elements.answerText.querySelectorAll('.citation-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetChunkId = link.getAttribute('data-chunk-id');
      jumpToEvidenceChunk(targetChunkId);
    });
  });
}

function renderCitationsStrip(citations) {
  elements.citationsPills.innerHTML = '';
  if (!citations || citations.length === 0) {
    elements.citationsPills.innerHTML = `<span class="no-citations-text">No evidence chunks cited for this answer.</span>`;
    return;
  }

  citations.forEach(c => {
    const btn = document.createElement('button');
    btn.className = 'citation-pill-btn';
    const pageNum = (c.pages && c.pages.length > 0) ? c.pages[0] : '?';
    btn.innerHTML = `&#x1F4C4; p.${pageNum} &bull; ${c.chunk_id}`;
    btn.addEventListener('click', () => {
      jumpToEvidenceChunk(c.chunk_id);
    });
    elements.citationsPills.appendChild(btn);
  });
}

// --------------------------------------------------------------------------
// Tab 1: Evidence Inspector
// --------------------------------------------------------------------------

function renderEvidenceList() {
  if (!state.currentResult) return;

  const citations = state.currentResult.citations || [];
  const allRetrieved = state.currentResult.retrieved_evidence || [];

  // Update counts
  elements.evidenceCountBadge.textContent = citations.length;
  elements.citedCountText.textContent = citations.length;
  elements.allCandidateCountText.textContent = allRetrieved.length;

  const itemsToRender = (state.activeEvidenceFilter === 'cited') ? citations : allRetrieved;

  if (itemsToRender.length === 0) {
    elements.evidenceList.innerHTML = `
      <div class="empty-tab-state">
        <span class="empty-icon">&#x1F4D6;</span>
        <p>No ${state.activeEvidenceFilter === 'cited' ? 'cited' : 'retrieved'} evidence passages to display.</p>
      </div>
    `;
    return;
  }

  elements.evidenceList.innerHTML = '';

  itemsToRender.forEach(item => {
    const isCited = item.is_cited !== undefined ? item.is_cited : true;
    const pageStr = (item.pages && item.pages.length > 0) ? item.pages.join(', ') : '1';
    const isDefect = item.provenance_valid === false;

    const card = document.createElement('div');
    card.className = `evidence-card ${isCited ? 'is-cited' : ''}`;
    card.id = `chunk-card-${item.chunk_id}`;

    card.innerHTML = `
      <div class="evidence-header">
        <div class="evidence-id-group">
          <span class="chunk-id-tag">${item.chunk_id}</span>
          <span class="page-badge">Page ${pageStr}</span>
        </div>
        <div class="evidence-badges">
          ${isCited ? '<span class="badge-cited">&#x2713; CITED PASSAGE</span>' : '<span class="badge-subtle">CANDIDATE POOL</span>'}
          ${isDefect ? '<span class="badge-defect">&#x26A0; PROVENANCE DEFECT</span>' : (isCited ? '<span class="badge-provenance-ok">VALID PROVENANCE</span>' : '')}
        </div>
      </div>
      <div class="evidence-body">
        <p>${escapeHtml(item.text || 'No text snippet available in index.')}</p>
      </div>
    `;

    elements.evidenceList.appendChild(card);
  });
}

function jumpToEvidenceChunk(chunkId) {
  // Ensure we switch to Evidence tab
  switchTab('evidenceTab');

  // If in 'cited' filter and chunk is not in cited, switch to 'all'
  const isCited = state.currentResult.citations.some(c => c.chunk_id === chunkId);
  if (!isCited && state.activeEvidenceFilter === 'cited') {
    state.activeEvidenceFilter = 'all';
    elements.filterAllCandidates.classList.add('active');
    elements.filterCitedOnly.classList.remove('active');
    renderEvidenceList();
  }

  setTimeout(() => {
    const card = document.getElementById(`chunk-card-${chunkId}`);
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      card.classList.remove('highlight-flash');
      // Force DOM reflow to restart animation
      void card.offsetWidth;
      card.classList.add('highlight-flash');
    }
  }, 100);
}

// --------------------------------------------------------------------------
// Tab 2: Requirement Support
// --------------------------------------------------------------------------

function renderRequirementsTab(result) {
  const downgradeDetails = result.downgrade_details || [];
  const downgradeReasons = result.downgrade_reasons || [];

  let totalReqs = 0;
  let supportedCount = 0;
  let unsupportedCount = 0;

  downgradeDetails.forEach(dd => {
    if (dd.total_requirements) totalReqs = dd.total_requirements;
    if (dd.supported_count) supportedCount = dd.supported_count;
    if (dd.unsupported_requirements) unsupportedCount = dd.unsupported_requirements.length;
  });

  if (totalReqs === 0 && result.answer_status === 'SUPPORTED') {
    totalReqs = 1;
    supportedCount = 1;
    unsupportedCount = 0;
  }

  elements.reqBadge.textContent = `${supportedCount}/${totalReqs}`;

  let html = `
    <div class="req-summary-row">
      <div class="req-stat-box">
        <div class="req-stat-val" style="color: #38bdf8;">${totalReqs}</div>
        <div class="req-stat-label">Total Requirements</div>
      </div>
      <div class="req-stat-box">
        <div class="req-stat-val" style="color: var(--color-supported);">${supportedCount}</div>
        <div class="req-stat-label">Satisfied by Evidence</div>
      </div>
      <div class="req-stat-box">
        <div class="req-stat-val" style="color: ${unsupportedCount > 0 ? 'var(--color-partial)' : 'var(--text-muted)'};">${unsupportedCount}</div>
        <div class="req-stat-label">Unsupported Sub-facets</div>
      </div>
    </div>
  `;

  if (downgradeReasons.length > 0) {
    html += `
      <div class="req-rationales-card">
        <h4 class="req-section-title">Support Evaluation Rationales &amp; Overrides</h4>
    `;
    downgradeReasons.forEach(r => {
      html += `<div class="rationale-item">${escapeHtml(r)}</div>`;
    });
    html += `</div>`;
  } else if (result.answer_status === 'SUPPORTED') {
    html += `
      <div class="req-rationales-card">
        <h4 class="req-section-title">Grounding Validation Summary</h4>
        <div class="rationale-item" style="border-left-color: var(--color-supported);">
          All decomposed information requirements were verified as fully entailed by retrieved citations without contradiction.
        </div>
      </div>
    `;
  } else {
    html += `
      <div class="req-rationales-card">
        <h4 class="req-section-title">Support Evaluation</h4>
        <div class="rationale-item" style="border-left-color: var(--color-insufficient);">
          ${escapeHtml(result.insufficiency_information || 'Evidence pool does not satisfy query requirements.')}
        </div>
      </div>
    `;
  }

  elements.requirementsContent.innerHTML = html;
}

// --------------------------------------------------------------------------
// Tab 3: Pipeline Telemetry
// --------------------------------------------------------------------------

function renderTelemetryTab(result) {
  const stages = result.stages || [];
  elements.telemetryBadge.textContent = stages.length;
  elements.telemetryTotalTime.textContent = `Total: ${Number(result.total_execution_seconds || 0).toFixed(1)}s`;

  if (stages.length === 0) {
    elements.telemetryContent.innerHTML = `
      <div class="empty-tab-state">
        <span class="empty-icon">&#x2699;</span>
        <p>No stage execution telemetry available.</p>
      </div>
    `;
    return;
  }

  // Find max latency to calculate relative bar widths
  const maxLatency = Math.max(...stages.map(s => s.latency_seconds || 0), 1.0);

  let html = '';

  stages.forEach(stg => {
    const lat = Number(stg.latency_seconds || 0);
    const pct = Math.min(100, Math.max(3, (lat / maxLatency) * 100));
    const stStatus = (stg.status || 'COMPLETED').toLowerCase();

    let statusClass = 'status-completed';
    if (stStatus === 'skipped') statusClass = 'status-skipped';
    if (stStatus === 'failed') statusClass = 'status-failed';

    html += `
      <div class="telemetry-stage-row">
        <div class="telemetry-row-header">
          <span class="stage-name">${escapeHtml(stg.stage)}</span>
          <div class="stage-metrics">
            <span class="stage-status-badge ${statusClass}">${escapeHtml(stg.status)}</span>
            <span class="stage-count">Out: ${stg.output_count}</span>
            <span class="stage-latency">${lat.toFixed(2)}s</span>
          </div>
        </div>
        <div class="stage-bar-track">
          <div class="stage-bar-fill" style="width: ${pct}%;"></div>
        </div>
        ${stg.message ? `<div class="stage-msg">${escapeHtml(stg.message)}</div>` : ''}
      </div>
    `;
  });

  elements.telemetryContent.innerHTML = html;
}

// --------------------------------------------------------------------------
// Helpers
// --------------------------------------------------------------------------

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
