# -*- coding: utf-8 -*-
import os
from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime
import math

project_path = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = True

TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
JIAZI_CYCLE = [TIAN_GAN[i % 10] + DI_ZHI[i % 12] for i in range(60)]
JIE_QI = ['立春', '惊蛰', '清明', '立夏', '芒种', '小暑', '立秋', '白露', '寒露', '立冬', '大雪', '小寒']

# --- 【关键】数据加载函数，现在只加载需要的小文件 ---
def load_data_for_year(year):
    """
    Dynamically finds and loads the correct CSV chunk based on the birth year.
    """
    # 每20年一个文件
    chunk_size = 20
    start_year_of_chunk = (year // chunk_size) * chunk_size
    
    # 兼容处理，例如1900年之前的年份
    if year < 1900: 
        start_year_of_chunk = 1900 # Or whatever your data starts from

    end_year_of_chunk = start_year_of_chunk + chunk_size - 1
    
    filename = f"bazi_{start_year_of_chunk}_{end_year_of_chunk}.csv"
    filepath = os.path.join(project_path, 'bazi_data_split', filename)
    
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        df['日期'] = pd.to_datetime(df['日期'])
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"错误：找不到对应年份 {year} 的数据文件: {filename}")
    except Exception as e:
        raise Exception(f"读取数据文件 {filename} 时出错: {e}")

# --- Health Check ---
@app.route('/', methods=['GET'])
def health_check():
    return "OK", 200

# --- Core Calculation Function ---
def get_bazi_details(birth_time_str, gender):
    try:
        birth_dt = datetime.strptime(birth_time_str, '%Y-%m-%d %H:%M')
    except ValueError:
        raise ValueError("日期时间格式错误。")

    # 【关键】动态加载数据
    df = load_data_for_year(birth_dt.year)
    
    # ... (The rest of the calculation logic is identical)
    DATE_COLUMN, SOLAR_TERM_COLUMN, GAN_ZHI_COLUMN = '日期', '节气', '干支'
    lichun_this_year = df[(df[DATE_COLUMN].dt.year == birth_dt.year) & (df[SOLAR_TERM_COLUMN] == '立春')]
    year_for_bazi = birth_dt.year
    if not lichun_this_year.empty and birth_dt < lichun_this_year.iloc[0][DATE_COLUMN]:
        year_for_bazi = birth_dt.year - 1
    year_gan_zhi = JIAZI_CYCLE[(year_for_bazi - 1984) % 60]
    jie_qi_df = df[df[SOLAR_TERM_COLUMN].isin(JIE_QI)].sort_values(DATE_COLUMN).reset_index()
    last_jie_qi = jie_qi_df[jie_qi_df[DATE_COLUMN] <= birth_dt].iloc[-1]
    year_gan_index = TIAN_GAN.index(year_gan_zhi[0])
    month_start_gan_index = (year_gan_index % 5) * 2
    month_index = JIE_QI.index(last_jie_qi[SOLAR_TERM_COLUMN])
    month_gan_index = (month_start_gan_index + month_index) % 10
    month_di_zhi_index = (month_index + 2) % 12
    month_gan_zhi = TIAN_GAN[month_gan_index] + DI_ZHI[month_di_zhi_index]
    day_row = df[df[DATE_COLUMN].dt.date == birth_dt.date()]
    if day_row.empty: raise ValueError(f"数据表中找不到日期: {birth_dt.date()}。")
    day_gan_zhi = day_row.iloc[0][GAN_ZHI_COLUMN]
    hour = birth_dt.hour
    hour_map = {'子（23-1）': [23, 0], '丑(1-3)': [1, 2], '寅(3-5)': [3, 4], '卯(5-7)': [5, 6], '辰(7-9)': [7, 8], '巳(9-11)': [9, 10], '午(11-13)': [11, 12], '未(13-15)': [13, 14], '申(15-17)': [15, 16], '酉(17-19)': [17, 18], '戌(19-21)': [19, 20], '亥(21-23)': [21, 22]}
    hour_gan_zhi = next((day_row.iloc[0][col] for col, hours in hour_map.items() if hour in hours), None)
    if pd.isna(hour_gan_zhi): raise ValueError(f"无法为 {birth_dt.hour} 点找到对应的时柱。")
    year_gan = year_gan_zhi[0]
    is_yang_year = year_gan in ['甲', '丙', '戊', '庚', '壬']
    is_male = gender == '男'
    is_forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)
    time_diff = (jie_qi_df[jie_qi_df[DATE_COLUMN] > birth_dt].iloc[0][DATE_COLUMN] - birth_dt) if is_forward else (birth_dt - last_jie_qi[DATE_COLUMN])
    days_diff = time_diff.total_seconds() / (24 * 3600)
    start_luck_years = int(days_diff / 3)
    start_luck_months = int((days_diff % 3) * 4)
    start_luck_days = math.ceil((days_diff % 3 * 4 % 1) * 30)
    luck_pillars = []
    month_pillar_index = JIAZI_CYCLE.index(month_gan_zhi)
    for i in range(1, 10):
        pillar_index = (month_pillar_index + i) % 60 if is_forward else (month_pillar_index - i + 60) % 60
        luck_pillars.append(JIAZI_CYCLE[pillar_index])
    return {
        "基本信息": {"公历生日": birth_dt.strftime('%Y-%m-%d %H:%M'), "性别": gender},
        "八字命盘": {"年柱": year_gan_zhi, "月柱": month_gan_zhi, "日柱": day_gan_zhi, "时柱": hour_gan_zhi},
        "起运信息": {"方向": "顺行" if is_forward else "逆行", "起运岁数": f"{start_luck_years}岁 {start_luck_months}个月 {start_luck_days}天后"},
        "大运（前九步）": {f"{start_luck_years + i*10}岁": pillar for i, pillar in enumerate(luck_pillars)}
    }

# --- Main API Endpoint ---
@app.route('/bazi', methods=['POST'])
def bazi_handler():
    data = request.get_json()
    if not data or 'birth_time' not in data or 'gender' not in data:
        return jsonify({"error": "请求体必须是JSON"}), 400
    try:
        bazi_info = get_bazi_details(data['birth_time'], data['gender'])
        return jsonify(bazi_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

