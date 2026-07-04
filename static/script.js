/**
 * script.js
 * ----------
 * Frontend logic for the Health Risk Tracker.
 * Talks to the FastAPI backend via fetch() for all CRUD operations:
 *   POST   /api/patients                  - create patient + first reading
 *   GET    /api/patients                  - list all patients
 *   PUT    /api/patients/{id}             - update patient details
 *   DELETE /api/patients/{id}             - delete patient (+ their records)
 *   POST   /api/patients/{id}/records     - add a new reading
 *   GET    /api/patients/{id}/records     - get reading history
 *   DELETE /api/records/{id}              - delete a single reading
 */

const API = {
  patients: '/api/patients',
  patient: (id) => `/api/patients/${id}`,
  records: (patientId) => `/api/patients/${patientId}/records`,
  deleteRecord: (recordId) => `/api/records/${recordId}`,
};

let currentPatientId = null;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function $(selector) { return document.querySelector(selector); }
function $all(selector) { return document.querySelectorAll(selector); }

function formatDate(isoString) {
  const d = new Date(isoString);
  return d.toLocaleString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  });
}

function clearFieldErrors(form) {
  form.querySelectorAll('.field__error').forEach(el => el.textContent = '');
}

function showFieldErrors(form, detailList) {
  // FastAPI/Pydantic validation errors come back as a list of
  // {loc: [...], msg: "..."} objects.
  clearFieldErrors(form);
  if (!Array.isArray(detailList)) return;
  detailList.forEach(err => {
    const field = err.loc?.[err.loc.length - 1];
    const el = form.querySelector(`[data-error-for="${field}"]`);
    if (el) el.textContent = err.msg;
  });
}

async function apiRequest(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    let detail = 'Something went wrong. Please try again.';
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) { /* ignore parse errors */ }
    const error = new Error(typeof detail === 'string' ? detail : 'Validation error');
    error.status = res.status;
    error.detail = detail;
    throw error;
  }

  if (res.status === 204) return null;
  return res.json();
}

// ---------------------------------------------------------------------------
// Gauge rendering (signature visual element)
// ---------------------------------------------------------------------------

function positionGauge(markerEl, riskLevel, probabilities) {
  // Map risk level + its own confidence into a 0-100% position within
  // that level's third of the gauge, so the marker reflects both the
  // category AND how strongly the model leans toward it.
  const zoneIndex = { Low: 0, Moderate: 1, High: 2 }[riskLevel] ?? 0;
  const confidence = probabilities ? probabilities[riskLevel] ?? 0.5 : 0.5;
  const zoneWidth = 100 / 3;
  const positionWithinZone = confidence * zoneWidth * 0.8 + zoneWidth * 0.1;
  const leftPercent = zoneIndex * zoneWidth + positionWithinZone;
  markerEl.style.left = `calc(${leftPercent}% - 2px)`;
}

function renderRiskCard(prediction) {
  const { risk_level, risk_confidence, probabilities } = prediction;

  $('#result-empty').hidden = true;
  $('#result-content').hidden = false;

  const badge = $('#risk-badge');
  badge.textContent = `${risk_level} risk`;
  badge.dataset.level = risk_level;

  $('#risk-confidence').textContent = `${Math.round(risk_confidence * 100)}% confidence`;

  positionGauge($('#gauge-marker'), risk_level, probabilities);

  const breakdown = $('#risk-breakdown');
  breakdown.innerHTML = '';
  ['Low', 'Moderate', 'High'].forEach(level => {
    const pct = probabilities && probabilities[level] != null
      ? Math.round(probabilities[level] * 100) : 0;
    const wrap = document.createElement('div');
    wrap.innerHTML = `<dt>${level}</dt><dd>${pct}%</dd>`;
    breakdown.appendChild(wrap);
  });
}

