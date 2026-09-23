import json
import random
from flask import Blueprint, request, jsonify, session
from database import connect, save_quiz_attempt, get_user_quiz_attempts

bp = Blueprint('quiz', __name__)

@bp.get('/quiz/topics')
def get_topics():
    c = connect()
    topics_rows = c.execute("SELECT DISTINCT topic, COUNT(*) as count FROM quiz_questions GROUP BY topic").fetchall()
    diff_rows = c.execute("SELECT DISTINCT difficulty FROM quiz_questions").fetchall()
    c.close()

    topics = [{"name": r["topic"], "count": r["count"]} for r in topics_rows]
    difficulties = [r["difficulty"] for r in diff_rows]
    return jsonify(topics=topics, difficulties=difficulties)

@bp.get('/quiz/questions')
def get_questions():
    topic = request.args.get('topic', 'all').strip()
    difficulty = request.args.get('difficulty', 'all').strip()
    try:
        count = min(int(request.args.get('count', 5)), 10)
    except (ValueError, TypeError):
        count = 5

    c = connect()
    query = "SELECT id, question, option_a, option_b, option_c, option_d, topic, difficulty FROM quiz_questions WHERE 1=1"
    params = []

    if topic and topic.lower() != 'all':
        query += " AND topic=?"
        params.append(topic)
    if difficulty and difficulty.lower() != 'all':
        query += " AND difficulty=?"
        params.append(difficulty)

    rows = c.execute(query, params).fetchall()
    c.close()

    if not rows:
        # Fallback to any questions
        c = connect()
        rows = c.execute("SELECT id, question, option_a, option_b, option_c, option_d, topic, difficulty FROM quiz_questions").fetchall()
        c.close()

    selected_rows = list(rows)
    random.shuffle(selected_rows)
    selected_rows = selected_rows[:count]

    questions = []
    for r in selected_rows:
        opts = [r['option_a'], r['option_b'], r['option_c'], r['option_d']]
        random.shuffle(opts)
        questions.append({
            "id": r['id'],
            "question": r['question'],
            "options": opts,
            "topic": r['topic'],
            "difficulty": r['difficulty']
        })

    return jsonify(questions=questions, total=len(questions))

@bp.post('/quiz/submit')
def submit_quiz():
    if 'user_id' not in session:
        return jsonify(error='Login required to save quiz attempts'), 401

    data = request.json or {}
    answers = data.get('answers', {})
    topic = data.get('topic', 'General Green Chemistry')
    difficulty = data.get('difficulty', 'Mixed')

    if not answers:
        return jsonify(error='No answers provided'), 400

    q_ids = list(answers.keys())
    c = connect()
    placeholders = ','.join('?' for _ in q_ids)
    rows = c.execute(f"SELECT id, question, correct_answer, explanation FROM quiz_questions WHERE id IN ({placeholders})", q_ids).fetchall()
    c.close()

    db_map = {str(r['id']): dict(r) for r in rows}
    score = 0
    total = len(q_ids)
    review = []

    for qid_str, user_ans in answers.items():
        q_info = db_map.get(str(qid_str))
        if not q_info:
            continue
        is_correct = (str(user_ans).strip().lower() == str(q_info['correct_answer']).strip().lower())
        if is_correct:
            score += 1
        review.append({
            "id": int(qid_str),
            "question": q_info['question'],
            "selected": user_ans,
            "correct_answer": q_info['correct_answer'],
            "is_correct": is_correct,
            "explanation": q_info.get('explanation', '')
        })

    percentage = (score / total * 100.0) if total > 0 else 0.0

    attempt_id = save_quiz_attempt(
        user_id=session['user_id'],
        topic=topic,
        difficulty=difficulty,
        score=score,
        total_questions=total,
        percentage=percentage,
        correct_answers=score,
        review_json=json.dumps(review)
    )

    return jsonify(
        attempt_id=attempt_id,
        score=score,
        total_questions=total,
        percentage=round(percentage, 1),
        review=review
    )

@bp.get('/quiz/attempts')
def get_attempts():
    if 'user_id' not in session:
        return jsonify(error='Login required'), 401
    attempts = get_user_quiz_attempts(session['user_id'])
    return jsonify(attempts=attempts)
