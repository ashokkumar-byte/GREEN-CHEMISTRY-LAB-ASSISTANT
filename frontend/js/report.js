const reportBox = document.getElementById('reportContainer');
const navAuthBtn = document.getElementById('navAuthBtn');

api('/me').then(me => {
  if (navAuthBtn) {
    navAuthBtn.textContent = 'Dashboard';
    navAuthBtn.href = 'dashboard.html';
  }
}).catch(() => {});

async function loadReport() {
  const id = new URLSearchParams(location.search).get('id');
  if (!id) {
    reportBox.innerHTML = `
      <div class="card" style="text-align:center;padding:40px">
        <h3 class="error">No Report ID Specified</h3>
        <p class="muted">Please select a completed practical report from your history.</p>
        <a class="btn" href="history.html">Go to History</a>
      </div>
    `;
    return;
  }

  try {
    const res = await api(`/reports/${id}`);
    const rep = res.report;
    const c = rep.content || {};
    const generatedMessage = '<div class="success" style="text-align:center;padding:12px 16px;margin-bottom:18px;font-weight:700">Report Generated Successfully</div>';

    reportBox.innerHTML = `
      ${generatedMessage}
      <div class="report-sheet">
        <div style="text-align:center;border-bottom:3px double var(--green);padding-bottom:14px;margin-bottom:20px">
          <div style="font-size:13px;letter-spacing:1px;font-weight:700;color:var(--muted)">DEPARTMENT OF CHEMISTRY • SUSTAINABLE LABORATORY PROGRAM</div>
          <h1 style="border:none;margin:8px 0 4px;font-size:26px">OFFICIAL LABORATORY RECORD</h1>
          <div style="font-size:15px;color:var(--teal);font-weight:700">${c.experiment_name || rep.title}</div>
        </div>

        <div class="report-meta-grid">
          <div><b>Student Name:</b> ${c.student_name || 'Student'}</div>
          <div><b>Roll / Username:</b> @${c.student_username || 'user'}</div>
          <div><b>Email:</b> ${c.student_email || 'N/A'}</div>
          <div><b>Date & Time:</b> ${c.date || rep.created_at}</div>
          <div><b>Discipline / Category:</b> ${c.category || 'Organic Chemistry'}</div>
          <div><b>Record ID:</b> #REP-${rep.id.toString().padStart(4, '0')}</div>
        </div>

        <div class="report-section">
          <h3>1. Aim of the Experiment</h3>
          <p>${c.aim || 'To synthesize the target compound adhering to Green Chemistry principles.'}</p>
        </div>

        <div class="report-section">
          <h3>2. Green Chemistry Principles Involved</h3>
          <ul style="padding-left:22px;line-height:1.7">
            ${(c.principles || []).map(p => `<li><b>${p}</b></li>`).join('')}
          </ul>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px" class="report-section">
          <div style="border:1px solid #dce9e1;border-radius:8px;padding:14px;background:#fafdfb">
            <h4 style="margin-top:0;color:var(--dark)">⚗️ Apparatus & Equipment</h4>
            <ul style="padding-left:20px;line-height:1.6;margin:0">
              ${(c.apparatus || c.materials || []).map(a => `<li>${a}</li>`).join('')}
            </ul>
          </div>

          <div style="border:1px solid #dce9e1;border-radius:8px;padding:14px;background:#fafdfb">
            <h4 style="margin-top:0;color:var(--dark)">🧪 Chemicals & Reagents</h4>
            <ul style="padding-left:20px;line-height:1.6;margin:0">
              ${(c.chemicals || c.materials || []).map(ch => `<li>${ch}</li>`).join('')}
            </ul>
          </div>
        </div>

        <div class="report-section" style="background:#fffbee;border:1px solid #faecc6;border-radius:8px;padding:14px">
          <h4 style="margin-top:0;color:#856404">🛡️ Safety Precautions & PPE Compliance</h4>
          <ul style="padding-left:20px;line-height:1.6;margin:0;color:#6d4d00">
            ${(c.safety_precautions || ["Standard PPE worn at all times."]).map(s => `<li>${s}</li>`).join('')}
          </ul>
        </div>

        <div class="report-section">
          <h3>3. Experimental Procedure</h3>
          <ol style="padding-left:22px;line-height:1.8">
            ${(c.procedure || []).map(step => `<li>${step}</li>`).join('')}
          </ol>
        </div>

        <div class="report-section">
          <h3>4. Experimental Observations</h3>
          <div style="background:#f4fbf7;border-left:4px solid var(--green);padding:14px 18px;border-radius:6px;line-height:1.7;white-space:pre-line">
            ${c.observations || 'No specific observations recorded.'}
          </div>
        </div>

        <div class="report-section">
          <h3>5. Results & Calculations</h3>
          <div style="background:#f4fbf7;border-left:4px solid var(--teal);padding:14px 18px;border-radius:6px;line-height:1.7;white-space:pre-line">
            ${c.result || 'Target product successfully isolated with high atom economy.'}
          </div>
        </div>

        <div class="report-section" style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
          <div style="border:1px solid #dce9e1;border-radius:8px;padding:14px;background:#fafdfb">
            <h4 style="margin-top:0;color:var(--dark)">♻️ Waste Generated</h4>
            <p style="margin:0">${c.waste_generated || 'Minimal reaction residue.'}</p>
          </div>

          <div style="border:1px solid #dce9e1;border-radius:8px;padding:14px;background:#fafdfb">
            <h4 style="margin-top:0;color:var(--dark)">♻️ Waste Management Method</h4>
            <p style="margin:0">${c.waste_management || 'Neutralized and segregated safely.'}</p>
          </div>
        </div>

        <div class="report-section">
          <h3>6. Conclusion & Green Evaluation</h3>
          <p style="line-height:1.7">${c.conclusion || 'The practical demonstrated viable sustainable synthesis adhering to green metrics.'}</p>
        </div>

        <div style="display:flex;justify-content:space-between;margin-top:50px;padding-top:30px;border-top:1px dashed #b8ded0">
          <div>
            <b>Student Signature:</b><br>
            <span style="font-family:cursive;font-size:18px;color:var(--green)">${c.student_name || 'Student'}</span>
          </div>
          <div style="text-align:right">
            <b>Laboratory Instructor Verification:</b><br>
            <span style="font-size:13px;color:var(--muted)">Verified & Recorded digitally on ${c.date || rep.created_at}</span>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    reportBox.innerHTML = `
      <div class="card" style="text-align:center;padding:40px">
        <h3 class="error">Report Load Error</h3>
        <p>${err.message || 'Could not retrieve report'}</p>
        <a class="btn" href="history.html">Back to History</a>
      </div>
    `;
  }
}

loadReport();
