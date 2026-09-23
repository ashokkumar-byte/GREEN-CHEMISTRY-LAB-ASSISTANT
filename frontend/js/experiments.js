const navAuthBtn = document.getElementById('navAuthBtn');
api('/me').then(me => {
  if (navAuthBtn) {
    navAuthBtn.textContent = 'Dashboard';
    navAuthBtn.href = 'dashboard.html';
  }
}).catch(() => {});

// --- Experiments List View ---
async function loadExperiments() {
  const box = document.getElementById('experiments');
  if (!box) return;

  const searchInput = document.getElementById('searchInput');
  const catFilter = document.getElementById('categoryFilter');
  const diffFilter = document.getElementById('difficultyFilter');
  const princFilter = document.getElementById('principleFilter');

  async function fetchAndRender() {
    const q = searchInput ? searchInput.value.trim() : '';
    const cat = catFilter ? catFilter.value : 'all';
    const diff = diffFilter ? diffFilter.value : 'all';
    const princ = princFilter ? princFilter.value : 'all';

    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (cat !== 'all') params.set('category', cat);
    if (diff !== 'all') params.set('difficulty', diff);
    if (princ !== 'all') params.set('principle', princ);

    box.innerHTML = '<p class="muted">Searching experiments...</p>';

    try {
      const res = await api('/experiments?' + params.toString());
      const list = res.experiments || res;

      if (!list || list.length === 0) {
        box.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 40px 20px;">
            <h3>No experiments match your filter criteria.</h3>
            <p class="muted">Try adjusting your search terms or clearing the filters.</p>
          </div>
        `;
        return;
      }

      box.innerHTML = list.map(exp => {
        const principlesList = exp.principles || [];
        const diffClass = exp.difficulty === 'Beginner' ? '' : exp.difficulty === 'Advanced' ? 'red' : 'amber';

        return `
          <div class="card" style="display:flex;flex-direction:column;justify-content:space-between">
            <div>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px">
                <span class="badge teal">${exp.category}</span>
                <div>
                  <span class="badge ${diffClass}">${exp.difficulty}</span>
                  <span class="badge">${exp.safety_level || 'Low'} Safety</span>
                </div>
              </div>

              <h3 style="margin:10px 0 6px">${exp.name}</h3>
              <p class="muted" style="font-size:14px;line-height:1.5;margin-bottom:12px">${exp.description}</p>

              <div style="margin-bottom:14px">
                <div style="font-size:12px;font-weight:700;color:var(--dark);margin-bottom:4px">Green Principles:</div>
                <div style="display:flex;flex-wrap:wrap;gap:4px">
                  ${principlesList.slice(0, 3).map(p => `<span class="badge" style="font-size:11px;padding:3px 7px">${p}</span>`).join('')}
                </div>
              </div>
            </div>

            <div style="display:flex;gap:8px;margin-top:16px;border-top:1px solid var(--border);padding-top:14px">
              <a class="btn secondary" style="flex:1;padding:9px 12px;font-size:13px" href="experiment-details.html?id=${exp.id}">
                Details
              </a>
              <a class="btn" style="flex:1.2;padding:9px 12px;font-size:13px;background:linear-gradient(135deg,#127943,#0b806d)" href="practical-lab.html?id=${exp.id}">
                🔬 Virtual Lab
              </a>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      box.innerHTML = `<p class="error">Error loading experiments: ${err.message}</p>`;
    }
  }

  let debounceTimer;
  if (searchInput) {
    searchInput.oninput = () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(fetchAndRender, 250);
    };
  }
  if (catFilter) catFilter.onchange = fetchAndRender;
  if (diffFilter) diffFilter.onchange = fetchAndRender;
  if (princFilter) princFilter.onchange = fetchAndRender;

  fetchAndRender();
}

