# -*- coding: utf-8 -*-
# app.py (整合 SQLite 資料庫最終版)

from flask import Flask, render_template, request, redirect, url_for
import random
import sqlite3 # 引入 SQLite 工具
import os # 引入 os 工具，用來檢查檔案是否存在

app = Flask(__name__)
# 永久硬碟的路徑
DATA_DIR = '/var/data'
DATABASE = os.path.join(DATA_DIR, 'restaurants.db')

# 確保資料夾存在
os.makedirs(DATA_DIR, exist_ok=True)

# --- 資料區塊 ---
# (這部分資料只會在第一次建立資料庫時使用)
LOCATION_DATA = {
    "台北市": {"中正區": ["台北車站", "台大醫院", "中正紀念堂", "善導寺", "忠孝新生", "古亭", "東門", "小南門"], "大同區": ["雙連", "中山", "北門", "大橋頭", "圓山"], "中山區": ["松江南京", "南京復興", "中山國小", "行天宮", "大直", "劍南路", "西湖", "港墘", "文德", "內湖", "大湖公園", "葫洲", "東湖", "南港軟體園區", "南港展覽館"], "松山區": ["南京三民", "台北小巨蛋", "松山機場"], "大安區": ["大安", "信義安和", "忠孝復興", "忠孝敦化", "國父紀念館", "科技大樓", "六張犁", "麟光", "公館"], "萬華區": ["西門", "龍山寺"], "信義區": ["台北101/世貿", "象山", "永春", "後山埤", "市政府"], "士林區": ["士林", "劍潭", "芝山", "明德", "石牌", "唭哩岸", "奇岩"], "北投區": ["北投", "新北投", "復興崗", "忠義", "關渡"], "內湖區": ["內湖", "大湖公園", "葫洲", "東湖", "文德", "港墘", "西湖"], "南港區": ["南港", "南港展覽館", "南港軟體園區"], "文山區": ["景美", "萬隆", "辛亥", "萬芳醫院", "萬芳社區", "木柵", "動物園"]},
    "新北市": {"板橋區": ["板橋", "新埔", "江子翠", "府中", "亞東醫院"], "三重區": ["三重", "菜寮", "三重國小", "先嗇宮", "台北橋"], "中和區": ["景安", "永安市場", "南勢角", "中和"], "永和區": ["頂溪"], "新莊區": ["新莊", "輔大", "丹鳳", "迴龍", "頭前庄", "幸福", "新北產業園區"], "新店區": ["新店", "新店區公所", "七張", "大坪林", "小碧潭"], "土城區": ["土城", "海山", "永寧", "頂埔"], "蘆洲區": ["蘆洲", "三民高中", "徐匯中學", "三和國中"], "汐止區": ["南港展覽館"], "淡水區": ["淡水", "紅樹林", "竹圍", "淡水漁人碼頭", "淡金鄧公", "淡江大學"], "林口區": ["林口"], "樹林區": [], "鶯歌區": [], "三峽區": [], "瑞芳區": [], "五股區": [], "泰山區": [], "八里區": [], "深坑區": [], "石碇區": [], "坪林區": [], "三芝區": [], "石門區": [], "金山區": [], "萬里區": [], "平溪區": [], "雙溪區": [], "貢寮區": [], "烏來區": []},
    "桃園市": {"桃園區": [], "中壢區": ["環北", "興南", "桃園體育園區", "高鐵桃園站", "領航", "橫山", "大園"], "平鎮區": [], "八德區": [], "楊梅區": [], "蘆竹區": [], "大溪區": [], "龍潭區": [], "龜山區": [], "大園區": [], "觀音區": [], "新屋區": [], "復興區": []},
    "台中市": {"中區": [], "東區": [], "南區": [], "西區": [], "北區": [], "北屯區": ["北屯總站", "舊社", "松竹", "四維國小", "文心崇德", "文心中清"], "西屯區": ["文華高中", "文心櫻花", "市政府", "水安宮", "文心森林公園"], "南屯區": ["九張犁", "九德", "烏日", "高鐵台中站", "新烏日", "成功", "大慶"], "太平區": [], "大里區": [], "霧峰區": [], "烏日區": [], "豐原區": [], "后里區": [], "石岡區": [], "東勢區": [], "和平區": [], "新社區": [], "潭子區": [], "大雅區": [], "神岡區": [], "大肚區": [], "沙鹿區": [], "龍井區": [], "梧棲區": [], "清水區": [], "大甲區": [], "外埔區": [], "大安區": []},
    "高雄市": {"楠梓區": ["油廠國小", "楠梓加工區", "後勁", "都會公園"], "左營區": ["左營/高鐵", "生態園區", "巨蛋", "凹子底"], "鼓山區": ["西子灣", "哈瑪星", "鹽埕埔", "市議會(舊址)"], "三民區": ["高雄車站", "後驛"], "前金區": ["美麗島", "信義國小", "文化中心"], "苓雅區": ["中央公園", "三多商圈", "五塊厝", "衛武營"], "前鎮區": ["獅甲", "凱旋", "前鎮高中", "草衙", "高雄國際機場"], "小港區": ["小港"], "鳳山區": ["鳳山", "大東", "鳳山西站(高雄市議會)"], "大寮區": ["大寮"], "岡山區": ["岡山高醫", "岡山車站", "南岡山"], "橋頭區": ["橋頭火車站", "橋頭糖廠"]},
    "台南市":{}, "基隆市":{}, "新竹市":{}, "嘉義市":{}, "宜蘭縣":{}, "新竹縣":{}, "苗栗縣":{},"彰化縣":{},"南投縣":{},"雲林縣":{},"嘉義縣":{},"屏東縣":{},"花蓮縣":{},"台東縣":{},"澎湖縣":{},"金門縣":{},"連江縣":{}
}
CITY_ORDER = ["基隆市", "台北市", "新北市", "桃園市", "新竹市", "新竹縣", "宜蘭縣", "苗栗縣", "台中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "台南市", "高雄市", "屏東縣", "澎湖縣", "花蓮縣", "台東縣", "金門縣", "連江縣"]
LOCATION_DATA = {city: LOCATION_DATA.get(city, {}) for city in CITY_ORDER}
# --- End of 資料區塊 ---


# --- 資料庫輔助函式 ---
def get_db_conn():
    """建立資料庫連線"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # 讓回傳的資料可以用欄位名稱存取
    return conn

def init_db():
    """初始化資料庫：建立資料表並插入預設資料"""
    if os.path.exists(DATABASE): # 如果資料庫檔案已存在，就不再初始化
        return
        
    print("Creating a new database...")
    conn = get_db_conn()
    cursor = conn.cursor()
    
    # 建立 restaurants 資料表
    cursor.execute('''
        CREATE TABLE restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            district TEXT NOT NULL,
            station TEXT,
            name TEXT NOT NULL
        )
    ''')
    
    # 插入一些預設資料
    initial_restaurants = [
        {"city": "台北市", "district": "大安區", "station": "忠孝復興站", "name": "鼎泰豐 SOGO復興館"},
        {"city": "台北市", "district": "信義區", "station": "市政府站", "name": "添好運 統一時代店"},
        {"city": "新北市", "district": "板橋區", "station": "板橋站", "name": "海底撈 板橋大遠百店"},
    ]
    for r in initial_restaurants:
        cursor.execute("INSERT INTO restaurants (city, district, station, name) VALUES (?, ?, ?, ?)",
                       (r['city'], r['district'], r['station'], r['name']))
    
    conn.commit()
    conn.close()
    print("Database initialized.")
# --- End of 資料庫輔助函式 ---


@app.route('/')
def index():
    conn = get_db_conn()
    cursor = conn.cursor()

    # 從資料庫讀取所有店家資料
    cursor.execute("SELECT * FROM restaurants")
    restaurants_from_db = cursor.fetchall()

    conn.close()

    # 將資料庫回傳的 Row 物件轉換為我們前端習慣的字典格式
    restaurants = [dict(row) for row in restaurants_from_db]

    # (篩選邏輯和之前一樣，只是現在操作的是從 DB 讀出來的資料)
    filter_city = request.args.get('filter_city')
    if filter_city:
        restaurants = [r for r in restaurants if r['city'] == filter_city]
    # ... 您可以加回地區和捷運站的篩選 ...

    return render_template('index.html', 
                           location_data=LOCATION_DATA, 
                           restaurants=restaurants,
                           filter_values=request.args)

@app.route('/add', methods=['POST'])
def add():
    new_restaurant = {
        "city": request.form.get('city'),
        "district": request.form.get('district'),
        "station": request.form.get('station', ''),
        "name": request.form.get('name')
    }
    
    if new_restaurant['city'] and new_restaurant['district'] and new_restaurant['name']:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO restaurants (city, district, station, name) VALUES (?, ?, ?, ?)",
                       (new_restaurant['city'], new_restaurant['district'], new_restaurant['station'], new_restaurant['name']))
        conn.commit()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete/<int:restaurant_id>', methods=['POST'])
def delete(restaurant_id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM restaurants WHERE id = ?", (restaurant_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:restaurant_id>', methods=['GET', 'POST'])
def edit(restaurant_id):
    conn = get_db_conn()
    
    if request.method == 'POST':
        updated_data = {
            "city": request.form.get('city'),
            "district": request.form.get('district'),
            "station": request.form.get('station', ''),
            "name": request.form.get('name'),
            "id": restaurant_id
        }
        cursor = conn.cursor()
        cursor.execute("UPDATE restaurants SET city=?, district=?, station=?, name=? WHERE id=?",
                       (updated_data['city'], updated_data['district'], updated_data['station'], updated_data['name'], updated_data['id']))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else: # GET
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,))
        restaurant_to_edit = cursor.fetchone()
        conn.close()

        if restaurant_to_edit is None:
            return "找不到該店家!", 404
        
        return render_template('edit.html', restaurant=dict(restaurant_to_edit), restaurant_id=restaurant_id)


if __name__ == '__main__':
    init_db() # 在啟動伺服器前，先檢查並初始化資料庫
    app.run(debug=True)