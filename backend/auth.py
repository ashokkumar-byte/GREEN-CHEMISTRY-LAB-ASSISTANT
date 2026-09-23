from flask import Blueprint,request,jsonify,session
from database import create_user,get_user,valid_password,connect
bp=Blueprint('auth',__name__)
@bp.post('/register')
def register():
 d=request.json or {}; name=d.get('name','').strip();u=d.get('username','').strip();e=d.get('email','').strip();p=d.get('password','')
 if not all([name,u,e,p]): return jsonify(error='All fields are required'),400
 if len(p)<6:return jsonify(error='Password must be at least 6 characters'),400
 try:create_user(name,u,e,p)
 except Exception:return jsonify(error='Username already exists'),409
 return jsonify(message='registered')
@bp.post('/login')
def login():
 d=request.json or {};r=get_user(d.get('username',''))
 if not valid_password(r,d.get('password','')):return jsonify(error='Invalid username or password'),401
 session['user_id']=r['id'];return jsonify(message='logged in')
@bp.post('/logout')
def logout():session.clear();return jsonify(message='logged out')
@bp.get('/me')
def me():
 if 'user_id' not in session:return jsonify(error='Login required'),401
 c=connect();r=c.execute('SELECT id,name,username,email,created_at FROM users WHERE id=?',(session['user_id'],)).fetchone();c.close();return jsonify(user=dict(r))
@bp.put('/profile')
def profile():
 if 'user_id' not in session:return jsonify(error='Login required'),401
 d=request.json or {};c=connect();c.execute('UPDATE users SET name=?,email=? WHERE id=?',(d.get('name','').strip(),d.get('email','').strip(),session['user_id']));c.commit();c.close();return jsonify(message='updated')
