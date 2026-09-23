import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from flask import Blueprint, request, jsonify, session
from config import AI_API_KEY, AI_API_URL, AI_MODEL, DATA_DIR
from database import connect, save_chat_message, get_chat_history, clear_chat_history

logger = logging.getLogger(__name__)
bp = Blueprint('assistant', __name__)

def load_curriculum():
    """Loads all Green Chemistry curriculum data files."""
    data = {}
    try:
        p_path = DATA_DIR / 'principles.json'
        if p_path.exists():
            data['principles'] = json.loads(p_path.read_text(encoding='utf-8'))
        e_path = DATA_DIR / 'experiments.json'
        if e_path.exists():
            data['experiments'] = json.loads(e_path.read_text(encoding='utf-8'))
        s_path = DATA_DIR / 'safety.json'
        if s_path.exists():
            data['safety'] = json.loads(s_path.read_text(encoding='utf-8'))
        a_path = DATA_DIR / 'alternatives.json'
        if a_path.exists():
            data['alternatives'] = json.loads(a_path.read_text(encoding='utf-8'))
    except Exception as e:
        logger.warning(f"Error loading curriculum files: {e}")
    return data

def build_system_prompt():
    """Builds a rich, domain-specific Green Chemistry system prompt."""
    curriculum = load_curriculum()
    prompt = (
        "You are the Green Chemistry Lab Assistant, an expert educational AI companion dedicated "
        "to teaching green chemistry, laboratory safety, sustainable syntheses, waste minimization, "
        "and safer chemical alternatives.\n\n"
        "Guidelines:\n"
        "- Prioritize lab safety and environmental sustainability above all.\n"
        "- Explain concepts clearly with formatted Markdown (headings, bullet points, bold key terms).\n"
        "- Cover metrics like Atom Economy (% = (FW target / FW all reactants) * 100), E-factor, and waste reduction.\n"
        "- Integrate the specific curriculum and experiments present in this laboratory:\n"
    )

    if 'principles' in curriculum:
        prompt += "\n### 12 Principles of Green Chemistry:\n"
        for p in curriculum['principles']:
            prompt += f"- Principle {p.get('id')} ({p.get('name')}): {p.get('description')}\n"

    if 'experiments' in curriculum:
        prompt += "\n### Laboratory Experiments in this Lab:\n"
        for exp in curriculum['experiments']:
            prompt += f"- Exp #{exp.get('id')} '{exp.get('name')}' ({exp.get('category')}): {exp.get('description')}\n"
            prompt += f"  Materials: {', '.join(exp.get('materials', []))}\n"
            prompt += f"  Green Highlights: {', '.join(exp.get('green_points', []))}\n"

    if 'safety' in curriculum:
        prompt += "\n### Safety & Emergency Guidelines:\n"
        prompt += "Rules:\n"
        for r in curriculum['safety'].get('rules', []):
            prompt += f"- {r}\n"
        prompt += "Emergency Protocols:\n"
        for em in curriculum['safety'].get('emergency', []):
            prompt += f"- {em}\n"

    if 'alternatives' in curriculum:
        prompt += "\n### Safer Chemical Alternatives:\n"
        for alt in curriculum['alternatives']:
            prompt += f"- Hazardous item: {alt.get('hazard')} -> Safer alternative: {alt.get('alternative')} (Benefit: {alt.get('benefit')})\n"

    prompt += (
        "\n### Waste Management Hierarchy:\n"
        "1. Prevention/Reduction: Employ microscale procedures and stoichiometric calculations.\n"
        "2. Segregation: Never mix incompatible wastes. Separate halogenated from non-halogenated solvents.\n"
        "3. Recovery & Recycling: Solvent recovery via closed distillation when safe.\n"
        "4. Safe Disposal: Always comply with institutional hazardous waste protocol.\n"
    )
    return prompt

