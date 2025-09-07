# -*- coding: utf-8 -*-
# app.py (多使用者系統 - 核心功能版)

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# --- App 設定 ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local_users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a_super_secret_key_that_should_be_changed' # 在正式專案中，這應該是一個更複雜且不公開的字串

db = SQLAlchemy(app)

# --- 資料庫模型 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    restaurants = db.relationship('Restaurant', backref='author', lazy=True, cascade="all, delete-orphan")

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    station = db.Column(db.String(50))
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# --- 使用者狀態管理 ---
@app.before_request
def load_logged_in_user():
    """在處理每個請求前，先檢查 session 並載入使用者資訊"""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)

# --- 路由 (Routes) ---

@app.route('/')
def index():
    # 在下個階段，我們會在這裡加入顯示個人餐廳列表的邏輯
    return render_template('index.html')

# --- 使用者系統路由 ---

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = '請輸入使用者名稱。'
        elif not password:
            error = '請輸入密碼。'
        elif db.session.execute(db.select(User).where(User.username == username)).scalar() is not None:
            error = f"使用者名稱 '{username}' 已經被註冊了。"

        if error is None:
            new_user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('註冊成功，請登入！', 'success')
            return redirect(url_for('login'))
        
        flash(error, 'error')

    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        
        user = db.session.execute(db.select(User).where(User.username == username)).scalar_one_or_none()

        if user is None or not check_password_hash(user.password_hash, password):
            error = '使用者名稱或密碼錯誤。'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('index'))

        flash(error, 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- App 初始化 ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)