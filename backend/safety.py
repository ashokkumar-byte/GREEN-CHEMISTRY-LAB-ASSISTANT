import json
from flask import Blueprint,jsonify
from config import DATA_DIR
bp=Blueprint('safety',__name__)
@bp.get('/safety')
def get_safety():return jsonify(json.loads((DATA_DIR/'safety.json').read_text()))
