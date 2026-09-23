const workspace = document.getElementById('practicalWorkspace');
const labTitle = document.getElementById('labExpTitle');
const labSubtitle = document.getElementById('labExpSubtitle');
const statusBadge = document.getElementById('practicalStatusBadge');
const navAuthBtn = document.getElementById('navAuthBtn');

let expData = null;
let currentStage = 1;
let completedSimSteps = {};
let observations = '';
let results = '';
let conclusion = '';
let wasteManagement = '';

// Auth check
api('/me').then(me => {
  if (navAuthBtn) {
    navAuthBtn.textContent = 'Dashboard';
    navAuthBtn.href = 'dashboard.html';
  }
}).catch(() => {});

function updateStepperUI(stage) {
  for (let i = 1; i <= 5; i++) {
    const pill = document.getElementById(`pill-${i}`);
    if (!pill) continue;
    pill.className = 'lab-step-pill';
    if (i === stage) {
      pill.classList.add('active');
    } else if (i < stage) {
      pill.classList.add('completed');
      pill.innerHTML = `✓ Stage ${i}`;
    }
  }
}

async function initPractical() {
  const params = new URLSearchParams(location.search);
  const expId = params.get('id') || 1;

  try {
    const res = await api(`/practicals/${expId}`);
    expData = res.practical;

    labTitle.textContent = `🔬 Practical: ${expData.name}`;
    labSubtitle.textContent = `${expData.category} • Difficulty: ${expData.difficulty} • Safety: ${expData.safety_level}`;

    renderStage(1);
  } catch (err) {
    workspace.innerHTML = `
      <div style="text-align:center;padding:30px">
        <h3 class="error">Error Loading Virtual Practical</h3>
        <p>${err.message || 'Could not load experiment data'}</p>
        <a class="btn secondary" href="experiments.html">Return to Experiments</a>
      </div>
    `;
  }
}

function renderStage(stage) {
  currentStage = stage;
  updateStepperUI(stage);

  if (stage === 1) renderPreLab();
  else if (stage === 2) renderSimulation();
  else if (stage === 3) renderObservations();
  else if (stage === 4) renderResultsAndWaste();
  else if (stage === 5) renderConclusion();
}

// --- STAGE 1: Pre-Lab & Safety Verification ---
function renderPreLab() {
  statusBadge.textContent = 'Stage 1: Pre-Lab Setup';
  statusBadge.className = 'badge teal';

  workspace.innerHTML = `
    <h2>Stage 1: Pre-Lab & Safety Verification</h2>
    <p class="muted">Review experimental aim, apparatus, and verify laboratory safety precautions before starting the simulation.</p>

    <div style="background:#f4fbf7;border-left:4px solid var(--green);padding:14px 18px;border-radius:6px;margin:18px 0">
      <b style="color:var(--dark)">🎯 Experiment Aim:</b> ${expData.aim || expData.description}
    </div>

    <div style="margin:20px 0">
      <h3>🌱 Green Chemistry Principles in Action</h3>
      <div style="display:flex;flex-wrap:wrap;gap:8px">
        ${(expData.principles || []).map(p => `<span class="badge" style="padding:6px 12px;font-size:13px">${p}</span>`).join('')}
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:20px 0">
      <div style="background:#fff;border:1px solid var(--border);border-radius:12px;padding:18px">
        <h3 style="margin-top:0">⚗️ Apparatus Checklist</h3>
        <ul style="padding-left:20px;line-height:1.7;margin:0">
          ${(expData.apparatus && expData.apparatus.length ? expData.apparatus : expData.materials || []).map(a => `<li>${a}</li>`).join('')}
        </ul>
      </div>

      <div style="background:#fff;border:1px solid var(--border);border-radius:12px;padding:18px">
        <h3 style="margin-top:0">🧪 Chemicals & Reagents</h3>
        <ul style="padding-left:20px;line-height:1.7;margin:0">
          ${(expData.chemicals && expData.chemicals.length ? expData.chemicals : expData.materials || []).map(c => `<li>${c}</li>`).join('')}
        </ul>
      </div>
    </div>

    <div style="background:#fff3cd;border:1px solid #ffeeba;border-radius:12px;padding:20px;margin:22px 0">
      <h3 style="margin-top:0;color:#856404">🛡️ Mandatory Safety Checklist</h3>
      <div class="checklist">
        <label class="check-item">
          <input type="checkbox" id="chkPpe" checked>
          <span>Safety goggles, lab coat, and chemical-resistant gloves equipped.</span>
        </label>
        <label class="check-item">
          <input type="checkbox" id="chkVent" checked>
          <span>Fume hood / ventilation operational; water bath verified.</span>
        </label>
        <label class="check-item">
          <input type="checkbox" id="chkSpill" checked>
          <span>Emergency eyewash and chemical spill kit locations confirmed.</span>
        </label>
        <label class="check-item">
          <input type="checkbox" id="chkSds" checked>
          <span>Reagent SDS and waste segregation protocols reviewed.</span>
        </label>
      </div>
    </div>

    <div style="display:flex;justify-content:flex-end;margin-top:25px;border-top:1px solid var(--border);padding-top:20px">
      <button class="btn" style="padding:12px 28px;font-size:15px" onclick="renderStage(2)">
        Proceed to Reaction Procedure Simulation →
      </button>
    </div>
  `;
}

