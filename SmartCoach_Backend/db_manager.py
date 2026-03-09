# 1. ملف db_manager.py (مخ السيستم - Data Pipeline)
# الملف ده هو المسئول عن إدارة قاعدة البيانات بالكامل.
# التعديل الجديد: تم تأمين الملف بالكامل وبقينا بنسحب الباسوردات من الخزنة السرية (.env)

import psycopg2
import uuid
import time
import os
from dotenv import load_dotenv

# 2. بنفتح الخزنة السرية اللي فيها الباسوردات
load_dotenv()

# 3. بنسحب اللينك السري من الخزنة
# استخدام os.getenv بيخلي الكود آمن جداً ومفيش أي باسوردات هتبان على جيت هاب
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

# 🔥 خطوة أمان إضافية (Best Practice): 
# بنتأكد إن اللينك فعلاً اتسحب وموجود، عشان لو نسينا نعمل ملف .env السيستم ينبهنا فوراً
if not NEON_DATABASE_URL:
    raise ValueError("❌ مفيش لينك للداتا بيز! اتأكد إنك عامل ملف .env وكاتب فيه NEON_DATABASE_URL")

class DatabaseManager:
    def __init__(self):
        # 4. دي أول فنكشن بتشتغل أول ما ننده على الكلاس (Constructor)
        # بتحاول تفتح اتصال بالداتا بيز السحابية بتاعة Neon
        try:
            self.conn = psycopg2.connect(NEON_DATABASE_URL)
            self.cursor = self.conn.cursor()
            print("✅ تم الاتصال بقاعدة البيانات السحابية (Neon.tech) بنجاح!")
            self._create_tables()
        except Exception as e:
            print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")

    def _create_tables(self):
        # 5. الفنكشن دي بتضمن إن الجداول (Schema) موجودة وتتكريت أوتوماتيك لو مش موجودة
        # استخدام IF NOT EXISTS بيخلي الكود آمن تماماً (Idempotent) حتى لو اشتغل 100 مرة
        queries = [
            """
            -- جدول اللاعبين
            CREATE TABLE IF NOT EXISTS players (
                player_id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            -- جدول التمارين (الجلسات) اللي بيربط كل تمرينة بلاعب معين
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(50) PRIMARY KEY,
                player_id INT REFERENCES players(player_id),
                exercise_type VARCHAR(50),
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            -- جدول القرايات (البيانات اللحظية للعداد والنبض والحركة)
            CREATE TABLE IF NOT EXISTS exercise_data (
                reading_id VARCHAR(100) PRIMARY KEY,
                session_id VARCHAR(50) REFERENCES sessions(session_id),
                timestamp_ms BIGINT,
                angle FLOAT,
                stage VARCHAR(10),
                reps_count INT,
                emg_value FLOAT, -- 💡 ده العمود اللي بنسجل فيه نبضات القلب دلوقتي
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        # بنلف على الاستعلامات وننفذها واحد واحد
        for q in queries:
            self.cursor.execute(q)
        self.conn.commit() # بنأكد الحفظ في الداتا بيز
        print("✅ الجداول السحابية جاهزة وشغالة")

    def create_session(self, player_id=1, exercise_type="Squats"):
        # 6. الفنكشن دي بتعمل جلسة تمرين جديدة
        # بنستخدم uuid عشان نعمل ID عشوائي ومميز مستحيل يتكرر
        session_id = str(uuid.uuid4())
        
        # حركة صياعة (Data Engineering): بندخل بيانات لاعب افتراضي الأول
        # و(ON CONFLICT DO NOTHING) معناها لو اللاعب موجود متعملش إيرور وكمل شغل عادي
        self.cursor.execute("INSERT INTO players (player_id, name) VALUES (1, 'Ahmed') ON CONFLICT (player_id) DO NOTHING;")
        
        # بنسجل التمرينة الجديدة
        query = "INSERT INTO sessions (session_id, player_id, exercise_type) VALUES (%s, %s, %s)"
        self.cursor.execute(query, (session_id, player_id, exercise_type))
        self.conn.commit()
        return session_id

    def upsert_exercise_data(self, session_id, angle=None, stage=None, reps=0, emg_val=None):
        # 7. الفنكشن دي هي اللي بترمي الداتا اللحظية (زي النبض والعداد)
        current_time_ms = int(time.time() * 1000)
        reading_id = f"{session_id}_{current_time_ms}"

        # استخدمنا تقنية الـ Upsert (ON CONFLICT DO UPDATE)
        # دي بتخلي السيستم يـ Insert الداتا، ولو الـ ID ده موجود قبل كده بيعمله Update
        # ده بيمنع أي Data Duplication ويخلي الداتا بيز السحابية نضيفة
        query = """
            INSERT INTO exercise_data (reading_id, session_id, timestamp_ms, angle, stage, reps_count, emg_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (reading_id) 
            DO UPDATE SET 
                angle = EXCLUDED.angle,
                stage = EXCLUDED.stage,
                reps_count = EXCLUDED.reps_count,
                emg_value = EXCLUDED.emg_value;
        """
        try:
            self.cursor.execute(query, (reading_id, session_id, current_time_ms, angle, stage, reps, emg_val))
            self.conn.commit()
        except Exception as e:
            print(f"⚠️ مشكلة في حفظ الداتا السحابية: {e}")
            self.conn.rollback() # لو حصل مشكلة بنتراجع عن العملية عشان الداتا بيز متهنجش

    def get_live_data(self, session_id):
        # 8. الفنكشن المسئولة عن قراية البيانات (بيكلمها الـ API عشان يدي الداتا للموبايل)
        # بنرتب القرايات تنازلياً (DESC) بالوقت وبناخد أول واحدة (LIMIT 1) عشان نجيب أحدث نبض وعداد
        query = """
            SELECT angle, stage, reps_count, emg_value 
            FROM exercise_data 
            WHERE session_id = %s 
            ORDER BY timestamp_ms DESC LIMIT 1;
        """
        self.cursor.execute(query, (session_id,))
        result = self.cursor.fetchone()
        
        # لو رجع داتا بنرتبها في شكل Dictionary عشان الـ API يفهمها ويحولها JSON بسهولة
        if result:
            return {"angle": result[0], "stage": result[1], "reps": result[2], "emg": result[3]}
        return None

    def close(self):
        # 9. بنقفل الاتصال بقاعدة البيانات بنضافة عشان منستهلكش موارد السيرفر
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    # 10. ده كود تجريبي بيشتغل بس لو عملت Run للملف ده لوحده للتأكد إن كله سليم
    print("⏳ جاري اختبار الاتصال بقاعدة البيانات السحابية (Neon)...")
    test_db = DatabaseManager()
    
    # التأكد من إن الاتصال موجود قبل ما نقفله
    if hasattr(test_db, 'conn'):
        test_db.close()
        print("✅ تم قفل الاتصال بعد التجربة بنجاح")