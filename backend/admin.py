import json
from functools import wraps
from flask import Blueprint, request, jsonify, session
from database import connect, valid_password, get_user

bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify(error='Admin privilege required'), 403
        return f(*args, **kwargs)
    return decorated

@bp.post('/admin/login')
def admin_login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = get_user(username)
    if not user or not valid_password(user, password):
        return jsonify(error='Invalid admin credentials'), 401

    if not user['is_admin']:
        return jsonify(error='Access denied: not an administrator account'), 403

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['is_admin'] = 1
    return jsonify(message='Admin logged in successfully', username=user['username'])

@bp.post('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return jsonify(message='Admin logged out')

@bp.get('/admin/me')
def admin_me():
    if not session.get('is_admin'):
        return jsonify(error='Not logged in as admin'), 401
    return jsonify(is_admin=True, username=session.get('username', 'admin'))

@bp.get('/admin/stats')
@admin_required
def admin_stats():
    c = connect()
    u = c.execute("SELECT COUNT(*) n FROM users").fetchone()['n']
    e = c.execute("SELECT COUNT(*) n FROM experiments").fetchone()['n']
    q = c.execute("SELECT COUNT(*) n FROM quiz_questions").fetchone()['n']
    p = c.execute("SELECT COUNT(*) n FROM practical_attempts").fetchone()['n']
    r = c.execute("SELECT COUNT(*) n FROM reports").fetchone()['n']
    c.close()
    return jsonify(users=u, experiments=e, questions=q, practicals=p, reports=r)

# --- Experiment Management ---
@bp.get('/admin/experiments')
@admin_required
def admin_get_experiments():
    c = connect()
    rows = c.execute("SELECT id, name, category, difficulty, safety_level, description FROM experiments ORDER BY id ASC").fetchall()
    c.close()
    return jsonify(experiments=[dict(r) for r in rows])

@bp.post('/admin/experiments')
@admin_required
def admin_add_experiment():
    data = request.json or {}
    name = data.get('name', '').strip()
    category = data.get('category', 'Organic Chemistry').strip()
    difficulty = data.get('difficulty', 'Beginner').strip()
    safety_level = data.get('safety_level', 'Low').strip()
    description = data.get('description', '').strip()
    aim = data.get('aim', '').strip() or description
    waste_generated = data.get('waste_generated', 'Minimal chemical waste.')
    waste_management = data.get('waste_management', 'Follow standard neutralization and segregation procedures.')

    if not name or not description:
        return jsonify(error='Name and description are required'), 400

    principles = json.dumps(data.get('principles', ["Prevention", "Atom Economy"]))
    materials = json.dumps(data.get('materials', ["Standard lab reagents"]))
    apparatus = json.dumps(data.get('apparatus', ["Standard lab glassware"]))
    chemicals = json.dumps(data.get('chemicals', ["Standard reagents"]))
    safety_precautions = json.dumps(data.get('safety_precautions', ["Wear appropriate PPE."]))
    procedure = json.dumps(data.get('procedure', ["Measure reagents carefully.", "Observe reactions safely."]))
    green_points = json.dumps(data.get('green_points', ["Waste prevention."]))
    alternatives = json.dumps(data.get('alternatives', ["Safer solvent alternatives."]))
    interactive_steps = json.dumps(data.get('interactive_steps', [
        {"step": 1, "title": "Setup", "instruction": "Prepare reagents.", "action_name": "Mix", "feedback": "Step completed."}
    ]))

    c = connect()
    cur = c.execute("""
    INSERT INTO experiments(name, category, difficulty, safety_level, principles, description,
        aim, materials, apparatus, chemicals, safety_precautions, procedure,
        interactive_steps, green_points, waste_generated, waste_management, alternatives)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (name, category, difficulty, safety_level, principles, description,
          aim, materials, apparatus, chemicals, safety_precautions, procedure,
          interactive_steps, green_points, waste_generated, waste_management, alternatives))
    exp_id = cur.lastrowid
    c.commit()
    c.close()
    return jsonify(message='Experiment created', id=exp_id)

@bp.delete('/admin/experiments/<int:eid>')
@admin_required
def admin_delete_experiment(eid):
    c = connect()
    c.execute("DELETE FROM experiments WHERE id=?", (eid,))
    c.commit()
    c.close()
    return jsonify(message='Experiment deleted')

# --- User Management ---
@bp.get('/admin/users')
@admin_required
def admin_get_users():
    c = connect()
    rows = c.execute("SELECT id, name, username, email, is_admin, created_at FROM users ORDER BY id ASC").fetchall()
    c.close()
    return jsonify(users=[dict(r) for r in rows])

@bp.delete('/admin/users/<int:uid>')
@admin_required
def admin_delete_user(uid):
    if uid == session.get('user_id'):
        return jsonify(error='Cannot delete currently authenticated administrator'), 400
    c = connect()
    c.execute("DELETE FROM users WHERE id=?", (uid,))
    c.commit()
    c.close()
    return jsonify(message='User deleted')

# --- Quiz Management ---
@bp.get('/admin/quiz')
@admin_required
def admin_get_quiz():
    c = connect()
    rows = c.execute("SELECT id, question, option_a, option_b, option_c, option_d, correct_answer, topic, difficulty FROM quiz_questions ORDER BY id DESC").fetchall()
    c.close()
    return jsonify(questions=[dict(r) for r in rows])

@bp.post('/admin/quiz')
@admin_required
def admin_add_quiz():
    data = request.json or {}
    q = data.get('question', '').strip()
    a = data.get('option_a', '').strip()
    b = data.get('option_b', '').strip()
    cc = data.get('option_c', '').strip()
    d = data.get('option_d', '').strip()
    ans = data.get('correct_answer', '').strip()
    topic = data.get('topic', '12 Principles').strip()
    difficulty = data.get('difficulty', 'Medium').strip()
    expl = data.get('explanation', '').strip()

    if not all([q, a, b, cc, d, ans]):
        return jsonify(error='All question text, options and correct answer are required'), 400

    c = connect()
    cur = c.execute("""
    INSERT INTO quiz_questions(question, option_a, option_b, option_c, option_d, correct_answer, explanation, topic, difficulty)
    VALUES (?,?,?,?,?,?,?,?,?)
    """, (q, a, b, cc, d, ans, expl, topic, difficulty))
    qid = cur.lastrowid
    c.commit()
    c.close()
    return jsonify(message='Question added', id=qid)

@bp.delete('/admin/quiz/<int:qid>')
@admin_required
def admin_delete_quiz(qid):
    c = connect()
    c.execute("DELETE FROM quiz_questions WHERE id=?", (qid,))
    c.commit()
    c.close()
    return jsonify(message='Question deleted')
