import sqlite3
import os

# 连接数据库
conn = sqlite3.connect('app.db')
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

conn.close()