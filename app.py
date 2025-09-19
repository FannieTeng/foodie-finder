# -*- coding: utf-8 -*-
# app.py (資料最全之最終定案版)

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import random

app = Flask(__name__)

# --- App 設定 ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local_users.db').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_super_secret_key_for_dev')

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
UNSORTED_LOCATION_DATA = {
    "台北市": {"中正區": ["台北車站", "台大醫院", "中正紀念堂", "善導寺", "忠孝新生", "古亭", "東門", "小南門"], "大同區": ["雙連", "中山", "北門", "大橋頭", "圓山"], "中山區": ["松江南京", "南京復興", "中山國小", "行天宮", "大直", "劍南路", "西湖", "港墘", "文德", "內湖", "大湖公園", "葫洲", "東湖", "南港軟體園區", "南港展覽館"], "松山區": ["南京三民", "台北小巨蛋", "松山機場"], "大安區": ["大安", "信義安和", "忠孝復興", "忠孝敦化", "國父紀念館", "科技大樓", "六張犁", "麟光", "公館"], "萬華區": ["西門", "龍山寺"], "信義區": ["台北101/世貿", "象山", "永春", "後山埤", "市政府"], "士林區": ["士林", "劍潭", "芝山", "明德", "石牌", "唭哩岸", "奇岩"], "北投區": ["北投", "新北投", "復興崗", "忠義", "關渡"], "內湖區": ["內湖", "大湖公園", "葫洲", "東湖", "文德", "港墘", "西湖"], "南港區": ["南港", "南港展覽館", "南港軟體園區"], "文山區": ["景美", "萬隆", "辛亥", "萬芳醫院", "萬芳社區", "木柵", "動物園"]},
    "新北市": {"板橋區": ["板橋", "新埔", "江子翠", "府中", "亞東醫院"], "三重區": ["三重", "菜寮", "三重國小", "先嗇宮", "台北橋"], "中和區": ["景安", "永安市場", "南勢角", "中和"], "永和區": ["頂溪"], "新莊區": ["新莊", "輔大", "丹鳳", "迴龍", "頭前庄", "幸福", "新北產業園區"], "新店區": ["新店", "新店區公所", "七張", "大坪林", "小碧潭"], "土城區": ["土城", "海山", "永寧", "頂埔"], "蘆洲區": ["蘆洲", "三民高中", "徐匯中學", "三和國中"], "汐止區": ["南港展覽館"], "淡水區": ["淡水", "紅樹林", "竹圍", "淡水漁人碼頭", "淡金鄧公", "淡江大學"], "林口區": ["林口"]},
    "桃園市": {"桃園區": [], "中壢區": ["環北", "興南", "桃園體育園區", "高鐵桃園站", "領航", "橫山", "大園"]},
    "台中市": {"北屯區": ["北屯總站", "舊社", "松竹", "四維國小", "文心崇德", "文心中清"], "西屯區": ["文華高中", "文心櫻花", "市政府", "水安宮", "文心森林公園"], "南屯區": ["九張犁", "九德", "烏日", "高鐵台中站", "新烏日", "成功", "大慶"]},
    "高雄市": {"楠梓區": ["油廠國小", "楠梓加工區", "後勁", "都會公園"], "左營區": ["左營/高鐵", "生態園區", "巨蛋", "凹子底"], "鼓山區": ["西子灣", "哈瑪星", "鹽埕埔", "市議會(舊址)"], "三民區": ["高雄車站", "後驛"], "前金區": ["美麗島", "信義國小", "文化中心"], "苓雅區": ["中央公園", "三多商圈", "五塊厝", "衛武營"], "前鎮區": ["獅甲", "凱旋", "前鎮高中", "草衙", "高雄國際機場"], "小港區": ["小港"], "鳳山區": ["鳳山", "大東", "鳳山西站(高雄市議會)"], "大寮區": ["大寮"], "岡山區": ["岡山高醫", "岡山車站", "南岡山"], "橋頭區": ["橋頭火車站", "橋頭糖廠"]},
    "基隆市":{},"新竹市":{},"新竹縣":{},"宜蘭縣":{},"苗栗縣":{},"彰化縣":{},"南投縣":{},"雲林縣":{},"嘉義市":{},"嘉義縣":{},"台南市":{},"屏東縣":{},"澎湖縣":{},"花蓮縣":{},"台東縣":{},"金門縣":{},"連江縣":{}
}
LOCATION_DATA = {city: UNSORTED_LOCATION_DATA.get(city, {}) for city in CITY_ORDER}


