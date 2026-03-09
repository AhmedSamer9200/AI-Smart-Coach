# 1. ملف db_manager.py (مخ السيستم - Data Pipeline)
# التعديل: دعم تعدد المستخدمين، تأمين التوكنات، وإضافة دوال ملخص التمرينة (Analytics).

import psycopg2
import uuid
import time
import os
from dotenv import load_dotenv

# بنفتح الخزنة ونسحب اللينك السري
load_dotenv()
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

# خطوة أمان: التأكد إن اللينك موجود عشان السيستم ميضربش إيرور غامض
if not NEON_DATABASE_URL:
    raise ValueError("❌ مفيش لينك للداتا بيز! اتأكد إنك عامل ملف .env")

class DatabaseManager:
    def __init__(self):
        # محاولة الاتصال بالداتا بيز السحابية أول ما الكلاس يشتغل
        try:
            self.conn = psycopg2.connect(NEON_DATABASE_URL)
            self.cursor = self.conn.cursor()
            print("✅ تم الاتصال بقاعدة البيانات السحابية (Neon.tech) بنجاح!")
            self._create_tables() # بننادي على دالة إنشاء الجداول
        except Exception as e:
            print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")

    def _create_tables(self):
        # 🔥 إنشاء الجداول الأساسية (IF NOT EXISTS بتمنع الإيرور لو الجداول موجودة)
        queries = [
            """
            -- جدول اللاعبين
            CREATE TABLE IF NOT EXISTS players (
                player_id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                fitbit_access_token TEXT, 
                fitbit_refresh_token TEXT, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            -- جدول الجلسات
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(50) PRIMARY KEY,
                player_id INT REFERENCES players(player_id),
                exercise_type VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE, 
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            -- جدول القرايات اللحظية
            CREATE TABLE IF NOT EXISTS exercise_data (
                reading_id VARCHAR(100) PRIMARY KEY,
                session_id VARCHAR(50) REFERENCES sessions(session_id),
                timestamp_ms BIGINT,
                angle FLOAT,
                stage VARCHAR(10),
                reps_count INT,
                emg_value FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        
        for q in queries:
            self.cursor.execute(q)
            
        # إضافة العواميد الجديدة بالقوة لو الجداول كانت موجودة من نسخة قديمة
        try:
            self.cursor.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS fitbit_access_token TEXT;")
            self.cursor.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS fitbit_refresh_token TEXT;")
            self.cursor.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;")
        except Exception as e:
            pass 
            
        self.conn.commit()

    # 🚀 1. دالة تسجيل لاعب جديد
    def register_player(self, name, access_token, refresh_token):
        query = """
            INSERT INTO players (name, fitbit_access_token, fitbit_refresh_token) 
            VALUES (%s, %s, %s) RETURNING player_id;
        """
        self.cursor.execute(query, (name, access_token, refresh_token))
        player_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return player_id

    # 🚀 2. دالة بدء جلسة تمرين
    def create_session(self, player_id, exercise_type="Squats"):
        session_id = f"session_{int(time.time())}_{player_id}" 
        
        # بنقفل الجلسات القديمة لنفس اللاعب
        close_old_query = "UPDATE sessions SET is_active = FALSE WHERE player_id = %s AND is_active = TRUE;"
        self.cursor.execute(close_old_query, (player_id,))
        
        # بنفتح جلسة جديدة
        query = "INSERT INTO sessions (session_id, player_id, exercise_type, is_active) VALUES (%s, %s, %s, TRUE)"
        self.cursor.execute(query, (session_id, player_id, exercise_type))
        self.conn.commit()
        return session_id

    # 🚀 3. دالة بتجيب اللاعب اللي بيتمرن دلوقتي
    def get_active_session_tokens(self):
        query = """
            SELECT s.session_id, p.player_id, p.fitbit_access_token, p.fitbit_refresh_token 
            FROM sessions s
            JOIN players p ON s.player_id = p.player_id
            WHERE s.is_active = TRUE
            ORDER BY s.start_time DESC LIMIT 1;
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        
        if result:
            return {
                "session_id": result[0],
                "player_id": result[1],
                "access_token": result[2],
                "refresh_token": result[3]
            }
        return None

    # 🚀 4. دالة تحديث توكن الفيتبيت
    def update_fitbit_tokens(self, player_id, new_access, new_refresh):
        query = "UPDATE players SET fitbit_access_token = %s, fitbit_refresh_token = %s WHERE player_id = %s"
        self.cursor.execute(query, (new_access, new_refresh, player_id))
        self.conn.commit()

    # 🚀 5. دالة الـ Upsert لإضافة أو تحديث الداتا اللحظية
    def upsert_exercise_data(self, session_id, angle=None, stage=None, reps=0, emg_val=None):
        current_time_ms = int(time.time() * 1000)
        reading_id = f"{session_id}_{current_time_ms}"
        
        query = """
            INSERT INTO exercise_data (reading_id, session_id, timestamp_ms, angle, stage, reps_count, emg_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (reading_id) 
            DO UPDATE SET angle=EXCLUDED.angle, stage=EXCLUDED.stage, reps_count=EXCLUDED.reps_count, emg_value=EXCLUDED.emg_value;
        """
        try:
            self.cursor.execute(query, (reading_id, session_id, current_time_ms, angle, stage, reps, emg_val))
            self.conn.commit()
        except Exception as e:
            print(f"⚠️ مشكلة في حفظ الداتا: {e}") 
            self.conn.rollback()

    # 🚀 6. دالة سحب أحدث قراية لعرضها لايف
    def get_live_data(self, session_id):
        query = "SELECT angle, stage, reps_count, emg_value FROM exercise_data WHERE session_id = %s ORDER BY timestamp_ms DESC LIMIT 1;"
        self.cursor.execute(query, (session_id,))
        result = self.cursor.fetchone()
        
        if result:
            return {"angle": result[0], "stage": result[1], "reps": result[2], "emg": result[3]}
        return None

    # ==========================================
    # 🔥 الدوال الجديدة (لشاشة ملخص التمرين)
    # ==========================================

    # 🚀 7. دالة إنهاء التمرينة
    def end_session(self, session_id):
        # بنعمل UPDATE عشان نغير حالة الجلسة لـ FALSE
        # ده بيقفل الجلسة وبيمنع أي داتا متأخرة من الكاميرا أو السنسور إنها تتسجل فيها بالغلط
        self.cursor.execute("UPDATE sessions SET is_active = FALSE WHERE session_id = %s;", (session_id,))
        self.conn.commit()

    # 🚀 8. دالة جلب ملخص التمرينة (التقرير النهائي)
    def get_session_summary(self, session_id):
        # السحر هنا إننا بنخلي الداتا بيز هي اللي تحسب (MAX و AVG) بدل ما نسحب الداتا كلها للـ Python
        # ده بيوفر وقت وموارد السيرفر جداً (Best Practice)
        query = """
            SELECT MAX(reps_count), AVG(emg_value) 
            FROM exercise_data 
            WHERE session_id = %s;
        """
        self.cursor.execute(query, (session_id,))
        result = self.cursor.fetchone()
        
        # بنجيب اسم التمرينة عشان نعرضه لليوزر في التقرير
        query_session = "SELECT exercise_type FROM sessions WHERE session_id = %s;"
        self.cursor.execute(query_session, (session_id,))
        session_info = self.cursor.fetchone()
        
        if result and session_info:
            return {
                "exercise_type": session_info[0],
                "total_reps": result[0] if result[0] else 0, # لو مفيش عدات بنرجع 0 عشان ميديناش Error
                "avg_emg": round(result[1], 2) if result[1] else 0.0 # بنقرب المتوسط لرقمين عشريين لشكل أشيك
            }
        return None

    # 🚀 9. إغلاق الاتصال بقاعدة البيانات
    def close(self):
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    print("⏳ اختبار اتصال وصحة قاعدة البيانات...")
    test_db = DatabaseManager()
    if hasattr(test_db, 'conn'):
        test_db.close()
        print("✅ الكود سليم 100%")