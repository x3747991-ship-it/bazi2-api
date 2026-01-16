# -*- coding: utf-8 -*-
"""
CSV 转 SQLite 转换脚本
用于优化内存占用和查询性能
"""

import pandas as pd
import sqlite3
import os

def convert_csv_to_sqlite():
    """将 data.csv 转换为 SQLite 数据库"""
    
    current_dir = os.path.dirname(os.path.realpath(__file__))
    csv_path = os.path.join(current_dir, 'data.csv')
    db_path = os.path.join(current_dir, 'bazi.db')
    
    print(f"[1/3] 读取 CSV 文件: {csv_path}")
    df = pd.read_csv(csv_path, encoding='gbk')
    print(f"      共 {len(df)} 条记录")
    
    print(f"\n[2/3] 创建 SQLite 数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    
    # 将数据写入数据库
    df.to_sql('bazi_data', conn, if_exists='replace', index=False)
    
    print("\n[3/3] 创建索引以加速查询...")
    cursor = conn.cursor()
    
    # 为日期列创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON bazi_data(日期)')
    # 为节气列创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_solar_term ON bazi_data(节气)')
    
    conn.commit()
    
    # 验证数据
    cursor.execute('SELECT COUNT(*) FROM bazi_data')
    count = cursor.fetchone()[0]
    print(f"\n[完成] 转换完成！数据库包含 {count} 条记录")
    
    # 显示数据库大小
    db_size = os.path.getsize(db_path) / (1024 * 1024)
    csv_size = os.path.getsize(csv_path) / (1024 * 1024)
    print(f"\n文件大小对比：")
    print(f"  CSV:    {csv_size:.2f} MB")
    print(f"  SQLite: {db_size:.2f} MB")
    print(f"  压缩率: {(1 - db_size/csv_size) * 100:.1f}%")
    
    conn.close()
    
    print("\n[成功] 转换成功！现在可以修改 app.py 使用 SQLite 数据库")

if __name__ == '__main__':
    convert_csv_to_sqlite()
