import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        host="timescaledb", # اسم الخدمة في docker-compose
        database="construction_db",
        user="user",
        password="pass"
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # إنشاء جدول لتخزين ملخص حالة كل معدة
    cur.execute('''
        CREATE TABLE IF NOT EXISTS equipment_summary (
            equipment_id VARCHAR(50) PRIMARY KEY,
            total_active_seconds FLOAT DEFAULT 0,
            total_idle_seconds FLOAT DEFAULT 0,
            total_tracked_seconds FLOAT DEFAULT 0,
            utilization_percent FLOAT DEFAULT 0,
            last_activity VARCHAR(50),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_db()