def call_external_ai(messages):
    """
    Calls configured external AI API (OpenAI, Groq, OpenRouter, Gemini, or local models).
    Uses standard library urllib.
    """
    api_key = AI_API_KEY
    raw_url = AI_API_URL or 'https://api.openai.com/v1/chat/completions'
    model = AI_MODEL or 'gpt-4o-mini'

    # Support Google Gemini API if specified in URL
    if 'generativelanguage.googleapis.com' in raw_url:
        if not api_key:
            raise ValueError("AI_API_KEY is required for Google Gemini API")
        gemini_url = raw_url
        if 'generateContent' not in gemini_url:
            gemini_url = gemini_url.rstrip('/') + f"/models/{model}:generateContent?key={api_key}"
        elif 'key=' not in gemini_url:
            delim = '&' if '?' in gemini_url else '?'
            gemini_url += f"{delim}key={api_key}"

        gemini_contents = []
        for m in messages:
            role = 'user' if m['role'] in ('user', 'system') else 'model'
            gemini_contents.append({"role": role, "parts": [{"text": m['content']}]})

        payload = json.dumps({"contents": gemini_contents}).encode('utf-8')
        req = urllib.request.Request(gemini_url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            return res_data['candidates'][0]['content']['parts'][0]['text']

    # OpenAI-compatible endpoint (OpenAI, Groq, OpenRouter, DeepSeek, Ollama, etc.)
    url = raw_url
    if not url.endswith('/chat/completions'):
        if url.endswith('/v1') or url.endswith('/v1/'):
            url = url.rstrip('/') + '/chat/completions'
        elif '/chat/completions' not in url:
            url = url.rstrip('/') + '/chat/completions'

    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f"Bearer {api_key}"

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1200
    }).encode('utf-8')

    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=30) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        return res_data['choices'][0]['message']['content']

