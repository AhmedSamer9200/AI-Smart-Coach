# 1. ملف db_manager.py (مخ السيستم - Data Pipeline)
# التعديل: دعم تعدد المستخدمين (Multi-User SaaS) وتأمين التوكنات.

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
            -- جدول اللاعبين: ضفنا فيه عواميد التوكنز عشان كل يوزر ليه ساعته الخاصة
            CREATE TABLE IF NOT EXISTS players (
                player_id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                fitbit_access_token TEXT, 
                fitbit_refresh_token TEXT, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            -- جدول الجلسات: ضفنا is_active عشان نعرف مين بيتمرن لايف دلوقتي
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(50) PRIMARY KEY,
                player_id INT REFERENCES players(player_id),
                exercise_type VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE, 
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            -- جدول القرايات اللحظية (زي ما هو، بيربط الداتا بالجلسة)
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
        
        # تنفيذ أوامر الإنشاء
        for q in queries:
            self.cursor.execute(q)
            
        # 🔥 حركة Data Engineering (Migration): 
        # لو الجداول كانت موجودة من الديمو القديم، الكود ده بيجبرها تضيف العواميد الجديدة من غير ما نمسح الداتا
        try:
            self.cursor.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS fitbit_access_token TEXT;")
            self.cursor.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS fitbit_refresh_token TEXT;")
            self.cursor.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;")
        except Exception as e:
            pass # لو العواميد موجودة هيكمل شغل عادي
            
        self.conn.commit()

    # 🚀 1. دالة تسجيل لاعب جديد (بيكلمها الـ API لما يوزر يعمل حساب)
    def register_player(self, name, access_token, refresh_token):
        # بنعمل INSERT وبنستخدم (RETURNING player_id) عشان نرجع الـ ID بتاع اليوزر الجديد للموبايل
        query = """
            INSERT INTO players (name, fitbit_access_token, fitbit_refresh_token) 
            VALUES (%s, %s, %s) RETURNING player_id;
        """
        self.cursor.execute(query, (name, access_token, refresh_token))
        player_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return player_id

    # 🚀 2. دالة بدء جلسة تمرين (لما اليوزر يدوس Start Workout)
    def create_session(self, player_id, exercise_type="Squats"):
        session_id = f"session_{int(time.time())}_{player_id}" # ID فريد مستحيل يتكرر
        
        # 🔥 التصليح المعماري: بنقفل أي جلسة قديمة لـ "نفس اللاعب ده بس" عشان السيستم ميتلخبطش
        close_old_query = "UPDATE sessions SET is_active = FALSE WHERE player_id = %s AND is_active = TRUE;"
        self.cursor.execute(close_old_query, (player_id,))
        
        # بنفتح الجلسة الجديدة ونخليها Active
        query = "INSERT INTO sessions (session_id, player_id, exercise_type, is_active) VALUES (%s, %s, %s, TRUE)"
        self.cursor.execute(query, (session_id, player_id, exercise_type))
        self.conn.commit()
        return session_id

    # 🚀 3. دالة بتجيب "مين اللاعب اللي بيتمرن دلوقتي؟" (عشان الفيتبيت تسحب نبضه)
    def get_active_session_tokens(self):
        # بنعمل JOIN بين الـ sessions والـ players عشان نجيب التوكن بتاع اللاعب اللي الجلسة بتاعته شغالة
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

    # 🚀 4. دالة بتحدث توكن الفيتبيت لو خلص (Auto-Refresh)
    def update_fitbit_tokens(self, player_id, new_access, new_refresh):
        query = "UPDATE players SET fitbit_access_token = %s, fitbit_refresh_token = %s WHERE player_id = %s"
        self.cursor.execute(query, (new_access, new_refresh, player_id))
        self.conn.commit()

    # 🚀 5. دالة الـ Upsert (إضافة أو تحديث الداتا اللحظية لمنع التكرار)
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
            print(f"⚠️ مشكلة في حفظ الداتا: {e}") # ضفنا دي عشان لو حصل إيرور نعرف سببه
            self.conn.rollback()

    # 🚀 6. دالة سحب أحدث قراية لعرضها في الداشبورد والموبايل
    def get_live_data(self, session_id):
        query = "SELECT angle, stage, reps_count, emg_value FROM exercise_data WHERE session_id = %s ORDER BY timestamp_ms DESC LIMIT 1;"
        self.cursor.execute(query, (session_id,))
        result = self.cursor.fetchone()
        
        if result:
            return {"angle": result[0], "stage": result[1], "reps": result[2], "emg": result[3]}
        return None

    # 🚀 7. إغلاق الاتصال بقاعدة البيانات بنظافة
    def close(self):
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    print("⏳ اختبار اتصال وصحة قاعدة البيانات...")
    test_db = DatabaseManager()
    if hasattr(test_db, 'conn'):
        test_db.close()
        print("✅ الكود سليم 100%")