// --- STAGE 2: Interactive Procedure Simulation ---
function renderSimulation() {
  statusBadge.textContent = 'Stage 2: Procedure Simulation';
  statusBadge.className = 'badge amber';

  const steps = expData.interactive_steps && expData.interactive_steps.length
    ? expData.interactive_steps
    : (expData.procedure || []).map((stepText, idx) => ({
        step: idx + 1,
        title: `Procedure Step ${idx + 1}`,
        instruction: stepText,
        action_name: `Execute Step ${idx + 1}`,
        feedback: `Completed: ${stepText}`
      }));

  const allDone = steps.every(s => completedSimSteps[s.step]);

  workspace.innerHTML = `
    <h2>Stage 2: Step-by-Step Procedure Simulation</h2>
    <p class="muted">Perform each experimental operation sequentially. Observe reaction indicators, catalyst interactions, and phase changes.</p>

    <div style="display:flex;flex-direction:column;gap:16px;margin:24px 0">
      ${steps.map(s => {
        const isCompleted = !!completedSimSteps[s.step];
        const stepNum = s.step;
        const canExecute = stepNum === 1 || !!completedSimSteps[stepNum - 1];

        return `
          <div class="card" style="border-left:5px solid ${isCompleted ? 'var(--green)' : canExecute ? 'var(--teal)' : '#cbdad1'};padding:18px">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
              <h3 style="margin:0;font-size:16px">Step ${stepNum}: ${s.title}</h3>
              <span class="badge ${isCompleted ? '' : 'secondary'}">
                ${isCompleted ? '✓ Completed' : canExecute ? 'Ready' : 'Pending'}
              </span>
            </div>

            <p style="margin:10px 0;line-height:1.6;font-size:14.5px">${s.instruction}</p>

            ${isCompleted ? `
              <div style="background:#eef7f2;border-radius:8px;padding:10px 14px;font-size:13.5px;color:var(--dark);margin-top:10px">
                <b>💡 Lab Observation:</b> ${s.feedback}
              </div>
            ` : `
              <div style="margin-top:12px">
                <button type="button" class="btn" style="padding:8px 18px;font-size:13.5px" ${canExecute ? '' : 'disabled style="opacity:0.5"'} onclick="runStepAction(${stepNum})">
                  🧪 ${s.action_name}
                </button>
              </div>
            `}
          </div>
        `;
      }).join('')}
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:25px;border-top:1px solid var(--border);padding-top:20px">
      <button class="btn secondary" onclick="renderStage(1)">← Back to Pre-Lab</button>
      <button class="btn" ${allDone ? '' : 'disabled style="opacity:0.5"'} onclick="renderStage(3)">
        Proceed to Record Observations →
      </button>
    </div>
  `;
}

window.runStepAction = function(stepNum) {
  completedSimSteps[stepNum] = true;
  renderStage(2);
};

// --- STAGE 3: Record Observations ---
function renderObservations() {
  statusBadge.textContent = 'Stage 3: Observations Entry';
  statusBadge.className = 'badge amber';

  if (!observations) {
    observations = `1. Physical State & Appearance: Clear liquid reactants mixed smoothly; catalyst beads remained heterogeneous at bottom.\n2. Thermal Characteristics: Reaction maintained steady temperature without exothermic runaway.\n3. Separation & Phase: Phase separation clearly observed after cooling; crisp boundary between aqueous and organic phases.`;
  }

  workspace.innerHTML = `
    <h2>Stage 3: Record Experimental Observations</h2>
    <p class="muted">Document qualitative and quantitative physical observations observed during the reaction steps.</p>

    <div style="margin:20px 0">
      <label style="font-weight:700;display:block;margin-bottom:8px">Experimental Observations (Color, State Changes, Temperature, Separation):</label>
      <textarea id="obsInput" class="textarea" rows="8" style="resize:vertical">${observations}</textarea>
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-top:25px;border-top:1px solid var(--border);padding-top:20px">
      <button class="btn secondary" onclick="renderStage(2)">← Back to Procedure</button>
      <button class="btn" onclick="saveObsAndNext()">
        Proceed to Results & Waste →
      </button>
    </div>
  `;
}

window.saveObsAndNext = function() {
  const val = document.getElementById('obsInput').value.trim();
  if (!val) {
    alert('Please enter your observations before proceeding.');
    return;
  }
  observations = val;
  renderStage(4);
};