def educational_fallback(question, history=None):
    """
    Intelligent Green Chemistry educational engine.
    Handles principles, experiments, safety, waste management, and alternatives.
    """
    ql = question.lower().strip()
    curriculum = load_curriculum()

    # 1. Safer alternatives
    if 'alternative' in ql or 'substitut' in ql:
        alts = curriculum.get('alternatives', [])
        lines = [
            "### 🔄 Safer Alternatives in the Chemistry Laboratory\n\n"
            "Replacing hazardous reagents and toxic solvents is one of the highest-impact green strategies:\n"
        ]
        for alt in alts:
            lines.append(f"**Conventional Hazard:** {alt['hazard']}")
            lines.append(f"👉 **Green Alternative:** {alt['alternative']}")
            lines.append(f"💡 **Benefit:** {alt['benefit']}\n")
        lines.append("> *Solvent Selection Guide:* Water, ethanol, 2-MeTHF, and ethyl lactate are preferred 'green' solvents over hexane, benzene, or DCM.")
        return "\n".join(lines)

    # 2. Safety and emergency
    if 'safety' in ql or 'hazard' in ql or 'ppe' in ql or 'emergency' in ql or 'spill' in ql:
        safety_data = curriculum.get('safety', {})
        rules = safety_data.get('rules', [])
        emergency = safety_data.get('emergency', [])
        return (
            "### 🛡️ Laboratory Safety & Emergency Guidelines\n\n"
            "**Core Safety Practices:**\n" +
            "\n".join(f"- {r}" for r in rules) +
            "\n\n**Emergency Response Protocols:**\n" +
            "\n".join(f"- {em}" for em in emergency) +
            "\n\n> *Remember:* In case of any chemical incident, alert your lab instructor or supervisor immediately. Do not attempt unapproved cleanups alone."
        )

    # 3. Waste management
    if 'waste' in ql or 'disposal' in ql or 'segregat' in ql:
        return (
            "### ♻️ Green Chemical Waste Management\n\n"
            "Green waste management prioritizes **source reduction** followed by responsible handling:\n\n"
            "1. **Prevention & Minimization (Principle #1):**\n"
            "   - Conduct reactions on a microscale.\n"
            "   - Plan stoichiometric quantities rather than using vast excess.\n\n"
            "2. **Segregation Categories:**\n"
            "   - **Halogenated Organic Waste:** Dichloromethane, chloroform (separate strictly).\n"
            "   - **Non-Halogenated Organic Waste:** Ethanol, acetone, ethyl acetate.\n"
            "   - **Aqueous Waste:** Neutralized solutions free of heavy metals.\n"
            "   - **Heavy Metal Wastes:** Chromium, lead, copper solutions (kept isolated for specialized treatment).\n\n"
            "3. **Recovery & Reuse:**\n"
            "   - Distillation of spent solvents for reuse in washing or chromatography.\n"
            "   - Catalytic regeneration whenever possible.\n\n"
            "> *Safety Rule:* Never pour organic solvents or concentrated acids down the sink!"
        )

    # 4. Atom economy
    if 'atom economy' in ql:
        return (
            "### 🔬 Atom Economy (Principle #2)\n\n"
            "**Atom Economy** is a foundational metric in green chemistry that measures how efficiently "
            "reactant atoms are converted into the desired product, rather than wasted by-products.\n\n"
            "**Formula:**\n"
            "$$\\text{Atom Economy (\\%)} = \\frac{\\text{Formula Weight of Desired Product}}{\\text{Total Formula Weight of All Reactants}} \\times 100$$\n\n"
            "**Key Differences from Reaction Yield:**\n"
            "- **Yield** only measures the quantity of product isolated relative to theoretical yield.\n"
            "- **Atom Economy** evaluates intrinsic reaction efficiency — even a reaction with 100% yield can have poor atom economy if it generates bulky by-products (e.g. Wittig or Grignard reactions).\n\n"
            "**Examples:**\n"
            "- **100% Atom Economy:** Addition reactions (e.g., hydrogenation, Diels-Alder cycloadditions).\n"
            "- **Low Atom Economy:** Elimination or substitution reactions generating stoichiometric inorganic salts.\n\n"
            "> *Green Tip:* Always aim for addition or catalytic rearrangement steps whenever designing a synthesis!"
        )

    # 5. 12 Principles inquiry
    if 'principle' in ql or '12 principles' in ql:
        principles_list = curriculum.get('principles', [])
        lines = ["### 🌱 The 12 Principles of Green Chemistry (Anastas & Warner)\n"]
        for p in principles_list:
            lines.append(f"**{p['id']}. {p['name']}**: {p['description']}")
        lines.append("\n> *Summary:* The overarching goal of these principles is **hazard reduction**, **resource conservation**, and **waste prevention** at every stage of the chemical life-cycle.")
        return "\n".join(lines)

    # 6. Specific experiment inquiries
    experiments = curriculum.get('experiments', [])
    exp_keywords = {
        1: ['esterification', 'ester', 'experiment 1', 'exp 1', 'exp #1'],
        2: ['aldol', 'solvent-free aldol', 'experiment 2', 'exp 2', 'exp #2'],
        3: ['indicator', 'cabbage', 'natural indicator', 'acid-base indicator', 'experiment 3', 'exp 3', 'exp #3'],
        4: ['microscale', 'micro-scale', 'experiment 4', 'exp 4', 'exp #4']
    }
    for exp in experiments:
        eid = exp.get('id')
        keys = exp_keywords.get(eid, [])
        if any(k in ql for k in keys):
            return (
                f"### 🧪 Experiment #{exp['id']}: {exp['name']}\n\n"
                f"**Category:** {exp.get('category')}\n"
                f"**Description:** {exp.get('description')}\n\n"
                f"**Key Materials:**\n" + "\n".join(f"- {m}" for m in exp.get('materials', [])) + "\n\n"
                f"**Green Chemistry Highlights:**\n" + "\n".join(f"- {g}" for g in exp.get('green_points', [])) + "\n\n"
                f"**Procedure Steps:**\n" + "\n".join(f"{idx+1}. {step}" for idx, step in enumerate(exp.get('procedure', []))) + "\n\n"
                "> *Lab Best Practice:* Review material safety data sheets (SDS) and pre-calculate stoichiometric ratios before beginning."
            )

    # 7. General experiments
    if 'experiment' in ql or 'lab work' in ql:
        items = ["### 🧪 Available Green Chemistry Experiments in this Lab:\n"]
        for exp in experiments:
            items.append(f"**{exp['id']}. {exp['name']}** ({exp['category']})")
            items.append(f"   - *Concept:* {exp['description']}")
            items.append(f"   - *Green Advantage:* {', '.join(exp.get('green_points', []))}\n")
        items.append("Ask about any specific experiment (e.g. *'Tell me about the Solvent-Free Aldol reaction'*) for complete procedures and safety details!")
        return "\n".join(items)

    # 8. Catalysis
    if 'cataly' in ql:
        return (
            "### ⚡ Catalysis (Principle #9)\n\n"
            "**Catalytic reagents are vastly superior to stoichiometric reagents:**\n\n"
            "- **Lower Energy Barriers:** Catalysts lower activation energy ($E_a$), allowing reactions to occur at ambient temperatures and pressures.\n"
            "- **Reduced Waste:** Stoichiometric reagents are consumed and produce equivalent molar waste; catalysts are regenerated and used in sub-stoichiometric amounts (0.1 - 5 mol%).\n"
            "- **Selectivity:** Enzymes and specialized metal complexes can achieve high chemo-, regio-, and enantioselectivity, preventing unwanted by-products."
        )


    # Default educational response
    note = ""
    if not AI_API_KEY:
        note = "\n\n*(💡 AI Configuration Tip: You can connect live cloud AI models such as OpenAI, Groq, or Gemini anytime by setting `AI_API_KEY`, `AI_API_URL`, and `AI_MODEL` in `.env`)*."

    return (
        f"### 🌱 Green Chemistry Educational Assistant\n\n"
        f"I'm here to assist you with any green chemistry topic, lab experiment, or sustainable practice!\n\n"
        f"**Areas you can ask about:**\n"
        f"- **12 Principles:** Ask about atom economy, prevention, catalysis, or renewable feedstocks.\n"
        f"- **Lab Experiments:** Ask for procedures and green analysis for *Esterification*, *Solvent-Free Aldol*, *Natural Indicator*, or *Microscale Reactions*.\n"
        f"- **Safety & PPE:** Ask about lab hazards, eye-wash protocols, and safe chemical handling.\n"
        f"- **Waste Management:** Ask how to segregate chemical waste or reduce laboratory footprint.\n"
        f"- **Safer Alternatives:** Ask for green solvent replacements or safer reagent substitutes.\n\n"
        f"**Your Question:** *\"{question}\"*\n\n"
        f"To get started, try asking: *\"Explain the atom economy formula\"* or *\"How do we handle chemical waste in the lab?\"*{note}"
    )

