import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from database import connect, save_practical_attempt, get_user_practical_attempts, save_report, get_user_by_id

bp = Blueprint('practicals', __name__)

def parse_json_safely(val, fallback=None):
    if fallback is None:
        fallback = []
    if not val:
        return fallback
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return fallback

def read_text_field(data, key, fallback):
    value = data.get(key)
    if value is None:
        return fallback
    if not isinstance(value, str):
        raise ValueError(f'{key} must be text')
    return value.strip() or fallback

@bp.get('/practicals/<int:exp_id>')
def get_practical(exp_id):
    c = connect()
    row = c.execute("SELECT * FROM experiments WHERE id=?", (exp_id,)).fetchone()
    c.close()
    if not row:
        return jsonify(error='Experiment not found'), 404

    d = dict(row)
    d['principles'] = parse_json_safely(d.get('principles'), [])
    d['materials'] = parse_json_safely(d.get('materials'), [])
    d['apparatus'] = parse_json_safely(d.get('apparatus'), [])
    d['chemicals'] = parse_json_safely(d.get('chemicals'), [])
    d['safety_precautions'] = parse_json_safely(d.get('safety_precautions'), [])
    d['procedure'] = parse_json_safely(d.get('procedure'), [])
    d['interactive_steps'] = parse_json_safely(d.get('interactive_steps'), [])
    d['green_points'] = parse_json_safely(d.get('green_points'), [])
    d['alternatives'] = parse_json_safely(d.get('alternatives'), [])

    return jsonify(practical=d)

@bp.post('/practicals/submit')
def submit_practical():
    if 'user_id' not in session:
        return jsonify(error='Login required to submit practicals'), 401

    data = request.get_json(force=True, silent=True) or {}
    exp_id = data.get('experiment_id')
    if isinstance(exp_id, bool) or not isinstance(exp_id, (int, str)) or not str(exp_id).strip():
        return jsonify(error='Experiment ID is required'), 400
    try:
        exp_id = int(exp_id)
    except (TypeError, ValueError):
        return jsonify(error='Experiment ID must be a valid number'), 400

    c = connect()
    exp_row = c.execute("SELECT * FROM experiments WHERE id=?", (exp_id,)).fetchone()
    c.close()

    if not exp_row:
        return jsonify(error='Experiment not found'), 404

    user = get_user_by_id(session['user_id'])
    if not user:
        return jsonify(error='User profile not found'), 404

    try:
        observations = read_text_field(data, 'observations', 'No specific observations recorded.')
        result = read_text_field(data, 'result', 'Reaction conducted in accordance with green chemistry principles.')
        conclusion = read_text_field(data, 'conclusion', 'The practical successfully satisfied targeted green chemistry metrics.')
        waste_info = read_text_field(data, 'waste_info', exp_row['waste_management'])
    except ValueError as error:
        return jsonify(error=str(error)), 400

    # Save practical attempt
    prac_id = save_practical_attempt(
        user_id=session['user_id'],
        experiment_id=exp_id,
        experiment_name=exp_row['name'],
        observations=observations,
        result=result,
        conclusion=conclusion,
        waste_info=waste_info
    )

    # Auto-generate college-grade structured Laboratory Record Report
    now_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    report_title = f"Laboratory Record: {exp_row['name']}"

    report_content = {
        "student_name": user['name'],
        "student_username": user['username'],
        "student_email": user['email'],
        "date": now_str,
        "experiment_id": exp_id,
        "experiment_name": exp_row['name'],
        "category": exp_row['category'],
        "difficulty": exp_row['difficulty'],
        "safety_level": exp_row['safety_level'],
        "aim": exp_row['aim'] or exp_row['description'],
        "principles": parse_json_safely(exp_row['principles']),
        "materials": parse_json_safely(exp_row['materials']),
        "apparatus": parse_json_safely(exp_row['apparatus']),
        "chemicals": parse_json_safely(exp_row['chemicals']),
        "safety_precautions": parse_json_safely(exp_row['safety_precautions']),
        "procedure": parse_json_safely(exp_row['procedure']),
        "observations": observations,
        "result": result,
        "conclusion": conclusion,
        "waste_generated": exp_row['waste_generated'],
        "waste_management": waste_info,
        "green_points": parse_json_safely(exp_row['green_points']),
        "alternatives": parse_json_safely(exp_row['alternatives'])
    }

    report_id = save_report(
        user_id=session['user_id'],
        practical_id=prac_id,
        experiment_id=exp_id,
        title=report_title,
        content_dict=report_content
    )

    return jsonify(
        message='Practical completed and laboratory report generated successfully',
        practical_id=prac_id,
        report_id=report_id
    )

@bp.get('/practicals/attempts')
def get_attempts():
    if 'user_id' not in session:
        return jsonify(error='Login required'), 401
    attempts = get_user_practical_attempts(session['user_id'])
    return jsonify(practicals=attempts)
