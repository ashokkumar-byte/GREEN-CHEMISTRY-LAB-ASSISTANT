from flask import Blueprint, jsonify, session
from database import connect, get_user_reports, get_report_by_id

bp = Blueprint('reports', __name__)

@bp.get('/reports')
def list_reports():
    if 'user_id' not in session:
        return jsonify(error='Login required'), 401
    reports = get_user_reports(session['user_id'])
    return jsonify(reports=reports)

@bp.get('/reports/<int:rep_id>')
def view_report(rep_id):
    if 'user_id' not in session:
        return jsonify(error='Login required'), 401
    rep = get_report_by_id(rep_id, session['user_id'])
    if not rep:
        return jsonify(error='Report not found'), 404
    return jsonify(report=rep)

@bp.delete('/reports/<int:rep_id>')
def delete_report(rep_id):
    if 'user_id' not in session:
        return jsonify(error='Login required'), 401
    c = connect()
    c.execute("DELETE FROM reports WHERE id=? AND user_id=?", (rep_id, session['user_id']))
    c.commit()
    c.close()
    return jsonify(message='Report deleted successfully')
