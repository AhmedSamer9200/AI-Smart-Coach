# 4. ملف api.py (توصيل الداتا للموبايل أبلكيشن)
# ده الكود اللي محمد أشرف هيستخدمه. مبني بـ FastAPI عشان سريع جداً وبيطلع الداتا في شكل JSON جاهز.

from fastapi import FastAPI, HTTPException
from db_manager import DatabaseManager

# بنعمل الأبلكيشن بتاعنا
app = FastAPI(title="SmartCoach API", description="API for Mobile Application")
db = DatabaseManager()

@app.get("/")
def read_root():
    return {"message": "أهلاً بيك في باك إند SmartCoach يا هندسة!"}

# الـ Endpoint دي الموبايل هيكلمها كل ثانية عشان يجيب أجدد قراية للاعب وهو بيتمرن
@app.get("/session/{session_id}/live")
def get_live_session_data(session_id: str):
    data = db.get_live_data(session_id)
    
    if data:
        return {
            "status": "success",
            "session_id": session_id,
            "data": data # دي فيها الزاوية، العداد، وإشارة العضلة
        }
    else:
        # لو مفيش داتا لسه، هنبعت إيرور 404
        raise HTTPException(status_code=404, detail="مفيش داتا للتمرينة دي لسه")