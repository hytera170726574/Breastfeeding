import sqlite3
import os

# 连接数据库（使用绝对路径，避免工作目录不同导致连接到错误的 DB）
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'app.db')
print(f"Using DB: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("数据库中的表:")
for table in tables:
    print(f"  {table[0]}")

# 查看用户表内容
print("\n用户表内容:")
cursor.execute("SELECT * FROM user;")
users = cursor.fetchall()
for user in users:
    print(f"  {user}")

# 查看婴儿表内容
print("\n婴儿表内容:")
try:
    cursor.execute("SELECT * FROM baby;")
    babies = cursor.fetchall()
    for baby in babies:
        print(f"  {baby}")
except:
    print("  婴儿表不存在或为空")

# 查看睡眠表内容
print("\n睡眠表内容:")
try:
    cursor.execute("SELECT * FROM sleep;")
    sleeps = cursor.fetchall()
    for sleep in sleeps:
        print(f"  {sleep}")
    if not sleeps:
        print("  无记录")
except Exception as e:
    print("  睡眠表不存在或为空", e)

conn.close()