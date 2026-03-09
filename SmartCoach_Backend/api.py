# 4. ملف api.py (حلقة الوصل بين الداتا بيز وتطبيق الموبايل)
# التعديل الجديد: دعم الـ Multi-User، حماية الـ CORS، وقفل الداتا بيز بنضافة.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db_manager import DatabaseManager

# 1. بنقوم السيرفر بتاعنا
app = FastAPI(title="SmartCoach API", description="Production API for Multi-User SmartCoach System")

# 🔥 إضافة معمارية مهمة جداً (CORS Middleware):
# ده بيسمح لأي تطبيق (سواء موبايل فلاتر مع محمد أشرف، أو ويب داشبورد) إنه يكلم الـ API من غير ما الموبايل يعمل Block للبيانات.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # بنسمح لأي جهة تكلم السيرفر (مهم جداً للـ Development)
    allow_credentials=True,
    allow_methods=["*"], # بنسمح بكل أنواع الـ Requests زي GET و POST
    allow_headers=["*"],
)

# بنفتح اتصال بالداتا بيز مرة واحدة لما السيرفر يقوم
db = DatabaseManager()

# 🔥 إضافة معمارية (Graceful Shutdown):
# الفنكشن دي بتشتغل أوتوماتيك لما تقفل السيرفر (بـ Ctrl+C)، عشان تقفل الداتا بيز بنضافة ومتعملش Memory Leak
@app.on_event("shutdown")
def shutdown_db():
    db.close()
    print("🛑 تم إغلاق الاتصال بقاعدة البيانات بنجاح.")

# 2. تعريف شكل الداتا اللي هتيجي من الموبايل وقت التسجيل (Data Validation)
# مكتبة Pydantic بتأكد إن الموبايل باعت الداتا دي بالظبط، ولو باعت حاجة ناقصة الـ API بيرفضها لوحده
class PlayerRegistration(BaseModel):
    name: str
    fitbit_access_token: str
    fitbit_refresh_token: str

# 3. تعريف شكل الداتا اللي هتيجي وقت بداية التمرين
class SessionStart(BaseModel):
    player_id: int
    exercise_type: str

# 🚀 Endpoint 0: دالة فحص السيرفر (Health Check)
# دي بنستخدمها عشان نتأكد إن السيرفر والـ Ngrok شغالين قبل ما الموبايل يبعت داتا حقيقية
@app.get("/")
def read_root():
    return {"status": "success", "message": "أهلاً بيك في باك إند SmartCoach (Multi-User) يا هندسة!"}

# 🚀 Endpoint 1: تسجيل لاعب جديد
@app.post("/register")
def register_player(data: PlayerRegistration):
    try:
        # بنرمي بيانات اللاعب والتوكنات في الداتا بيز
        player_id = db.register_player(data.name, data.fitbit_access_token, data.fitbit_refresh_token)
        return {"status": "success", "message": "تم تسجيل اللاعب بنجاح", "player_id": player_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🚀 Endpoint 2: بدء تمرينة جديدة (بيحدد مين اللي بيتمرن دلوقتي)
@app.post("/start_session")
def start_session(data: SessionStart):
    try:
        session_id = db.create_session(data.player_id, data.exercise_type)
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🚀 Endpoint 3: جلب الداتا اللايف (للموبايل والداشبورد)
# دي اللي الداشبورد أو الموبايل بيكلموها كل ثانية عشان يجيبوا الزاوية والنبض والعداد
@app.get("/live_data/{session_id}")
def get_live_data(session_id: str):
    data = db.get_live_data(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="مفيش داتا متسجلة للجلسة دي لسه")
    
    # رجعنا الداتا في نفس الشكل الموحد اللي الموبايل متعود عليه عشان محمد أشرف ميغيرش حاجة في الكود بتاعه
    return {
        "status": "success",
        "session_id": session_id,
        "data": data 
    }