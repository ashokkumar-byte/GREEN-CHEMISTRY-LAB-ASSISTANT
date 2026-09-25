const container = document.getElementById('quizContainer');
const navAuthBtn = document.getElementById('navAuthBtn');

let selectedTopic = 'all';
let selectedDifficulty = 'all';
let currentQuestions = [];
let currentIdx = 0;
let userAnswers = {};

// Available topic and difficulty options
const topics = [
  { id: 'all', name: '🎯 All Green Chemistry Topics' },
  { id: '12 Principles', name: '🌱 12 Principles of Green Chemistry' },
  { id: 'Atom Economy', name: '🔬 Atom Economy & Reaction Efficiency' },
  { id: 'Safety & Emergencies', name: '🛡️ Laboratory Safety & Emergency Protocols' },
  { id: 'Waste Management', name: '♻️ Chemical Waste & Segregation' },
  { id: 'Solvents & Catalysis', name: '⚡ Safer Solvents & Catalysis' }
];

const difficulties = [
  { id: 'all', name: 'All Levels' },
  { id: 'Easy', name: '🟢 Easy' },
  { id: 'Medium', name: '🟡 Medium' },
  { id: 'Hard', name: '🔴 Hard' }
];

// Check auth state for nav
api('/me').then(me => {
  if (navAuthBtn) {
    navAuthBtn.textContent = 'Dashboard';
    navAuthBtn.href = 'dashboard.html';
  }
}).catch(() => {});

function renderSetup() {
  container.innerHTML = `
    <h2>⚙️ Smart Quiz Setup</h2>
    <p class="muted">Select a topic and difficulty level. Every attempt selects a fresh, randomized question set.</p>

    <h3 style="margin-top:20px;font-size:16px">1. Choose Topic</h3>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:12px 0 20px">
      ${topics.map(t => `
        <div class="quiz-topic-btn ${selectedTopic === t.id ? 'selected' : ''}" onclick="selectTopic('${t.id}')">
          <b>${t.name}</b>
        </div>
      `).join('')}
    </div>

    <h3 style="font-size:16px">2. Choose Difficulty</h3>
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin:12px 0 25px">
      ${difficulties.map(d => `
        <button type="button" class="btn ${selectedDifficulty === d.id ? '' : 'secondary'}" style="padding:10px 18px" onclick="selectDifficulty('${d.id}')">
          ${d.name}
        </button>
      `).join('')}
    </div>

    <div style="text-align:right;border-top:1px solid var(--border);padding-top:20px">
      <button class="btn" style="padding:13px 28px;font-size:15px" onclick="startQuiz()">Start Quiz (5 Questions) →</button>
    </div>
  `;
}

window.selectTopic = function(topicId) {
  selectedTopic = topicId;
  renderSetup();
};

window.selectDifficulty = function(diffId) {
  selectedDifficulty = diffId;
  renderSetup();
};

window.startQuiz = async function() {
  container.innerHTML = `
    <div style="text-align:center;padding:50px 20px">
      <h3>Generating Randomized Question Set...</h3>
      <p class="muted">Selecting questions from the green chemistry pool.</p>
    </div>
  `;

  try {
    const url = `/quiz/questions?topic=${encodeURIComponent(selectedTopic)}&difficulty=${encodeURIComponent(selectedDifficulty)}&count=5`;
    const res = await api(url);
    if (!res.questions || res.questions.length === 0) {
      container.innerHTML = `
        <p class="error">No questions found for this topic/difficulty combination.</p>
        <button class="btn secondary" onclick="renderSetup()">Back to Setup</button>
      `;
      return;
    }

    currentQuestions = res.questions;
    currentIdx = 0;
    userAnswers = {};
    renderQuestion();
  } catch (err) {
    container.innerHTML = `
      <p class="error">${err.message || 'Error loading questions'}</p>
      <button class="btn secondary" onclick="renderSetup()">Try Again</button>
    `;
  }
};

