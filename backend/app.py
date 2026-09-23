from flask import Flask, jsonify, send_from_directory, session, request
from pathlib import Path
from config import SECRET_KEY, BASE_DIR
from database import init_db, connect
from auth import bp as auth_bp
from experiments import bp as experiments_bp
from assistant import bp as assistant_bp
from safety import bp as safety_bp
from quiz import bp as quiz_bp
from practicals import bp as practicals_bp
from reports import bp as reports_bp
from admin import bp as admin_bp

app = Flask(__name__, static_folder=str(BASE_DIR / 'frontend'), static_url_path='')
app.secret_key = SECRET_KEY

init_db()

# Register API Blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(experiments_bp, url_prefix='/api')
app.register_blueprint(assistant_bp, url_prefix='/api')
app.register_blueprint(safety_bp, url_prefix='/api')
app.register_blueprint(quiz_bp, url_prefix='/api')
app.register_blueprint(practicals_bp, url_prefix='/api')
app.register_blueprint(reports_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')

@app.get('/api/health')
def health():
    return jsonify(status='ok', message='Green Chemistry platform backend is running')

@app.errorhandler(415)
def unsupported_media_type(e):
    return jsonify(error='Request must use Content-Type: application/json'), 415

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error='Internal server error', details=str(e)), 500


@app.get('/api/stats')
def stats():
    if 'user_id' not in session:
        return jsonify(error='Login required'), 401

    uid = session['user_id']
    c = connect()
    rep_count = c.execute('SELECT COUNT(*) n FROM reports WHERE user_id=?', (uid,)).fetchone()['n']
    prac_count = c.execute('SELECT COUNT(*) n FROM practical_attempts WHERE user_id=?', (uid,)).fetchone()['n']
    quiz_count = c.execute('SELECT COUNT(*) n FROM quiz_attempts WHERE user_id=?', (uid,)).fetchone()['n']
    quiz_avg_row = c.execute('SELECT AVG(percentage) a FROM quiz_attempts WHERE user_id=?', (uid,)).fetchone()
    avg_quiz_score = round(quiz_avg_row['a'] or 0.0, 1)
    total_exps = c.execute('SELECT COUNT(*) n FROM experiments').fetchone()['n']

    # Real progress calculation
    learning_progress = min(100, int((prac_count * 25) + (quiz_count * 15) + (rep_count * 10)))
    if learning_progress == 0 and (prac_count > 0 or quiz_count > 0):
        learning_progress = 10

    recent_rows = c.execute(
        'SELECT type, details, created_at FROM activity WHERE user_id=? ORDER BY id DESC LIMIT 8',
        (uid,)
    ).fetchall()
    c.close()

    return jsonify(
        reports=rep_count,
        practicals=prac_count,
        quizzes=quiz_count,
        avg_quiz_score=avg_quiz_score,
        experiments=total_exps,
        learning_progress=learning_progress,
        recent_activity=[dict(r) for r in recent_rows]
    )

@app.get('/api/history')
def history():
    if 'user_id' not in session:
        return jsonify(error='Login required'), 401

    uid = session['user_id']
    c = connect()
    rows = c.execute(
        'SELECT id, type, details, created_at FROM activity WHERE user_id=? ORDER BY id DESC LIMIT 100',
        (uid,)
    ).fetchall()
    practicals = c.execute(
        'SELECT id, experiment_name, status, created_at FROM practical_attempts WHERE user_id=? ORDER BY id DESC LIMIT 50',
        (uid,)
    ).fetchall()
    quizzes = c.execute(
        'SELECT id, topic, difficulty, score, total_questions, percentage, created_at FROM quiz_attempts WHERE user_id=? ORDER BY id DESC LIMIT 50',
        (uid,)
    ).fetchall()
    reports = c.execute(
        'SELECT id, title, practical_id, created_at FROM reports WHERE user_id=? ORDER BY id DESC LIMIT 50',
        (uid,)
    ).fetchall()
    c.close()

    return jsonify(
        items=[dict(x) for x in rows],
        practicals=[dict(x) for x in practicals],
        quizzes=[dict(x) for x in quizzes],
        reports=[dict(x) for x in reports]
    )

# --- Admin Static Files Serving ---
@app.route('/admin')
@app.route('/admin/')
def admin_root():
    return send_from_directory(str(BASE_DIR / 'admin'), 'admin-dashboard.html')

@app.route('/admin/<path:path>')
def admin_static(path):
    admin_folder = BASE_DIR / 'admin'
    p = admin_folder / path
    if p.is_file():
        return send_from_directory(str(admin_folder), path)
    return send_from_directory(str(admin_folder), 'admin-dashboard.html')

# --- Frontend Static Files Serving ---
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_page(path):
    p = Path(app.static_folder) / path
    if p.is_file():
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
