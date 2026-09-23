import json
from flask import Blueprint, jsonify, request
from database import connect

bp = Blueprint('experiments', __name__)

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

@bp.get('/experiments')
def all_experiments():
    q = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    principle = request.args.get('principle', '').strip()

    c = connect()
    rows = c.execute("SELECT * FROM experiments ORDER BY id ASC").fetchall()
    c.close()

    result = []
    for r in rows:
        d = dict(r)
        d['principles'] = parse_json_safely(d.get('principles'))
        d['materials'] = parse_json_safely(d.get('materials'))
        d['apparatus'] = parse_json_safely(d.get('apparatus'))
        d['chemicals'] = parse_json_safely(d.get('chemicals'))
        d['safety_precautions'] = parse_json_safely(d.get('safety_precautions'))
        d['procedure'] = parse_json_safely(d.get('procedure'))
        d['green_points'] = parse_json_safely(d.get('green_points'))
        d['alternatives'] = parse_json_safely(d.get('alternatives'))

        # Filters
        if category and category.lower() != 'all' and d['category'].lower() != category.lower():
            continue
        if difficulty and difficulty.lower() != 'all' and d['difficulty'].lower() != difficulty.lower():
            continue
        if principle and principle.lower() != 'all':
            p_match = any(principle.lower() in p.lower() for p in d['principles'])
            if not p_match:
                continue
        if q:
            text_corpus = f"{d['name']} {d['category']} {d['description']} {' '.join(d['materials'])} {' '.join(d['principles'])}".lower()
            if q not in text_corpus:
                continue

        result.append(d)

    return jsonify(experiments=result, total=len(result))

@bp.get('/experiments/<int:eid>')
def one(eid):
    c = connect()
    row = c.execute("SELECT * FROM experiments WHERE id=?", (eid,)).fetchone()
    c.close()
    if not row:
        return jsonify(error='Experiment not found'), 404

    d = dict(row)
    d['principles'] = parse_json_safely(d.get('principles'))
    d['materials'] = parse_json_safely(d.get('materials'))
    d['apparatus'] = parse_json_safely(d.get('apparatus'))
    d['chemicals'] = parse_json_safely(d.get('chemicals'))
    d['safety_precautions'] = parse_json_safely(d.get('safety_precautions'))
    d['procedure'] = parse_json_safely(d.get('procedure'))
    d['interactive_steps'] = parse_json_safely(d.get('interactive_steps'))
    d['green_points'] = parse_json_safely(d.get('green_points'))
    d['alternatives'] = parse_json_safely(d.get('alternatives'))

    return jsonify(experiment=d)
