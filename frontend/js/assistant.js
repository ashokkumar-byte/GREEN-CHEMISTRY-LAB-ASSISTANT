const chat = document.getElementById('chat');
const form = document.getElementById('chatForm');
const questionInput = document.getElementById('question');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearChatBtn');
const aiStatus = document.getElementById('aiStatus');
const navAuthBtn = document.getElementById('navAuthBtn');

let currentUser = null;
let isTyping = false;

// Safe Markdown Parser for Assistant Responses
function renderMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Headings
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h3 style="font-size:17px">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h3 style="font-size:18px">$1</h3>');

  // Bold & Italic
  html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<b><i>$1</i></b>');
  html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
  html = html.replace(/\*(.*?)\*/g, '<i>$1</i>');

  // Inline Code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Blockquotes
  html = html.replace(/^&gt; (.*$)/gim, '<blockquote>$1</blockquote>');

  // List Items
  html = html.replace(/^\s*[\-\*]\s+(.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gis, '<ul>$1</ul>');
  html = html.replace(/<\/ul>\s*<ul>/g, '');

  // Paragraphs
  html = html.replace(/\n\n+/g, '</p><p>');
  html = '<p>' + html.replace(/\n/g, '<br>') + '</p>';
  html = html.replace(/<p><\/p>/g, '');
  html = html.replace(/<p><h3>/g, '<h3>').replace(/<\/h3><\/p>/g, '</h3>');
  html = html.replace(/<p><ul>/g, '<ul>').replace(/<\/ul><\/p>/g, '</ul>');
  html = html.replace(/<p><blockquote>/g, '<blockquote>').replace(/<\/blockquote><\/p>/g, '</blockquote>');

  return html;
}

// Copy text to clipboard with user feedback
function copyToClipboard(button, rawText) {
  if (!navigator.clipboard) {
    const ta = document.createElement('textarea');
    ta.value = rawText;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  } else {
    navigator.clipboard.writeText(rawText).catch(() => {});
  }
  const original = button.innerHTML;
  button.innerHTML = '✓ Copied!';
  button.classList.add('copied');
  setTimeout(() => {
    button.innerHTML = original;
    button.classList.remove('copied');
  }, 2000);
}

