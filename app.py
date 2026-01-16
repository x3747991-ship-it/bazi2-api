# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import math
import os
import logging
from contextlib import contextmanager

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

# --- 数据库配置 ---
DB_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bazi.db')

@contextmanager
def get_db():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使查询结果可以按列名访问
    try:
        yield conn
    finally:
        conn.close()

def check_database():
    """检查数据库是否存在且有效"""
    if not os.path.exists(DB_PATH):
        logger.error(f"数据库文件不存在: {DB_PATH}")
        return False
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM bazi_data')
            count = cursor.fetchone()['count']
            logger.info(f"数据库连接成功，共 {count} 条记录")
            return True
    except Exception as e:
        logger.error(f"数据库检查失败: {e}")
        return False

# --- Core Calculation Function ---
def get_bazi_details(birth_time_str, gender):
    """计算八字详情（使用 SQLite）"""
    try:
        birth_dt = datetime.strptime(birth_time_str, '%Y-%m-%d %H:%M')
    except ValueError:
        raise ValueError("日期时间格式错误，请使用 'YYYY-MM-DD HH:MM' 格式。")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 确定八字年份（立春为界，数据库中日期格式为 '1990/1/1'）
        cursor.execute('''
            SELECT 日期 FROM bazi_data 
            WHERE 日期 LIKE ? AND 节气 = '立春'
            LIMIT 1
        ''', (f"{birth_dt.year}/%",))
        
        lichun_row = cursor.fetchone()
        year_for_bazi = birth_dt.year
        
        if lichun_row:
            # 数据库中的日期可能是 '1990/1/15' 格式
            lichun_date_str = lichun_row['日期'].replace('/', '-')
            # 尝试解析，可能没有时间部分
            try:
                lichun_date = datetime.strptime(lichun_date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                lichun_date = datetime.strptime(lichun_date_str, '%Y-%m-%d')
            
            if birth_dt < lichun_date:
                year_for_bazi = birth_dt.year - 1
        
        # 计算年柱
        year_gan_zhi = JIAZI_CYCLE[(year_for_bazi - 1984) % 60]
        
        # 查询节气数据并计算月柱
        # NOTE: 由于数据库日期格式为斜杠，需要手动比较
        cursor.execute('''
            SELECT 日期, 节气 FROM bazi_data 
            WHERE 节气 IN ('立春', '惊蛰', '清明', '立夏', '芒种', '小暑', 
                          '立秋', '白露', '寒露', '立冬', '大雪', '小寒')
            ORDER BY 日期 ASC
        ''')
        
        # 手动查找最近的节气
        all_jie_qi = cursor.fetchall()
        last_jie_qi = None
        for row in all_jie_qi:
            row_date_str = row['日期'].replace('/', '-')
            try:
                row_date = datetime.strptime(row_date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                row_date = datetime.strptime(row_date_str, '%Y-%m-%d')
            
            if row_date <= birth_dt:
                last_jie_qi = row
        if not last_jie_qi:
            raise ValueError("无法找到对应的节气信息")
        
        year_gan_index = TIAN_GAN.index(year_gan_zhi[0])
        month_start_gan_index = (year_gan_index % 5) * 2
        month_index = JIE_QI.index(last_jie_qi['节气'])
        month_gan_index = (month_start_gan_index + month_index) % 10
        month_di_zhi_index = (month_index + 2) % 12
        month_gan_zhi = TIAN_GAN[month_gan_index] + DI_ZHI[month_di_zhi_index]
        
        # 查询日柱（数据库中日期格式为 '1990/1/15'，需要转换）
        date_pattern = birth_dt.strftime('%Y/%-m/%-d') if os.name != 'nt' else birth_dt.strftime('%Y/%#m/%#d')
        cursor.execute('''
            SELECT 干支, `子（23-1）`, `丑(1-3)`, `寅(3-5)`, `卯(5-7)`, 
                   `辰(7-9)`, `巳(9-11)`, `午(11-13)`, `未(13-15)`,
                   `申(15-17)`, `酉(17-19)`, `戌(19-21)`, `亥(21-23)`
            FROM bazi_data 
            WHERE 日期 LIKE ?
            LIMIT 1
        ''', (f"{birth_dt.year}/{birth_dt.month}/{birth_dt.day}%",))
        
        day_row = cursor.fetchone()
        if not day_row:
            raise ValueError(f"数据表中找不到日期: {birth_dt.date()}")
        
        day_gan_zhi = day_row['干支']
        
        # 计算时柱
        hour = birth_dt.hour
        hour_map = {
            '子（23-1）': [23, 0], '丑(1-3)': [1, 2], '寅(3-5)': [3, 4],
            '卯(5-7)': [5, 6], '辰(7-9)': [7, 8], '巳(9-11)': [9, 10],
            '午(11-13)': [11, 12], '未(13-15)': [13, 14], '申(15-17)': [15, 16],
            '酉(17-19)': [17, 18], '戌(19-21)': [19, 20], '亥(21-23)': [21, 22]
        }
        
        hour_gan_zhi = None
        for col_name, hours in hour_map.items():
            if hour in hours:
                hour_gan_zhi = day_row[col_name]
                break
        
        if not hour_gan_zhi:
            raise ValueError(f"无法为 {birth_dt.hour} 点找到对应的时柱。")
        
        # 计算起运信息
        year_gan = year_gan_zhi[0]
        is_yang_year = year_gan in ['甲', '丙', '戊', '庚', '壬']
        is_male = gender == '男'
        is_forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)
        
        # 查询下一个节气
        cursor.execute('''
            SELECT 日期 FROM bazi_data 
            WHERE 节气 IN ('立春', '惊蛰', '清明', '立夏', '芒种', '小暑', 
                          '立秋', '白露', '寒露', '立冬', '大雪', '小寒')
            ORDER BY 日期 ASC
        ''')
        
        next_jie_qi = None
        for row in cursor.fetchall():
            row_date_str = row['日期'].replace('/', '-')
            try:
                row_date = datetime.strptime(row_date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                row_date = datetime.strptime(row_date_str, '%Y-%m-%d')
            
            if row_date > birth_dt:
                next_jie_qi = row
                break
        
        if is_forward and next_jie_qi:
            next_jie_qi_date_str = next_jie_qi['日期'].replace('/', '-')
            try:
                next_jie_qi_date = datetime.strptime(next_jie_qi_date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                next_jie_qi_date = datetime.strptime(next_jie_qi_date_str, '%Y-%m-%d')
            time_diff = next_jie_qi_date - birth_dt
        else:
            last_jie_qi_date_str = last_jie_qi['日期'].replace('/', '-')
            try:
                last_jie_qi_date = datetime.strptime(last_jie_qi_date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                last_jie_qi_date = datetime.strptime(last_jie_qi_date_str, '%Y-%m-%d')
            time_diff = birth_dt - last_jie_qi_date
        
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
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    db_ok = os.path.exists(DB_PATH)
    if not db_ok:
        return jsonify({"status": "unhealthy", "message": "数据库文件不存在"}), 503
    return jsonify({"status": "healthy", "database": "SQLite", "db_path": DB_PATH}), 200

@app.route('/', methods=['GET'])
def index():
    """根路径欢迎页"""
    return jsonify({
        "message": "八字 API 服务（SQLite 版本）",
        "version": "2.0",
        "database": "SQLite",
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

# --- 应用启动时检查数据库 ---
if __name__ != '__main__':
    # NOTE: Gunicorn 启动时执行
    logger.info("应用初始化中（SQLite 版本）...")
    if not check_database():
        logger.error("数据库不可用，应用无法正常工作")

if __name__ == '__main__':
    # 本地开发模式
    check_database()
    app.run(debug=True, host='0.0.0.0', port=8000)
