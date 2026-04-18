import json
import os
from kafka import KafkaConsumer
from database import get_db_connection, init_db

# إعدادات من الـ Environment Variables
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'equipment_status')

# إنشاء الجداول عند بدء الخدمة
init_db()

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    # التعديل: استخدام deserializer لتحويل البيانات المستلمة
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='backend-group' # إضافة Group ID لضمان استقرار الاستهلاك
)

print(f"Backend Consumer is running on topic [{KAFKA_TOPIC}]...")

def update_equipment_stats(data):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # استخراج البيانات بناءً على الـ Payload الجديد اللي عملناه
    eq_id = data['equipment_id']
    # ملاحظة: الحالة بقت بتيجي تحت مفتاح 'state' و 'activity'
    is_active = 1 if data['state'] == "ACTIVE" else 0
    is_idle = 1 if data['state'] == "INACTIVE" else 0
    activity = data['activity']
    
    # تحديث البيانات (UPSERT)
    # ملاحظة: قسمنا الـ Utilization على total_tracked_seconds عشان تطلع نسبة مئوية صحيحة
    query = """
    INSERT INTO equipment_summary (
        equipment_id, total_active_seconds, total_idle_seconds, 
        total_tracked_seconds, last_activity
    )
    VALUES (%s, %s, %s, 1, %s)
    ON CONFLICT (equipment_id) DO UPDATE SET
        total_active_seconds = equipment_summary.total_active_seconds + EXCLUDED.total_active_seconds,
        total_idle_seconds = equipment_summary.total_idle_seconds + EXCLUDED.total_idle_seconds,
        total_tracked_seconds = equipment_summary.total_tracked_seconds + 1,
        last_activity = EXCLUDED.last_activity,
        utilization_percent = (
            (CAST(equipment_summary.total_active_seconds + EXCLUDED.total_active_seconds AS FLOAT) / 
             CAST(equipment_summary.total_tracked_seconds + 1 AS FLOAT)) * 100
        ),
        last_updated = CURRENT_TIMESTAMP;
    """
    
    try:
        cur.execute(query, (eq_id, is_active, is_idle, activity))
        conn.commit()
    except Exception as e:
        print(f"Database Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# Loop الاستقبال
for message in consumer:
    payload = message.value
    # طباعة بسيطة للـ Debugging للتأكد من وصول البيانات
    print(f"📥 Received: {payload['equipment_id']} | State: {payload['state']} | Activity: {payload['activity']}")
    update_equipment_stats(payload)