// --- STAGE 4: Results & Waste Management ---
function renderResultsAndWaste() {
  statusBadge.textContent = 'Stage 4: Results & Waste';
  statusBadge.className = 'badge teal';

  if (!results) {
    results = `Isolated organic product with estimated 82% isolated yield. Reaction demonstrated high atom economy (~83%) with water as benign by-product.`;
  }
  if (!wasteManagement) {
    wasteManagement = expData.waste_management || 'Neutralized aqueous layer to pH 7 before disposal; recovered solid catalyst beads for subsequent cycles.';
  }

  workspace.innerHTML = `
    <h2>Stage 4: Result & Waste Management Evaluation</h2>
    <p class="muted">Record synthesis results, calculate green metrics, and select appropriate waste disposal methods.</p>

    <div style="margin:20px 0">
      <label style="font-weight:700;display:block;margin-bottom:8px">Experimental Results & Green Metrics Calculation:</label>
      <textarea id="resInput" class="textarea" rows="4" style="resize:vertical">${results}</textarea>
    </div>

    <div style="background:#eef7f2;border:1px solid var(--border);border-radius:12px;padding:20px;margin:22px 0">
      <h3 style="margin-top:0;color:var(--dark)">♻️ Green Waste Handling & Segregation Plan</h3>
      <p style="font-size:14px;margin-bottom:10px"><b>Expected Waste Generated:</b> ${expData.waste_generated || 'Aqueous wash and reusable catalyst.'}</p>
      <label style="font-weight:700;display:block;margin-bottom:6px">Document Segregation and Disposal Procedures Executed:</label>
      <textarea id="wasteInput" class="textarea" rows="3" style="resize:vertical">${wasteManagement}</textarea>
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:25px;border-top:1px solid var(--border);padding-top:20px">
      <button class="btn secondary" onclick="renderStage(3)">← Back to Observations</button>
      <button class="btn" onclick="saveResultsAndNext()">
        Proceed to Conclusion & Report Generation →
      </button>
    </div>
  `;
}

window.saveResultsAndNext = function() {
  const rVal = document.getElementById('resInput').value.trim();
  const wVal = document.getElementById('wasteInput').value.trim();
  if (!rVal || !wVal) {
    alert('Please complete both result and waste management entries.');
    return;
  }
  results = rVal;
  wasteManagement = wVal;
  renderStage(5);
};

// --- STAGE 5: Conclusion & Report Generation ---
function renderConclusion() {
  statusBadge.textContent = 'Stage 5: Final Review & Report';
  statusBadge.className = 'badge';

  if (!conclusion) {
    conclusion = `The virtual practical successfully demonstrated ${expData.name}. Replacing conventional hazardous methods with green alternatives minimized solvent toxicity, conserved energy, and prevented stoichiometric waste generation.`;
  }

  workspace.innerHTML = `
    <h2>Stage 5: Final Evaluation & Report Generation</h2>
    <p class="muted">Review summary details and submit your practical to generate a formal college laboratory record.</p>

    <div style="margin:20px 0">
      <label style="font-weight:700;display:block;margin-bottom:8px">Conclusion & Green Chemistry Reflection:</label>
      <textarea id="concInput" class="textarea" rows="4" style="resize:vertical">${conclusion}</textarea>
    </div>

    <div style="background:#f9fcf9;border:1px solid var(--border);border-radius:12px;padding:20px;margin:22px 0">
      <h3 style="margin-top:0">📋 Practical Summary Overview</h3>
      <ul style="line-height:1.8;padding-left:20px;margin:0">
        <li><b>Experiment:</b> ${expData.name} (${expData.category})</li>
        <li><b>Principles Applied:</b> ${(expData.principles || []).join(', ')}</li>
        <li><b>Observations Recorded:</b> ${observations.slice(0, 100)}...</li>
        <li><b>Report Action:</b> Automatically generated, stamped with student credentials, and saved to your Learning History.</li>
      </ul>
    </div>

    <div id="submitMsg"></div>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:25px;border-top:1px solid var(--border);padding-top:20px">
      <button class="btn secondary" onclick="renderStage(4)">← Back to Results</button>
      <button class="btn" style="background:linear-gradient(135deg,#127943,#0b806d);padding:14px 30px;font-size:15px" onclick="submitPractical()">
        ✓ Submit Practical & Generate Report →
      </button>
    </div>
  `;
}

window.submitPractical = async function() {
  const concVal = document.getElementById('concInput').value.trim();
  if (!concVal) {
    alert('Please enter a conclusion.');
    return;
  }
  conclusion = concVal;

  workspace.innerHTML = `
    <div style="text-align:center;padding:60px 20px">
      <h3>Generating Structured Laboratory Report...</h3>
      <p class="muted">Recording practical simulation into database and formatting official laboratory record.</p>
    </div>
  `;

  try {
    const res = await api('/practicals/submit', {
      method: 'POST',
      body: JSON.stringify({
        experiment_id: expData.id,
        observations: observations,
        result: results,
        conclusion: conclusion,
        waste_info: wasteManagement
      })
    });

    // Successfully saved! Redirect to the generated laboratory report
    location.href = `report.html?id=${res.report_id}`;
  } catch (err) {
    workspace.innerHTML = `
      <div style="text-align:center;padding:40px 20px">
        <h3 class="error">Submission Failed</h3>
        <p>${err.message || 'Please log in to submit practicals and generate reports.'}</p>
        <div style="margin-top:20px">
          <a class="btn" href="login.html">Login</a>
          <button class="btn secondary" onclick="renderStage(5)">Try Again</button>
        </div>
      </div>
    `;
  }
};

initPractical();
