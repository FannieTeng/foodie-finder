# -*- coding: utf-8 -*-
# app.py (最終功能整合版)

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from functools import wraps # 用於製作「需要登入」的裝飾器

app = Flask(__name__)

# --- App 設定 ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local_users.db').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev') # 從環境變數讀取密鑰，更安全

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

# --- 地點資料 (用來產生下拉選單) ---
CITY_ORDER = ["基隆市", "台北市", "新北市", "桃園市", "新竹市", "新竹縣", "宜蘭縣", "苗栗縣", "台中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "台南市", "高雄市", "屏東縣", "澎湖縣", "花蓮縣", "台東縣", "金門縣", "連江縣"]
UNSORTED_LOCATION_DATA = { "台北市": {"中正區": ["台北車站"], "大安區": ["忠孝復興站"]}, "新北市": {"板橋區": ["板橋站"]} } # 您可以貼回更完整的版本
LOCATION_DATA = {city: UNSORTED_LOCATION_DATA.get(city, {}) for city in CITY_ORDER}

# --- 使用者狀態管理 ---
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = db.session.get(User, user_id) if user_id else None

def login_required(view):
    """一個裝飾器，用於保護需要登入才能訪問的頁面"""
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# --- 路由 (Routes) ---

@app.route('/')
@login_required # 保護主頁，必須登入才能看
def index():
    restaurants_query = db.session.execute(
        db.select(Restaurant).where(Restaurant.user_id == g.user.id).order_by(Restaurant.id)
    ).scalars().all()
    restaurants_list = [r.to_dict() for r in restaurants_query]
    
    filter_city = request.args.get('filter_city')
    if filter_city:
        restaurants_list = [r for r in restaurants_list if r['city'] == filter_city]
    
    return render_template('index.html', 
                           location_data=LOCATION_DATA, 
                           restaurants=restaurants_list,
                           filter_values=request.args)

@app.route('/search', methods=['POST'])
@login_required
def search():
    # ... 搜尋邏輯 ...
    return redirect(url_for('index')) # 簡化：搜尋功能暫時導回主頁

@app.route('/add', methods=['POST'])
@login_required
def add():
    new_restaurant = Restaurant(
        city=request.form.get('city'), district=request.form.get('district'),
        station=request.form.get('station', ''), name=request.form.get('name'),
        author=g.user # 直接關聯目前登入的使用者
    )
    if new_restaurant.city and new_restaurant.district and new_restaurant.name:
        db.session.add(new_restaurant)
        db.session.commit()
        flash(f"已成功新增店家：{new_restaurant.name}", 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:restaurant_id>', methods=['POST'])
@login_required
def delete(restaurant_id):
    restaurant_to_delete = db.session.get(Restaurant, restaurant_id)
    if restaurant_to_delete and restaurant_to_delete.author == g.user:
        db.session.delete(restaurant_to_delete)
        db.session.commit()
        flash(f"已刪除店家：{restaurant_to_delete.name}", 'success')
    else:
        flash("操作無效或權限不足。", 'error')
    return redirect(url_for('index'))

@app.route('/edit/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def edit(restaurant_id):
    restaurant_to_edit = db.session.get(Restaurant, restaurant_id)
    if not restaurant_to_edit or restaurant_to_edit.author != g.user:
        flash("找不到該店家或權限不足。", 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        restaurant_to_edit.city = request.form.get('city')
        restaurant_to_edit.district = request.form.get('district')
        restaurant_to_edit.station = request.form.get('station', '')
        restaurant_to_edit.name = request.form.get('name')
        db.session.commit()
        flash(f"已更新店家：{restaurant_to_edit.name}", 'success')
        return redirect(url_for('index'))
    else: # GET
        return render_template('edit.html', restaurant=restaurant_to_edit.to_dict(), restaurant_id=restaurant_id)

# --- 使用者系統路由 ---
@app.route('/register', methods=('GET', 'POST'))
def register():
    # ... 註冊邏輯 (與上一版相同) ...
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        if not username: error = '請輸入使用者名稱。'
        elif not password: error = '請輸入密碼。'
        elif db.session.execute(db.select(User).where(User.username == username)).scalar():
            error = f"使用者 '{username}' 已被註冊。"
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
    # ... 登入邏輯 (與上一版相同) ...
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
    return redirect(url_for('login'))

# --- App 初始化 ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)