function renderHistory(patientName, records) {
  $('#history-name').textContent = patientName;
  const list = $('#history-list');
  list.innerHTML = '';

  if (!records.length) {
    const li = document.createElement('li');
    li.className = 'history__item';
    li.textContent = 'No previous readings.';
    list.appendChild(li);
    return;
  }

  records.forEach(rec => {
    const li = document.createElement('li');
    li.className = 'history__item';
    li.innerHTML = `
      <span>G ${rec.glucose} · Hb ${rec.haemoglobin} · Chol ${rec.cholesterol}</span>
      <span class="tag" data-level="${rec.risk_level}">${rec.risk_level}</span>
      <time>${formatDate(rec.recorded_at)}</time>
    `;
    list.appendChild(li);
  });
}

// ---------------------------------------------------------------------------
// Main form: create patient + first reading
// ---------------------------------------------------------------------------

const patientForm = $('#patient-form');
const submitBtn = $('#submit-btn');
const formStatus = $('#form-status');

patientForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearFieldErrors(patientForm);
  formStatus.textContent = '';
  formStatus.removeAttribute('data-state');
  submitBtn.disabled = true;
  submitBtn.querySelector('.btn__label').textContent = 'Predicting…';

  const payload = {
    name: $('#name').value,
    dob: $('#dob').value,
    email: $('#email').value,
    glucose: parseFloat($('#glucose').value),
    haemoglobin: parseFloat($('#haemoglobin').value),
    cholesterol: parseFloat($('#cholesterol').value),
  };

  try {
    const patient = await apiRequest(API.patients, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    currentPatientId = patient.id;
    renderRiskCard({
      risk_level: patient.records[0].risk_level,
      risk_confidence: patient.records[0].risk_confidence,
      probabilities: null, // not stored on the record; full breakdown only on /predict
    });

    // Get a full probability breakdown via the standalone predict endpoint
    // (keeps the DB record lean while still giving a rich UI result).
    const fullPrediction = await apiRequest('/api/predict', {
      method: 'POST',
      body: JSON.stringify({
        glucose: payload.glucose,
        haemoglobin: payload.haemoglobin,
        cholesterol: payload.cholesterol,
      }),
    });
    renderRiskCard(fullPrediction);

    renderHistory(patient.name, patient.records);

    formStatus.textContent = `Saved. ${patient.name}'s risk: ${fullPrediction.risk_level}.`;
    formStatus.dataset.state = 'success';

    patientForm.reset();
    await loadPatients();
  } catch (err) {
    if (err.status === 422 && Array.isArray(err.detail)) {
      showFieldErrors(patientForm, err.detail);
      formStatus.textContent = 'Please fix the highlighted fields.';
    } else {
      formStatus.textContent = err.message;
    }
    formStatus.dataset.state = 'error';
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector('.btn__label').textContent = 'Save & predict risk';
  }
});

// ---------------------------------------------------------------------------
// People table (list / view / edit / delete / add reading)
// ---------------------------------------------------------------------------

