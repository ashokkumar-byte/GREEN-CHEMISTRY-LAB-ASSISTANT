async function loadDashboard() {
  try {
    const me = await api('/me');
    document.querySelectorAll('[data-name]').forEach(e => e.textContent = me.user.name);
    const badge = document.getElementById('studentUsernameBadge');
    if (badge) badge.textContent = `@${me.user.username}`;

    const s = await api('/stats');
    const pEl = document.getElementById('practicalsCount');
    if (pEl) pEl.textContent = s.practicals || 0;

    const rEl = document.getElementById('reportCount');
    if (rEl) rEl.textContent = s.reports || 0;

    const qEl = document.getElementById('quizCount');
    if (qEl) qEl.textContent = s.quizzes || 0;

    const aEl = document.getElementById('avgQuizScore');
    if (aEl) aEl.textContent = `${s.avg_quiz_score || 0}%`;

    const eEl = document.getElementById('experimentCount');
    if (eEl) eEl.textContent = s.experiments || 4;

    const prog = s.learning_progress || 0;
    const ptEl = document.getElementById('progressText');
    if (ptEl) ptEl.textContent = `${prog}%`;

    const pfEl = document.getElementById('progressFill');
    if (pfEl) pfEl.style.width = `${prog}%`;

    const actBox = document.getElementById('recentActivityList');
    if (actBox) {
      if (s.recent_activity && s.recent_activity.length > 0) {
        actBox.innerHTML = s.recent_activity.map(act => {
          let icon = '📌';
          if (act.type.includes('Practical')) icon = '🔬';
          else if (act.type.includes('Quiz')) icon = '📝';
          else if (act.type.includes('Report')) icon = '📑';
          else if (act.type.includes('AI')) icon = '🤖';

          return `
            <div class="activity-item">
              <div>
                <b>${icon} ${act.type}</b>
                <div class="muted" style="font-size:13px">${act.details || 'Completed task'}</div>
              </div>
              <span class="muted" style="font-size:12px">${act.created_at || ''}</span>
            </div>
          `;
        }).join('');
      } else {
        actBox.innerHTML = '<p class="muted">No recent activity yet. Start your first practical or quiz above!</p>';
      }
    }
  } catch (e) {
    if (location.pathname.endsWith('dashboard.html')) {
      location.href = 'login.html';
    }
  }
}

loadDashboard();