@bp.post('/assistant')
def assistant():
    if 'user_id' not in session:
        return jsonify(error='Login required. Please login to use the AI Assistant.'), 401

    data = request.json or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify(error='Message required'), 400

    user_id = session['user_id']

    # Record activity in history and dashboard stats
    try:
        c = connect()
        c.execute('INSERT INTO activity(user_id, type) VALUES(?, ?)', (user_id, 'AI question'))
        c.commit()
        c.close()
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

    # Persist user message to chat history
    try:
        save_chat_message(user_id, 'user', message)
    except Exception as e:
        logger.error(f"Error saving user chat message: {e}")

    # Retrieve previous conversation turns for multi-turn context
    context_rows = []
    try:
        context_rows = get_chat_history(user_id, limit=16)
    except Exception as e:
        logger.error(f"Error fetching chat history context: {e}")

    # Build prompt and messages
    system_prompt = build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]

    for r in context_rows:
        role = 'assistant' if r['role'] == 'assistant' else 'user'
        messages.append({"role": role, "content": r['content']})

    # Execute AI call
    answer = None
    if AI_API_KEY or (AI_API_URL and ('localhost' in AI_API_URL or '127.0.0.1' in AI_API_URL)):
        try:
            answer = call_external_ai(messages)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            logger.error(f"AI API HTTP Error {e.code}: {err_body}")
            answer = (
                f"⚠️ **AI API Status ({e.code})**: Remote service reported `{err_body[:180]}`.\n\n"
                f"**Green Chemistry Guidance:**\n\n" + educational_fallback(message, context_rows)
            )
        except Exception as e:
            logger.error(f"AI API Connection Error: {e}")
            answer = (
                f"⚠️ **AI Connection Notice**: Could not reach remote AI endpoint ({str(e)}).\n\n"
                f"**Green Chemistry Guidance:**\n\n" + educational_fallback(message, context_rows)
            )

    if not answer:
        answer = educational_fallback(message, context_rows)

    # Persist assistant response to chat history
    from datetime import datetime
    now_str = datetime.now().strftime("%I:%M %p")
    try:
        save_chat_message(user_id, 'assistant', answer)
    except Exception as e:
        logger.error(f"Error saving assistant chat message: {e}")

    return jsonify(answer=answer, created_at=now_str)

@bp.get('/assistant/history')
def get_history():
    if 'user_id' not in session:
        return jsonify(error='Login required'), 401
    user_id = session['user_id']
    try:
        history = get_chat_history(user_id, limit=80)
        return jsonify(history=history)
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.delete('/assistant/history')
def clear_history():
    if 'user_id' not in session:
        return jsonify(error='Login required'), 401
    user_id = session['user_id']
    try:
        clear_chat_history(user_id)
        return jsonify(message='Chat history cleared successfully')
    except Exception as e:
        return jsonify(error=str(e)), 500
