# -*- coding: utf-8 -*-
# app.py (整合 PostgreSQL + SQLAlchemy 版)

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# --- 資料庫設定 ---
# 從「環境變數」讀取資料庫連結，這是專業、安全的作法
# 如果在本機測試，它會使用一個名為 local.db 的 SQLite 檔案
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 資料庫模型 (定義資料表的樣子) ---
class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    station = db.Column(db.String(50))
    name = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# --- End of 資料庫設定 ---

# (地點資料不再需要從 Python 讀取，但為了下拉選單的級聯，我們暫時保留)
LOCATION_DATA = { "台北市": {"大安區": ["忠孝復興站"]}, "新北市": {"板橋區": ["板橋站"]} } # 您可以貼回完整版

@app.route('/')
def index():
    restaurants_from_db = db.session.execute(db.select(Restaurant).order_by(Restaurant.id)).scalars().all()
    restaurants_list = [r.to_dict() for r in restaurants_from_db]
    return render_template('index.html', 
                           location_data=LOCATION_DATA, 
                           restaurants=restaurants_list)

@app.route('/add', methods=['POST'])
def add():
    new_restaurant = Restaurant(
        city=request.form.get('city'),
        district=request.form.get('district'),
        station=request.form.get('station', ''),
        name=request.form.get('name')
    )
    if new_restaurant.city and new_restaurant.district and new_restaurant.name:
        db.session.add(new_restaurant)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:restaurant_id>', methods=['POST'])
def delete(restaurant_id):
    restaurant_to_delete = db.session.get(Restaurant, restaurant_id)
    if restaurant_to_delete:
        db.session.delete(restaurant_to_delete)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:restaurant_id>', methods=['GET', 'POST'])
def edit(restaurant_id):
    restaurant_to_edit = db.session.get(Restaurant, restaurant_id)
    if not restaurant_to_edit:
        return "找不到該店家!", 404
    
    if request.method == 'POST':
        restaurant_to_edit.city = request.form.get('city')
        restaurant_to_edit.district = request.form.get('district')
        restaurant_to_edit.station = request.form.get('station', '')
        restaurant_to_edit.name = request.form.get('name')
        db.session.commit()
        return redirect(url_for('index'))
    else: # GET
        return render_template('edit.html', restaurant=restaurant_to_edit.to_dict(), restaurant_id=restaurant_id)

# 建立資料庫表格的輔助指令
with app.app_context():
    db.create_all()

# 我們不再需要 init_db() 和 get_db_conn()
# if __name__ == '__main__': app.run(debug=True)