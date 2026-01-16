# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime
import math
import os
import logging

# --- 配置日志 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = True

# --- GLOBAL CONSTANTS ---
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
JIAZI_CYCLE = [TIAN_GAN[i % 10] + DI_ZHI[i % 12] for i in range(60)]
JIE_QI = ['立春', '惊蛰', '清明', '立夏', '芒种', '小暑', '立秋', '白露', '寒露', '立冬', '大雪', '小寒']

# --- 全局数据缓存 ---
# NOTE: 应用启动时加载一次，所有请求共享，避免重复读取文件
BAZI_DATA = None
DATE_COLUMN = '日期'
SOLAR_TERM_COLUMN = '节气'
GAN_ZHI_COLUMN = '干支'

def load_data():
    """应用启动时加载数据到内存"""
    global BAZI_DATA
    try:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        csv_path = os.path.join(current_dir, 'data.csv')
        
        logger.info(f"开始加载数据文件: {csv_path}")
        df = pd.read_csv(csv_path, encoding='gbk')
        df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
        
        # 预处理节气数据，提高查询效率
        jie_qi_df = df[df[SOLAR_TERM_COLUMN].isin(JIE_QI)].sort_values(DATE_COLUMN).reset_index()
        
        BAZI_DATA = {
            'full_data': df,
            'jie_qi_data': jie_qi_df
        }
        logger.info(f"数据加载成功，共 {len(df)} 条记录")
        return True
    except Exception as e:
        logger.error(f"数据加载失败: {e}")
        return False

# --- Core Calculation Function ---
def get_bazi_details(birth_time_str, gender):
    """计算八字详情"""
    if BAZI_DATA is None:
        raise Exception("数据未加载，请稍后再试")
    
    try:
        birth_dt = datetime.strptime(birth_time_str, '%Y-%m-%d %H:%M')
    except ValueError:
        raise ValueError("日期时间格式错误，请使用 'YYYY-MM-DD HH:MM' 格式。")
    
    df = BAZI_DATA['full_data']
    jie_qi_df = BAZI_DATA['jie_qi_data']
    
    # 确定八字年份（立春为界）
    lichun_this_year = df[(df[DATE_COLUMN].dt.year == birth_dt.year) & (df[SOLAR_TERM_COLUMN] == '立春')]
    year_for_bazi = birth_dt.year
    if not lichun_this_year.empty and birth_dt < lichun_this_year.iloc[0][DATE_COLUMN]:
        year_for_bazi = birth_dt.year - 1
    
    # 计算年柱
    year_gan_zhi = JIAZI_CYCLE[(year_for_bazi - 1984) % 60]
    
    # 计算月柱
    last_jie_qi = jie_qi_df[jie_qi_df[DATE_COLUMN] <= birth_dt].iloc[-1]
    year_gan_index = TIAN_GAN.index(year_gan_zhi[0])
    month_start_gan_index = (year_gan_index % 5) * 2
    month_index = JIE_QI.index(last_jie_qi[SOLAR_TERM_COLUMN])
    month_gan_index = (month_start_gan_index + month_index) % 10
    month_di_zhi_index = (month_index + 2) % 12
    month_gan_zhi = TIAN_GAN[month_gan_index] + DI_ZHI[month_di_zhi_index]
    
    # 计算日柱
    day_row = df[df[DATE_COLUMN].dt.date == birth_dt.date()]
    if day_row.empty:
        raise ValueError(f"数据表中找不到日期: {birth_dt.date()}。")
    day_gan_zhi = day_row.iloc[0][GAN_ZHI_COLUMN]
    
    # 计算时柱
    hour = birth_dt.hour
    hour_map = {
        '子（23-1）': [23, 0], '丑(1-3)': [1, 2], '寅(3-5)': [3, 4],
        '卯(5-7)': [5, 6], '辰(7-9)': [7, 8], '巳(9-11)': [9, 10],
        '午(11-13)': [11, 12], '未(13-15)': [13, 14], '申(15-17)': [15, 16],
        '酉(17-19)': [17, 18], '戌(19-21)': [19, 20], '亥(21-23)': [21, 22]
    }
    hour_gan_zhi = next((day_row.iloc[0][col] for col, hours in hour_map.items() if hour in hours), None)
    if pd.isna(hour_gan_zhi):
        raise ValueError(f"无法为 {birth_dt.hour} 点找到对应的时柱。")
    
    # 计算起运信息
    year_gan = year_gan_zhi[0]
    is_yang_year = year_gan in ['甲', '丙', '戊', '庚', '壬']
    is_male = gender == '男'
    is_forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)
    
    time_diff = (jie_qi_df[jie_qi_df[DATE_COLUMN] > birth_dt].iloc[0][DATE_COLUMN] - birth_dt) if is_forward else (birth_dt - last_jie_qi[DATE_COLUMN])
    days_diff = time_diff.total_seconds() / (24 * 3600)
    start_luck_years = int(days_diff / 3)
    start_luck_months = int((days_diff % 3) * 4)
    start_luck_days = math.ceil((days_diff % 3 * 4 % 1) * 30)
    
    # 计算大运
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

# --- 健康检查端点 ---
# NOTE: zeabur 需要此端点来确认服务启动成功
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    if BAZI_DATA is None:
        return jsonify({"status": "unhealthy", "message": "数据未加载"}), 503
    return jsonify({"status": "healthy", "data_loaded": True}), 200

@app.route('/', methods=['GET'])
def index():
    """根路径欢迎页"""
    return jsonify({
        "message": "八字 API 服务",
        "endpoints": {
            "/health": "健康检查",
            "/bazi": "八字计算（POST JSON: {birth_time, gender}）"
        }
    }), 200

# --- Flask Web Application Wrapper ---
@app.route('/bazi', methods=['POST'])
def bazi_handler():
    """八字计算接口"""
    data = request.get_json()
    if not data or 'birth_time' not in data or 'gender' not in data:
        return jsonify({"error": "请求体必须是JSON，且包含 'birth_time' 和 'gender' 字段。"}), 400
    try:
        bazi_info = get_bazi_details(data['birth_time'], data['gender'])
        return jsonify(bazi_info)
    except Exception as e:
        logger.error(f"处理请求时出错: {e}")
        return jsonify({"error": str(e)}), 500

# --- 应用启动时加载数据 ---
if __name__ != '__main__':
    # NOTE: Gunicorn 启动时执行
    logger.info("应用初始化中...")
    if not load_data():
        logger.error("数据加载失败，应用无法正常工作")

if __name__ == '__main__':
    # 本地开发模式
    load_data()
    app.run(debug=True, host='0.0.0.0', port=8000)