# --- 使用者狀態管理 ---
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = db.session.get(User, user_id) if user_id else None

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("請先登入才能訪問此頁面。", "error")
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# --- 路由 (Routes) ---
@app.route('/')
@login_required
def index():
    restaurants_query = db.session.execute(db.select(Restaurant).where(Restaurant.user_id == g.user.id).order_by(Restaurant.id)).scalars().all()
    restaurants_list = [r.to_dict() for r in restaurants_query]
    filter_city = request.args.get('filter_city')
    if filter_city:
        restaurants_list = [r for r in restaurants_list if r['city'] == filter_city]
    filter_district = request.args.get('filter_district')
    if filter_district:
        restaurants_list = [r for r in restaurants_list if r['district'] == filter_district]
    return render_template('index.html', location_data=LOCATION_DATA, restaurants=restaurants_list, filter_values=request.args)

@app.route('/search', methods=['POST'])
@login_required
def search():
    all_restaurants_query = db.session.execute(db.select(Restaurant).where(Restaurant.user_id == g.user.id)).scalars().all()
    all_restaurants_list = [r.to_dict() for r in all_restaurants_query]
    selected_city = request.form.get('city')
    selected_district = request.form.get('district')
    selected_station = request.form.get('station')
    action = request.form.get('action')
    filtered_list = all_restaurants_list
    if selected_city:
        filtered_list = [r for r in filtered_list if r['city'] == selected_city]
    if selected_district:
        filtered_list = [r for r in filtered_list if r['district'] == selected_district]
    if selected_station:
        filtered_list = [r for r in filtered_list if r['station'] == selected_station]
    search_results = []
    recommendation = None
    if action == '檢視所有':
        search_results = filtered_list
    elif action == '隨機推薦' and filtered_list:
        recommendation = random.choice(filtered_list)
    return render_template('index.html', location_data=LOCATION_DATA, restaurants=all_restaurants_list, search_results=search_results, recommendation=recommendation, filter_values={})

@app.route('/add', methods=['POST'])
@login_required
def add():
    new_restaurant = Restaurant(city=request.form.get('city'), district=request.form.get('district'), station=request.form.get('station', ''), name=request.form.get('name'), author=g.user)
    if new_restaurant.city and new_restaurant.district and new_restaurant.name:
        db.session.add(new_restaurant); db.session.commit(); flash(f"已成功新增店家：{new_restaurant.name}", 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:restaurant_id>', methods=['POST'])
@login_required
def delete(restaurant_id):
    r_to_delete = db.session.get(Restaurant, restaurant_id)
    if r_to_delete and r_to_delete.author == g.user:
        db.session.delete(r_to_delete); db.session.commit(); flash(f"已刪除店家：{r_to_delete.name}", 'success')
    else: flash("操作無效或權限不足。", 'error')
    return redirect(url_for('index'))

@app.route('/edit/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def edit(restaurant_id):
    r_to_edit = db.session.get(Restaurant, restaurant_id)
    if not r_to_edit or r_to_edit.author != g.user:
        flash("找不到該店家或權限不足。", 'error'); return redirect(url_for('index'))
    if request.method == 'POST':
        r_to_edit.city = request.form.get('city'); r_to_edit.district = request.form.get('district'); r_to_edit.station = request.form.get('station', ''); r_to_edit.name = request.form.get('name')
        db.session.commit(); flash(f"已更新店家：{r_to_edit.name}", 'success'); return redirect(url_for('index'))
    return render_template('edit.html', restaurant=r_to_edit.to_dict(), restaurant_id=restaurant_id)

@app.route('/register', methods=('GET', 'POST'))
def register():
    if g.user: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']; password = request.form['password']; error = None
        if not username: error = '請輸入使用者名稱。'
        elif not password: error = '請輸入密碼。'
        elif db.session.execute(db.select(User).where(User.username == username)).scalar(): error = f"使用者 '{username}' 已被註冊。"
        if error is None:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password_hash=hashed_password)
            db.session.add(new_user); db.session.commit(); flash('註冊成功，請登入！', 'success'); return redirect(url_for('login'))
        flash(error, 'error')
    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if g.user: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']; password = request.form['password']; error = None
        user = db.session.execute(db.select(User).where(User.username == username)).scalar_one_or_none()
        if user is None or not check_password_hash(user.password_hash, password): error = '使用者名稱或密碼錯誤。'
        if error is None:
            session.clear(); session['user_id'] = user.id; return redirect(url_for('index'))
        flash(error, 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功登出。', 'success')
    return redirect(url_for('login'))

# --- App 初始化 ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)