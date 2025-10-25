"""Seed seven days of sample data into the SQLite DB directly (no Flask imports).

This script will:
- Ensure a Baby named '李望舒' exists (create if missing)
- Insert per-day records for the previous 7 days (7 days ago .. yesterday):
  - 2 DirectBreastfeeding entries
  - 1 wet Diaper and sometimes 1 dirty Diaper
  - 1 Sleep record
  - 1 BottleBreastFeeding
  - Occasionally 1 FormulaFeeding
- Ensure MilkInventory exists for the baby

Run from project root:
    python3 scripts/seed_weekly_sqlite.py
"""
import sqlite3
from datetime import datetime, date, time, timedelta

DB_PATH = 'app.db'
BABY_NAME = '李望舒'

def iso(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Ensure baby exists
cur.execute("SELECT id, name FROM baby WHERE name = ?", (BABY_NAME,))
row = cur.fetchone()
if row:
    baby_id = row[0]
    print(f"Found baby '{BABY_NAME}' with id={baby_id}")
else:
    # pick an existing user to own the baby (user id 1 exists in this DB)
    user_id = 1
    birth_date = '2025-08-06'
    cur.execute("INSERT INTO baby (name, birth_date, gender, created_at, user_id) VALUES (?, ?, ?, ?, ?)",
                (BABY_NAME, birth_date, 'female', iso(datetime.now()), user_id))
    baby_id = cur.lastrowid
    print(f"Created baby '{BABY_NAME}' with id={baby_id}")

# Seed 7 days: from 7 days ago up to yesterday
today = date.today()
for days_ago in range(7, 0, -1):
    d = today - timedelta(days=days_ago)

    # Direct feed 1 at 09:00
    s1 = datetime.combine(d, time(9,0))
    e1 = s1 + timedelta(minutes=10 + (days_ago % 5) * 2)
    cur.execute("INSERT INTO direct_breastfeeding (start_time, end_time, notes, side, created_at, baby_id) VALUES (?, ?, ?, ?, ?, ?)",
                (iso(s1), iso(e1), '自动种子数据', 'both', iso(datetime.now()), baby_id))

    # Direct feed 2 at 15:00
    s2 = datetime.combine(d, time(15,0))
    e2 = s2 + timedelta(minutes=12 + (days_ago % 4) * 3)
    cur.execute("INSERT INTO direct_breastfeeding (start_time, end_time, notes, side, created_at, baby_id) VALUES (?, ?, ?, ?, ?, ?)",
                (iso(s2), iso(e2), '自动种子数据', 'left', iso(datetime.now()), baby_id))

    # Diaper wet at 11:30
    t_wet = datetime.combine(d, time(11,30))
    cur.execute("INSERT INTO diaper (diaper_type, timestamp, notes, created_at, baby_id) VALUES (?, ?, ?, ?, ?)",
                ('wet', iso(t_wet), '自动种子数据', iso(datetime.now()), baby_id))

    # Diaper dirty on even days_ago
    if days_ago % 2 == 0:
        t_dirty = datetime.combine(d, time(18,20))
        cur.execute("INSERT INTO diaper (diaper_type, timestamp, notes, created_at, baby_id) VALUES (?, ?, ?, ?, ?)",
                    ('dirty', iso(t_dirty), '自动种子数据', iso(datetime.now()), baby_id))

    # Sleep midday nap at 13:00
    nap_start = datetime.combine(d, time(13,0))
    nap_minutes = 30 + (days_ago * 25) % 180
    nap_end = nap_start + timedelta(minutes=nap_minutes)
    cur.execute("INSERT INTO sleep (start_time, end_time, notes, created_at, baby_id) VALUES (?, ?, ?, ?, ?)",
                (iso(nap_start), iso(nap_end), '自动种子午睡', iso(datetime.now()), baby_id))

    # Bottle breast feeding at 20:00
    bottle_time = datetime.combine(d, time(20,0))
    bottle_ml = 50 + (days_ago * 15) % 120
    cur.execute("INSERT INTO bottle_breast_feeding (timestamp, volume_ml, notes, created_at, baby_id) VALUES (?, ?, ?, ?, ?)",
                (iso(bottle_time), int(bottle_ml), '自动种子瓶喂', iso(datetime.now()), baby_id))

    # Formula feeding every 3rd day
    if days_ago % 3 == 0:
        formula_time = datetime.combine(d, time(19,0))
        formula_ml = 80 + (days_ago * 10) % 100
        cur.execute("INSERT INTO formula_feeding (timestamp, volume_ml, brand, notes, created_at, baby_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (iso(formula_time), int(formula_ml), 'Generic', '自动种子配方', iso(datetime.now()), baby_id))

# Ensure milk inventory
cur.execute("SELECT id, remaining_ml FROM milk_inventory WHERE baby_id = ?", (baby_id,))
inv = cur.fetchone()
if not inv:
    cur.execute("INSERT INTO milk_inventory (baby_id, remaining_ml, updated_at) VALUES (?, ?, ?)",
                (baby_id, 200, iso(datetime.now())))
    print("Created milk_inventory with 200 ml")
else:
    cur.execute("UPDATE milk_inventory SET remaining_ml = ?, updated_at = ? WHERE baby_id = ?", (max(inv[1],200), iso(datetime.now()), baby_id))
    print("Updated existing milk_inventory to at least 200 ml")

conn.commit()
print("Seeding complete.")
conn.close()
