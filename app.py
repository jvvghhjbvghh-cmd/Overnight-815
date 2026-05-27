import os
import shutil
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

os.system('') 

app = Flask(__name__)
app.secret_key = 'garaxy_811_super_secret_key_neon'

# ==========================================
ADMIN_USERNAME = 'GARAXY 811'
ADMIN_PASSWORD = 'Realsun 211105'
# ==========================================

# --- ส่วนที่เพิ่มเข้ามาเพื่อแก้ปัญหา Vercel 500 Error ---
# เช็คว่าระบบกำลังรันอยู่บน Vercel หรือไม่ (Vercel จะมีตัวแปร VERCEL ใน Environment)
IS_VERCEL = 'VERCEL' in os.environ
# ถ้าใช่ ให้ใช้โฟลเดอร์ /tmp ที่อนุญาตให้เขียนไฟล์ได้ชั่วคราว
DB_PATH = '/tmp/garaxy.db' if IS_VERCEL else 'garaxy.db'
# ---------------------------------------------------

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = f"""\033[95m
    ██████╗  █████╗ ██████╗  █████╗ ██╗  ██╗██╗   ██╗
    ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗╚██╗██╔╝╚██╗ ██╔╝
    ██║  ███╗███████║██████╔╝███████║ ╚███╔╝  ╚████╔╝ 
    ██║   ██║██╔══██║██╔══██╗██╔══██║ ██╔██╗   ╚██╔╝  
    ╚██████╔╝██║  ██║██║  ██║██║  ██║██╔╝ ██╗   ██║   
     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   \033[0m
    """
    print(banner)
    print(f"\033[96m[*] System Initialized Successfully\033[0m")
    print(f"\033[93m[*] Admin Account : {ADMIN_USERNAME}\033[0m")
    print(f"\033[92m[*] Server is running on http://127.0.0.1:5000\033[0m\n")

@app.after_request
def custom_logger(response):
    method_color = '\033[94m' if request.method == 'GET' else '\033[93m'
    status_color = '\033[92m' if response.status_code == 200 else '\033[91m'
    print(f"\033[90m[LOG]\033[0m {method_color}{request.method}\033[0m {request.path} -> {status_color}{response.status_code}\033[0m")
    return response

def get_db():
    # ถ้าอยู่บน Vercel และยังไม่มีไฟล์ DB ใน /tmp ให้ก๊อปปี้จากต้นฉบับมาใช้
    if IS_VERCEL and not os.path.exists(DB_PATH):
        if os.path.exists('garaxy.db'):
            shutil.copy2('garaxy.db', DB_PATH)
            
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, ig TEXT, category TEXT, avatar TEXT, is_fav INTEGER)')
        admin = conn.execute('SELECT * FROM admin WHERE username = ?', (ADMIN_USERNAME,)).fetchone()
        hashed_pw = generate_password_hash(ADMIN_PASSWORD)
        
        if not admin:
            conn.execute('INSERT INTO admin (username, password) VALUES (?, ?)', (ADMIN_USERNAME, hashed_pw))
        else:
            conn.execute('UPDATE admin SET password = ? WHERE username = ?', (hashed_pw, ADMIN_USERNAME))
            
        conn.commit()

init_db()

@app.route('/')
def welcome():
    return render_template('enter.html')

@app.route('/system')
def index():
    return render_template('index.html')

@app.route('/api/auth/status')
def auth_status():
    return jsonify({'isAdmin': session.get('is_admin', False)})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    with get_db() as conn:
        admin = conn.execute('SELECT * FROM admin WHERE username = ?', (data['username'],)).fetchone()
        
        if admin and check_password_hash(admin['password'], data['password']):
            session['is_admin'] = True
            return jsonify({'success': True})
            
    return jsonify({'success': False, 'message': 'Username หรือ Password ไม่ถูกต้อง!'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('is_admin', None)
    return jsonify({'success': True})

@app.route('/api/users', methods=['GET'])
def get_users():
    with get_db() as conn:
        users = conn.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    return jsonify([dict(u) for u in users])

@app.route('/api/users', methods=['POST'])
def add_user():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    with get_db() as conn:
        cur = conn.execute('INSERT INTO users (name, ig, category, avatar, is_fav) VALUES (?, ?, ?, ?, 0)',
                           (data['name'], data['ig'], data['category'], data['avatar']))
        conn.commit()
        return jsonify({'success': True, 'id': cur.lastrowid})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    with get_db() as conn:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/fav', methods=['POST'])
def toggle_fav(user_id):
    with get_db() as conn:
        user = conn.execute('SELECT is_fav FROM users WHERE id = ?', (user_id,)).fetchone()
        new_fav = 0 if user['is_fav'] == 1 else 1
        conn.execute('UPDATE users SET is_fav = ? WHERE id = ?', (new_fav, user_id))
        conn.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    print_banner()
    app.run(debug=True, port=5000)