// Append a message bubble to the chat container
function appendMessage(role, text, animate = false) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-msg ${role}`;

  const header = document.createElement('div');
  header.className = 'chat-header-bar';

  if (role === 'user') {
    header.innerHTML = `<span>👤 You</span>`;
  } else {
    const titleSpan = document.createElement('span');
    titleSpan.textContent = '🤖 AI Assistant';

    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.className = 'copy-btn';
    copyBtn.innerHTML = '📋 Copy';
    copyBtn.onclick = () => copyToClipboard(copyBtn, text);

    header.appendChild(titleSpan);
    header.appendChild(copyBtn);
  }

  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble';

  msgDiv.appendChild(header);
  msgDiv.appendChild(bubble);
  chat.appendChild(msgDiv);

  if (role === 'assistant' && animate) {
    // Progressive Typing Animation
    let currentIdx = 0;
    const speed = 12; // ms per step
    const chunkSize = 4; // chars per step
    let skipped = false;

    // Allow user to click to skip typing animation
    bubble.onclick = () => {
      if (!skipped) {
        skipped = true;
        bubble.innerHTML = renderMarkdown(text);
        chat.scrollTop = chat.scrollHeight;
      }
    };

    const interval = setInterval(() => {
      if (skipped) {
        clearInterval(interval);
        return;
      }
      currentIdx += chunkSize;
      if (currentIdx >= text.length) {
        currentIdx = text.length;
        bubble.innerHTML = renderMarkdown(text);
        clearInterval(interval);
        chat.scrollTop = chat.scrollHeight;
      } else {
        bubble.innerHTML = renderMarkdown(text.slice(0, currentIdx) + ' ▋');
        chat.scrollTop = chat.scrollHeight;
      }
    }, speed);
  } else {
    bubble.innerHTML = role === 'user' ? text.replace(/</g, '&lt;') : renderMarkdown(text);
  }

  chat.scrollTop = chat.scrollHeight;
}

// Show Typing Indicator Animation
function showTypingIndicator() {
  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-msg assistant';
  typingDiv.id = 'typingIndicator';
  typingDiv.innerHTML = `
    <div class="chat-header-bar"><span>🤖 AI Assistant is typing...</span></div>
    <div class="typing-indicator">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>
  `;
  chat.appendChild(typingDiv);
  chat.scrollTop = chat.scrollHeight;
}

function hideTypingIndicator() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

// Initial Welcome Message
function showWelcomeMessage() {
  const welcomeText = 
    "### 👋 Welcome to your Green Chemistry Lab Assistant!\n\n" +
    "I'm your dedicated educational AI guide for sustainable chemistry.\n\n" +
    "Here's what we can explore together:\n" +
    "- **12 Principles of Green Chemistry**: Deep-dive into atom economy, waste prevention, and catalysis.\n" +
    "- **Lab Experiments**: Get step-by-step guidance, green metrics, and procedures for our lab's experiments.\n" +
    "- **Safety & Protocols**: Review PPE requirements, spill protocols, and emergency guidelines.\n" +
    "- **Waste Management**: Learn how to reduce and segregate halogenated vs non-halogenated waste.\n" +
    "- **Safer Alternatives**: Discover green solvents and catalytic replacements for toxic reagents.\n\n" +
    "> *Select any topic chip above or type your question below to begin!*";
  appendMessage('assistant', welcomeText, false);
}

// Load Chat History & User Status
async function initAssistant() {
  try {
    const me = await api('/me');
    currentUser = me.user;
    if (navAuthBtn) {
      navAuthBtn.textContent = 'Dashboard';
      navAuthBtn.href = 'dashboard.html';
    }
    if (aiStatus) {
      aiStatus.textContent = `🌱 Logged in as ${currentUser.name}`;
    }

    // Load saved conversation history
    const historyRes = await api('/assistant/history');
    if (historyRes.history && historyRes.history.length > 0) {
      chat.innerHTML = '';
      historyRes.history.forEach(item => {
        appendMessage(item.role, item.content, false);
      });
    } else {
      chat.innerHTML = '';
      showWelcomeMessage();
    }
  } catch (err) {
    // User is not logged in
    chat.innerHTML = '';
    const loginNotice = document.createElement('div');
    loginNotice.className = 'card';
    loginNotice.style.background = '#fff8e6';
    loginNotice.style.borderColor = '#faecc6';
    loginNotice.style.margin = '10px 0';
    loginNotice.innerHTML = `
      <b>ℹ️ Login Required for Persistent Chat:</b><br>
      Please <a href="login.html" style="color:var(--green);font-weight:bold;text-decoration:underline">Login here</a>
      to save your learning history, ask AI questions, and access your student dashboard.
    `;
    chat.appendChild(loginNotice);
    showWelcomeMessage();
    if (aiStatus) {
      aiStatus.textContent = '⚠️ Login Required';
      aiStatus.style.background = '#fff0f0';
      aiStatus.style.color = '#c53030';
    }
  }
}

// Form Submit Handler
if (form) {
  form.onsubmit = async (e) => {
    e.preventDefault();
    const q = questionInput.value.trim();
    if (!q || isTyping) return;

    appendMessage('user', q);
    questionInput.value = '';
    questionInput.disabled = true;
    sendBtn.disabled = true;
    isTyping = true;

    showTypingIndicator();

    try {
      const res = await api('/assistant', {
        method: 'POST',
        body: JSON.stringify({ message: q })
      });
      hideTypingIndicator();
      appendMessage('assistant', res.answer, true);
    } catch (err) {
      hideTypingIndicator();
      const errMsg = err.message || 'Failed to receive response. Please try again.';
      appendMessage('assistant', `⚠️ **Error:** ${errMsg}`, false);
    } finally {
      questionInput.disabled = false;
      sendBtn.disabled = false;
      questionInput.focus();
      isTyping = false;
    }
  };
}

// Clear Chat Handler
if (clearBtn) {
  clearBtn.onclick = async () => {
    if (!confirm('Are you sure you want to clear your chat history?')) return;
    try {
      await api('/assistant/history', { method: 'DELETE' });
      chat.innerHTML = '';
      showWelcomeMessage();
    } catch (err) {
      alert(err.message || 'Could not clear chat history');
    }
  };
}

// Quick Topic Chips Handler
document.querySelectorAll('.chip').forEach(chip => {
  chip.onclick = () => {
    const prompt = chip.getAttribute('data-prompt');
    if (prompt && questionInput) {
      questionInput.value = prompt;
      if (form) {
        form.dispatchEvent(new Event('submit'));
      }
    }
  };
});

initAssistant();