function renderQuestion() {
  const q = currentQuestions[currentIdx];
  const total = currentQuestions.length;
  const progressPct = ((currentIdx + 1) / total) * 100;
  const currentSelection = userAnswers[q.id];

  container.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <span style="font-weight:700;font-size:14px;color:var(--dark)">Question ${currentIdx + 1} of ${total}</span>
      <div>
        <span class="badge teal">${q.topic}</span>
        <span class="badge ${q.difficulty === 'Easy' ? '' : q.difficulty === 'Hard' ? 'red' : 'amber'}">${q.difficulty}</span>
      </div>
    </div>

    <div class="progress-bar">
      <div class="progress-fill" style="width: ${progressPct}%"></div>
    </div>

    <h2 style="font-size:18px;margin:20px 0 16px;line-height:1.5">${q.question}</h2>

    <div style="margin:16px 0">
      ${q.options.map((opt, i) => `
        <button type="button" class="quiz-option ${currentSelection === opt ? 'selected' : ''}" onclick="pickOption(${q.id}, '${opt.replace(/'/g, "\\'")}')">
          <b>${String.fromCharCode(65 + i)}.</b> ${opt}
        </button>
      `).join('')}
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--border);padding-top:18px;margin-top:20px">
      <button type="button" class="btn secondary" ${currentIdx === 0 ? 'disabled style="opacity:0.5"' : ''} onclick="prevQuestion()">
        ← Previous
      </button>

      ${currentIdx === total - 1 ? `
        <button type="button" class="btn" style="background:#0e8372" onclick="submitQuiz()">
          ✓ Submit Quiz
        </button>
      ` : `
        <button type="button" class="btn" onclick="nextQuestion()">
          Next →
        </button>
      `}
    </div>
  `;
}

window.pickOption = function(qid, optionText) {
  userAnswers[qid] = optionText;
  renderQuestion();
};

window.nextQuestion = function() {
  if (currentIdx < currentQuestions.length - 1) {
    currentIdx++;
    renderQuestion();
  }
};

window.prevQuestion = function() {
  if (currentIdx > 0) {
    currentIdx--;
    renderQuestion();
  }
};

window.submitQuiz = async function() {
  const answeredCount = Object.keys(userAnswers).length;
  const total = currentQuestions.length;

  if (answeredCount < total) {
    const unanswered = total - answeredCount;
    if (!confirm(`You have ${unanswered} unanswered question(s). Are you sure you want to submit?`)) {
      return;
    }
  }

  container.innerHTML = `
    <div style="text-align:center;padding:50px 20px">
      <h3>Evaluating Your Quiz Answers...</h3>
      <p class="muted">Grading and recording results into your learning history.</p>
    </div>
  `;

  try {
    const res = await api('/quiz/submit', {
      method: 'POST',
      body: JSON.stringify({
        topic: selectedTopic === 'all' ? 'General Green Chemistry' : selectedTopic,
        difficulty: selectedDifficulty === 'all' ? 'Mixed' : selectedDifficulty,
        answers: Object.fromEntries(currentQuestions.map(question => [question.id, userAnswers[question.id] || null]))
      })
    });

    renderReview(res);
  } catch (err) {
    container.innerHTML = `
      <div style="text-align:center;padding:30px">
        <h3 class="error">Quiz Submission Error</h3>
        <p>${err.message || 'Please log in to save your quiz results.'}</p>
        <div style="margin-top:20px">
          <a class="btn" href="login.html">Login</a>
          <button class="btn secondary" onclick="renderSetup()">Back to Setup</button>
        </div>
      </div>
    `;
  }
};

function renderReview(res) {
  const pct = res.percentage;
  let gradeBadge = 'badge';
  let gradeMessage = 'Review recommended to strengthen principles.';

  if (pct >= 80) {
    gradeBadge = 'badge';
    gradeMessage = '🌟 Outstanding Mastery! Excellent understanding of Green Chemistry principles.';
  } else if (pct >= 60) {
    gradeBadge = 'badge teal';
    gradeMessage = '👍 Good performance! Solid knowledge with minor areas for review.';
  }

  container.innerHTML = `
    <div style="text-align:center;border-bottom:1px solid var(--border);padding-bottom:24px;margin-bottom:24px">
      <span class="${gradeBadge}" style="font-size:14px;padding:8px 16px">Score: ${res.score} / ${res.total_questions} (${pct}%)</span>
      <h2 style="margin:16px 0 8px">${gradeMessage}</h2>
      <p class="muted">Topic: <b>${selectedTopic === 'all' ? 'General Green Chemistry' : selectedTopic}</b> • Difficulty: <b>${selectedDifficulty}</b></p>

      <div style="display:flex;gap:10px;justify-content:center;margin-top:18px;flex-wrap:wrap">
        <button class="btn" onclick="startQuiz()">🔄 Try Again (Fresh Randomized Set)</button>
        <button class="btn secondary" onclick="renderSetup()">⚙️ Change Topic / Difficulty</button>
        <a class="btn secondary" href="history.html">📜 View in History</a>
      </div>
    </div>

    <h3>🔍 Comprehensive Question Review</h3>
    <div style="margin-top:16px">
      ${res.review.map((item, idx) => `
        <div class="review-card ${item.is_correct ? 'correct' : 'incorrect'}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <b>Question ${idx + 1}</b>
            <span style="font-weight:bold;color:${item.is_correct ? 'var(--green)' : 'var(--danger)'}">
              ${item.is_correct ? '✓ Correct (+1)' : '✗ Incorrect (0)'}
            </span>
          </div>

          <p style="margin:8px 0;font-size:15.5px"><b>${item.question}</b></p>

          <div style="font-size:14px;margin:8px 0;line-height:1.6">
            <div>Your Answer: <span style="font-weight:600;color:${item.is_correct ? 'var(--green)' : 'var(--danger)'}">${item.selected || '*(No answer selected)*'}</span></div>
            ${!item.is_correct ? `<div>Correct Answer: <b style="color:var(--green)">${item.correct_answer}</b></div>` : ''}
          </div>

          ${item.explanation ? `
            <div style="margin-top:10px;padding:10px 14px;background:rgba(255,255,255,0.7);border-radius:8px;font-size:13px;border-left:3px solid var(--green)">
              <b>💡 Educational Insight:</b> ${item.explanation}
            </div>
          ` : ''}
        </div>
      `).join('')}
    </div>

    <div style="text-align:center;margin-top:30px;padding-top:20px;border-top:1px solid var(--border)">
      <button class="btn" onclick="startQuiz()">🔄 Take Another Quiz</button>
    </div>
  `;
}

renderSetup();