// --- Experiment Details View ---
async function loadDetails() {
  const detailsBox = document.getElementById('details');
  if (!detailsBox) return;

  const id = new URLSearchParams(location.search).get('id');
  if (!id) {
    detailsBox.innerHTML = '<p class="error">No experiment selected. <a href="experiments.html">Return to experiments list</a></p>';
    return;
  }

  try {
    const res = await api('/experiments/' + id);
    const exp = res.experiment;
    if (!exp) throw new Error('Experiment data not found');

    const topBtns = document.getElementById('topActionBtns');
    if (topBtns) {
      topBtns.innerHTML = `
        <a class="btn" style="background:linear-gradient(135deg,#127943,#0b806d);padding:9px 18px" href="practical-lab.html?id=${exp.id}">
          🔬 Start Virtual Practical
        </a>
      `;
    }

    detailsBox.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:12px">
        <span class="badge teal" style="font-size:13px">${exp.category}</span>
        <div>
          <span class="badge" style="font-size:13px">${exp.difficulty} Level</span>
          <span class="badge" style="font-size:13px">Safety: ${exp.safety_level}</span>
        </div>
      </div>

      <h1 style="margin:6px 0 12px;color:var(--dark)">${exp.name}</h1>
      <p style="font-size:16px;line-height:1.6;color:var(--muted)">${exp.description}</p>

      ${exp.aim ? `
        <div style="background:#f4fbf7;border-left:4px solid var(--green);padding:14px 18px;border-radius:6px;margin:18px 0">
          <b style="color:var(--dark)">🎯 Experiment Aim:</b> ${exp.aim}
        </div>
      ` : ''}

      <div style="margin:22px 0">
        <h3>🌱 Green Chemistry Principles Involved</h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          ${(exp.principles || []).map(p => `<span class="badge" style="padding:6px 12px;font-size:13px">${p}</span>`).join('')}
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:22px 0">
        <div style="background:#fff;border:1px solid var(--border);border-radius:12px;padding:18px">
          <h3 style="margin-top:0">⚗️ Apparatus & Equipment</h3>
          <ul style="padding-left:20px;line-height:1.7;margin-bottom:0">
            ${(exp.apparatus && exp.apparatus.length ? exp.apparatus : exp.materials || []).map(a => `<li>${a}</li>`).join('')}
          </ul>
        </div>

        <div style="background:#fff;border:1px solid var(--border);border-radius:12px;padding:18px">
          <h3 style="margin-top:0">🧪 Chemicals & Reagents</h3>
          <ul style="padding-left:20px;line-height:1.7;margin-bottom:0">
            ${(exp.chemicals && exp.chemicals.length ? exp.chemicals : exp.materials || []).map(c => `<li>${c}</li>`).join('')}
          </ul>
        </div>
      </div>

      <div style="background:#fff3cd;border:1px solid #ffeeba;border-radius:12px;padding:18px;margin:22px 0;color:#856404">
        <h3 style="margin-top:0;color:#856404">🛡️ Safety Precautions</h3>
        <ul style="padding-left:20px;line-height:1.7;margin-bottom:0">
          ${(exp.safety_precautions || ["Wear standard laboratory PPE (goggles, lab coat, gloves)."]).map(s => `<li>${s}</li>`).join('')}
        </ul>
      </div>

      <div style="margin:22px 0">
        <h3>📋 Step-by-Step Procedure</h3>
        <ol style="padding-left:22px;line-height:1.8">
          ${(exp.procedure || []).map(step => `<li style="margin-bottom:6px">${step}</li>`).join('')}
        </ol>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:22px 0">
        <div style="background:#eef7f2;border:1px solid var(--border);border-radius:12px;padding:18px">
          <h3 style="margin-top:0;color:var(--dark)">♻️ Waste & Environmental Management</h3>
          <p style="margin-bottom:8px"><b>Waste Generated:</b> ${exp.waste_generated || 'Minimal reaction residue.'}</p>
          <p style="margin:0"><b>Management Method:</b> ${exp.waste_management || 'Neutralization and institutional collection.'}</p>
        </div>

        <div style="background:#eef7f2;border:1px solid var(--border);border-radius:12px;padding:18px">
          <h3 style="margin-top:0;color:var(--dark)">🔄 Safer Chemical Alternatives</h3>
          <ul style="padding-left:20px;line-height:1.6;margin:0">
            ${(exp.alternatives || ["Replaced volatile organic solvents with benign substitutes."]).map(alt => `<li>${alt}</li>`).join('')}
          </ul>
        </div>
      </div>

      <div style="text-align:center;margin-top:35px;padding-top:25px;border-top:1px solid var(--border)">
        <a class="btn" style="background:linear-gradient(135deg,#127943,#0b806d);padding:14px 32px;font-size:16px" href="practical-lab.html?id=${exp.id}">
          🔬 Enter Virtual Practical Lab →
        </a>
      </div>
    `;
  } catch (err) {
    detailsBox.innerHTML = `<p class="error">Failed to load details: ${err.message}</p>`;
  }
}

loadExperiments();
loadDetails();
