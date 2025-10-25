"""Seed seven days of sample data for the baby named '李望舒'.

Usage: from project root run:
    python3 scripts/seed_weekly.py

This script uses the app factory so it will honor the configured database.
"""
from datetime import datetime, date, time, timedelta
from app import create_app, db
from app.models.models import (
    Baby, DirectBreastfeeding, Diaper, Sleep, BottleBreastFeeding, FormulaFeeding, MilkInventory
)

app = create_app()

def seed_for_baby(baby_name: str):
    with app.app_context():
        baby = Baby.query.filter_by(name=baby_name).first()
        if not baby:
            print(f"No baby found with name '{baby_name}'. Aborting.")
            return

        today = datetime.now().date()
        created = []

        # For days 7..1 days ago (7 days ago up to yesterday)
        for days_ago in range(7, 0, -1):
            d = today - timedelta(days=days_ago)

            # Create two direct-breast records per day at 09:00 and 15:00 with small varying durations
            s1 = datetime.combine(d, time(9, 0))
            e1 = s1 + timedelta(minutes=10 + (days_ago % 5) * 2)
            db.session.add(DirectBreastfeeding(start_time=s1, end_time=e1, side='both', baby_id=baby.id))

            s2 = datetime.combine(d, time(15, 0))
            e2 = s2 + timedelta(minutes=12 + (days_ago % 4) * 3)
            db.session.add(DirectBreastfeeding(start_time=s2, end_time=e2, side='left', baby_id=baby.id))

            # Diaper: alternate wet/dirty, always add one wet; on even days add a dirty
            t_wet = datetime.combine(d, time(11, 30))
            db.session.add(Diaper(timestamp=t_wet, diaper_type='wet', notes='自动种子数据', baby_id=baby.id))

            if days_ago % 2 == 0:
                t_dirty = datetime.combine(d, time(18, 20))
                db.session.add(Diaper(timestamp=t_dirty, diaper_type='dirty', notes='自动种子数据', baby_id=baby.id))

            # Sleep: midday nap with varying durations (30..210 minutes)
            nap_start = datetime.combine(d, time(13, 0))
            nap_minutes = 30 + (days_ago * 25) % 180
            nap_end = nap_start + timedelta(minutes=nap_minutes)
            db.session.add(Sleep(start_time=nap_start, end_time=nap_end, notes='自动种子午睡', baby_id=baby.id))

            # Bottle breast feeding (母乳瓶喂) in evening
            bottle_time = datetime.combine(d, time(20, 0))
            bottle_ml = 50 + (days_ago * 15) % 120
            db.session.add(BottleBreastFeeding(timestamp=bottle_time, volume_ml=int(bottle_ml), notes='自动种子瓶喂', baby_id=baby.id))

            # Formula feeding on every 3rd day
            if days_ago % 3 == 0:
                formula_time = datetime.combine(d, time(19, 0))
                formula_ml = 80 + (days_ago * 10) % 100
                db.session.add(FormulaFeeding(timestamp=formula_time, volume_ml=int(formula_ml), notes='自动种子配方', baby_id=baby.id))

        # Optionally ensure there's a MilkInventory record
        inv = MilkInventory.query.filter_by(baby_id=baby.id).first()
        if not inv:
            inv = MilkInventory(baby_id=baby.id, remaining_ml=200)
            db.session.add(inv)
        else:
            # bump it slightly so UI shows non-zero
            inv.remaining_ml = max(inv.remaining_ml, 200)
            inv.updated_at = datetime.now()

        db.session.commit()
        print(f"Seeded 7 days of data for baby '{baby_name}' (id={baby.id}).")

if __name__ == '__main__':
    seed_for_baby('李望舒')
