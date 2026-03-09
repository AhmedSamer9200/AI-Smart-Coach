# 4. ملف api.py (حلقة الوصل بين الداتا بيز والفرونت إند/الموبايل)
# الملف ده هو السيرفر بتاعك اللي بيستقبل الطلبات ويرد عليها.
# المشروع بالكامل إعداد وبرمجة: م. أحمد سامر

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db_manager import DatabaseManager

# 1. بنقوم السيرفر بتاعنا وبنديله اسم ووصف احترافي
app = FastAPI(title="SmartCoach API", description="Production API for AI SmartCoach System")

# 🔥 حماية الـ CORS: 
# دي بتسمح للـ Streamlit (أو أي موبايل أبلكيشن) إنه يكلم السيرفر بتاعك من غير ما المتصفح يفتكره هاكر ويعمل Block.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # مسموح لأي جهة تكلم السيرفر
    allow_credentials=True,
    allow_methods=["*"], # مسموح بكل أنواع الطلبات (GET, POST, ...)
    allow_headers=["*"],
)

# بنفتح اتصال بالداتا بيز (العقل المدبر) مرة واحدة بس أول ما السيرفر يقوم
db = DatabaseManager()

# 🔥 القفل الآمن (Graceful Shutdown):
# لما تقفل السيرفر من التيرمينال (Ctrl+C)، الفنكشن دي بتقفل الداتا بيز بنضافة عشان متسيبش اتصالات مفتوحة (Memory Leak).
@app.on_event("shutdown")
def shutdown_db():
    db.close()
    print("🛑 تم إغلاق الاتصال بقاعدة البيانات بنجاح.")

# ==========================================
# 🛡️ Data Validation (هيكل البيانات المطلوبة)
# ==========================================
# مكتبة Pydantic بتجبر الواجهة إنها تبعت الداتا بالشكل ده بالظبط، ولو في حاجة ناقصة السيرفر بيرفضها فوراً (أمان عالي).

class PlayerRegistration(BaseModel):
    name: str
    fitbit_access_token: str
    fitbit_refresh_token: str

class SessionStart(BaseModel):
    player_id: int
    exercise_type: str

# ==========================================
# 🚀 الـ Endpoints (نقاط الاتصال)
# ==========================================

# 📍 Endpoint 0: فحص السيرفر (Health Check)
@app.get("/")
def read_root():
    return {"status": "success", "message": "أهلاً بيك في باك إند SmartCoach يا هندسة!"}

# 📍 Endpoint 1: تسجيل لاعب جديد وربط الساعة
@app.post("/register")
def register_player(data: PlayerRegistration):
    try:
        player_id = db.register_player(data.name, data.fitbit_access_token, data.fitbit_refresh_token)
        return {"status": "success", "message": "تم تسجيل اللاعب بنجاح", "player_id": player_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📍 Endpoint 2: بدء تمرينة جديدة 
@app.post("/start_session")
def start_session(data: SessionStart):
    try:
        session_id = db.create_session(data.player_id, data.exercise_type)
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📍 Endpoint 3: جلب الداتا اللايف (للتتبع المباشر)
@app.get("/live_data/{session_id}")
def get_live_data(session_id: str):
    data = db.get_live_data(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="مفيش داتا متسجلة للجلسة دي لسه")
    return {"status": "success", "session_id": session_id, "data": data}

# ==========================================
# 🔥 التعديلات الجديدة (نهاية التمرينة والملخص)
# ==========================================

# 📍 Endpoint 4: إنهاء الجلسة أوتوماتيك (بتخلي is_active = FALSE)
@app.post("/end_session/{session_id}")
def end_session(session_id: str):
    try:
        db.end_session(session_id)
        return {"status": "success", "message": "تم إنهاء الجلسة بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📍 Endpoint 5: جلب التقرير النهائي (Analytics)
@app.get("/session_summary/{session_id}")
def get_session_summary(session_id: str):
    data = db.get_session_summary(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="مفيش داتا مسجلة للجلسة دي عشان نعمل تقرير")
    return {"status": "success", "summary": data}