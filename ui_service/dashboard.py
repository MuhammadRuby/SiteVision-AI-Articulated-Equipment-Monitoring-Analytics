import streamlit as st
import pandas as pd
import psycopg2
import time
import os

# 1. إعدادات الصفحة الاحترافية
st.set_page_config(
    page_title="EagleVision Construction AI",
    page_icon="🏗️",
    layout="wide"
)

def get_db_connection():
    try:
        # استخدام المتغيرات من Docker Environment
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "timescaledb"),
            database=os.getenv("DB_NAME", "construction_db"),
            user=os.getenv("DB_USER", "user"),
            password=os.getenv("DB_PASS", "pass")
        )
    except:
        return None

# العنوان والـ Sidebar
st.title("🏗️ EagleVision: Construction Equipment Real-time Monitor")
st.sidebar.header("System Status")
st.sidebar.success("CV Service: Online")
st.sidebar.success("Kafka: Connected")

# أماكن عرض البيانات (Placeholders)
main_container = st.empty()

while True:
    conn = get_db_connection()
    if conn:
        # جلب البيانات وترتيبها حسب آخر تحديث
        query = "SELECT * FROM equipment_summary ORDER BY last_updated DESC;"
        df = pd.read_sql(query, conn)
        conn.close()

        if not df.empty:
            with main_container.container():
                # 2. عرض الـ Global Metrics (نظرة عامة)
                avg_util = df['utilization_percent'].mean()
                active_count = len(df[df['last_activity'] != 'WAITING'])
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Tracked Machines", len(df))
                m2.metric("Currently Active", active_count)
                m3.metric("Fleet Utilization", f"{avg_util:.1f}%")
                
                st.divider()

                # 3. عرض البطاقات التفصيلية لكل معدة باستخدام Columns
                # هنعرض كل معدتين في صف واحد عشان الـ Layout ميبقاش طويل جداً
                for i in range(0, len(df), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(df):
                            row = df.iloc[i + j]
                            with cols[j].expander(f"Machine: {row['equipment_id']}", expanded=True):
                                c1, c2, c3 = st.columns(3)
                                
                                # تحديد لون الحالة
                                status_color = "green" if row['last_activity'] != "WAITING" else "orange"
                                c1.markdown(f"**Status:** :{status_color}[{row['last_activity']}]")
                                
                                c2.metric("Active Time", f"{row['total_active_seconds']:.1f}s")
                                
                                util = row['utilization_percent']
                                c3.metric("Utilization", f"{util:.1f}%")
                                
                                # بار التقدم
                                st.progress(min(util/100, 1.0))
                                st.caption(f"Last updated: {row['last_updated']}")

                # 4. الرسوم البيانية في الأسفل
                st.write("### 📊 Fleet Performance Analytics")
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    st.write("Active vs Idle Time (Seconds)")
                    st.bar_chart(df.set_index('equipment_id')[['total_active_seconds', 'total_idle_seconds']])
                
                with chart_col2:
                    st.write("Utilization Percentage by Machine")
                    # رسمة بسيطة لنسبة الاستخدام
                    st.line_chart(df.set_index('equipment_id')['utilization_percent'])

        else:
            st.info("🔄 Waiting for data from Computer Vision service...")
    else:
        st.error("❌ Database connection failed. Retrying...")
    
    time.sleep(1)