async function loadPatients() {
  const tbody = $('#people-tbody');
  try {
    const patients = await apiRequest(API.patients);

    if (!patients.length) {
      tbody.innerHTML = `<tr class="people-table__empty"><td colspan="6">No records yet — add your first reading above.</td></tr>`;
      return;
    }

    tbody.innerHTML = '';
    patients.forEach(p => {
      const latest = p.records[0]; // records are ordered desc by recorded_at
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${escapeHtml(p.name)}</td>
        <td>${escapeHtml(p.email)}</td>
        <td>${p.dob}</td>
        <td>${latest ? `<span class="tag" data-level="${latest.risk_level}">${latest.risk_level}</span>` : '—'}</td>
        <td>${latest ? formatDate(latest.recorded_at) : '—'}</td>
        <td class="row-actions">
          <button class="btn btn--ghost btn--small" data-action="view" data-id="${p.id}">View</button>
          <button class="btn btn--ghost btn--small" data-action="add-reading" data-id="${p.id}">+ Reading</button>
          <button class="btn btn--ghost btn--small" data-action="edit" data-id="${p.id}">Edit</button>
          <button class="btn btn--danger btn--small" data-action="delete" data-id="${p.id}">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr class="people-table__empty"><td colspan="6">Could not load people: ${escapeHtml(err.message)}</td></tr>`;
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

$('#refresh-btn').addEventListener('click', loadPatients);

$('#people-tbody').addEventListener('click', async (e) => {
  const btn = e.target.closest('button[data-action]');
  if (!btn) return;
  const id = parseInt(btn.dataset.id, 10);
  const action = btn.dataset.action;

  if (action === 'view') return viewPatient(id);
  if (action === 'edit') return openEditDialog(id);
  if (action === 'add-reading') return openReadingDialog(id);
  if (action === 'delete') return deletePatient(id);
});

async function viewPatient(id) {
  try {
    const patient = await apiRequest(API.patient(id));
    currentPatientId = patient.id;

    if (patient.records.length) {
      const latest = patient.records[0];
      const fullPrediction = await apiRequest('/api/predict', {
        method: 'POST',
        body: JSON.stringify({
          glucose: latest.glucose,
          haemoglobin: latest.haemoglobin,
          cholesterol: latest.cholesterol,
        }),
      });
      renderRiskCard(fullPrediction);
    }
    renderHistory(patient.name, patient.records);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (err) {
    alert(`Could not load patient: ${err.message}`);
  }
}

async function deletePatient(id) {
  if (!confirm('Delete this person and all their readings? This cannot be undone.')) return;
  try {
    await apiRequest(API.patient(id), { method: 'DELETE' });
    if (currentPatientId === id) {
      currentPatientId = null;
      $('#result-content').hidden = true;
      $('#result-empty').hidden = false;
    }
    await loadPatients();
  } catch (err) {
    alert(`Could not delete: ${err.message}`);
  }
}

// ---------------- Edit dialog ----------------

const editDialog = $('#edit-dialog');
const editForm = $('#edit-form');
let editingPatientId = null;

async function openEditDialog(id) {
  try {
    const patient = await apiRequest(API.patient(id));
    editingPatientId = id;
    $('#edit-name').value = patient.name;
    $('#edit-dob').value = patient.dob;
    $('#edit-email').value = patient.email;
    $('#edit-error').textContent = '';
    editDialog.showModal();
  } catch (err) {
    alert(`Could not load patient: ${err.message}`);
  }
}

$('#edit-cancel').addEventListener('click', () => editDialog.close());

editForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  $('#edit-error').textContent = '';
  try {
    await apiRequest(API.patient(editingPatientId), {
      method: 'PUT',
      body: JSON.stringify({
        name: $('#edit-name').value,
        dob: $('#edit-dob').value,
        email: $('#edit-email').value,
      }),
    });
    editDialog.close();
    await loadPatients();
  } catch (err) {
    $('#edit-error').textContent = err.message;
  }
});

// ---------------- Add reading dialog ----------------

const readingDialog = $('#reading-dialog');
const readingForm = $('#reading-form');
let readingPatientId = null;

async function openReadingDialog(id) {
  try {
    const patient = await apiRequest(API.patient(id));
    readingPatientId = id;
    $('#reading-dialog-name').textContent = patient.name;
    $('#reading-glucose').value = '';
    $('#reading-haemoglobin').value = '';
    $('#reading-cholesterol').value = '';
    $('#reading-error').textContent = '';
    readingDialog.showModal();
  } catch (err) {
    alert(`Could not load patient: ${err.message}`);
  }
}

$('#reading-cancel').addEventListener('click', () => readingDialog.close());

readingForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  $('#reading-error').textContent = '';
  try {
    await apiRequest(API.records(readingPatientId), {
      method: 'POST',
      body: JSON.stringify({
        glucose: parseFloat($('#reading-glucose').value),
        haemoglobin: parseFloat($('#reading-haemoglobin').value),
        cholesterol: parseFloat($('#reading-cholesterol').value),
      }),
    });
    readingDialog.close();
    await loadPatients();
    if (currentPatientId === readingPatientId) {
      await viewPatient(readingPatientId);
    }
  } catch (err) {
    $('#reading-error').textContent = err.message;
  }
});

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

loadPatients();
