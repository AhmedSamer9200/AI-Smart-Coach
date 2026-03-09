# 2. ملف fitbit_reader.py (سحب النبض اللحظي)
# التعديل الجديد: تم إخفاء الـ CLIENT_ID والـ CLIENT_SECRET في الخزنة السرية (.env) لحماية الأكونت.

import requests
import time
import json
import os
from db_manager import DatabaseManager # 🔥 ربطنا الداتا بيز هنا عشان نرمي النبض فيها
from dotenv import load_dotenv # 🔥 استدعاء مكتبة الخزنة

# 1. بنفتح الخزنة السرية
load_dotenv()

# 2. بيانات الأبلكيشن بتاعك من موقع Fitbit Developer
# بنسحب الباسوردات السرية من الخزنة بدل ما تكون مكشوفة في الكود
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")

# 🔥 خطوة أمان إضافية: بنطمن إن الداتا اتسحبت صح من ملف الـ .env
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("❌ بيانات Fitbit مش موجودة! اتأكد إنك كاتب FITBIT_CLIENT_ID و FITBIT_CLIENT_SECRET في ملف .env")

# الملف ده اللي هنحفظ فيه التوكنز عشان لو قفلنا وشغلنا تاني ميرجعش يطلب صلاحيات من الأول
TOKEN_FILE = "fitbit_tokens.json"

# 3. بنفتح اتصال بالداتا بيز
db = DatabaseManager()

# 🔥 التعديل السحري: توحيد الـ Session ID
# خلينا الـ ID ده نفس اللي الكاميرا بتسجل بيه، عشان النبض والحركة يتسجلوا لنفس الجلسة وفي نفس اللحظة
session_id = "smartcoach_live_session" 

# 4. الداتا الأولية بتاعتك (التصاريح المبدئية)
# الـ Access token ده المفتاح المؤقت (بيخلص كل 8 ساعات)
# الـ Refresh token ده المفتاح الماستر اللي بنجيب بيه access token جديد لو القديم خلص
INITIAL_TOKENS = {
    "access_token": "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyM1RZRDciLCJzdWIiOiJEMzZEVFkiLCJpc3MiOiJGaXRiaXQiLCJ0eXAiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZXMiOiJyc29jIHJlY2cgcnNldCByaXJuIHJveHkgcm51dCBycHJvIHJzbGUgcmNmIHJhY3QgcnJlcyBybG9jIHJ3ZWkgcmhyIHJ0ZW0iLCJleHAiOjE3NzI5NDUzNjgsImlhdCI6MTc3MjkxNjU2OH0.HhJa608c1PX6jD2GAp830kCkQWMCZR1T3Mv0oM65ftY",
    "refresh_token": "02349f0764756c82a5867028904a80465e3747ea5ae3b8ba8b4fd86aa60120e4"
}

# الفنكشن دي بتقرأ التوكنز من الملف، ولو الملف مش موجود بتعمله وتحط فيه الداتا الأولية
def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'w') as f:
            json.dump(INITIAL_TOKENS, f)
        return INITIAL_TOKENS
    with open(TOKEN_FILE, 'r') as f:
        return json.load(f)

# الفنكشن دي بتحفظ التوكنز الجديدة في الملف بعد ما تتحدث
def save_tokens(token_data):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)

# 5. ذكاء السيستم (Auto-Refresh)
# الفنكشن دي بتشتغل لوحدها لو السيرفر قالنا إن التوكن خلص (كود 401)
# بتروح تكلم فيتبيت بالمفتاح الماستر وتجيب مفتاح مؤقت جديد وتكمل شغل من غير ما السيستم يقع
def refresh_access_token(current_refresh_token):
    print("🔄 التوكن خلص.. السيستم بيجدده أوتوماتيك دلوقتي!")
    url = "https://api.fitbit.com/oauth2/token"
    
    auth = (CLIENT_ID, CLIENT_SECRET)
    data = {
        "grant_type": "refresh_token",
        "refresh_token": current_refresh_token
    }
    
    response = requests.post(url, auth=auth, data=data)
    
    if response.status_code == 200:
        new_tokens = response.json()
        save_tokens(new_tokens) 
        print("✅ تم تجديد التوكن بنجاح ومكملين شغل!")
        return new_tokens
    else:
        print("❌ فشل تجديد التوكن، الغلطة من فيتبيت:", response.json())
        return None

# 6. الفنكشن الأساسية اللي بتسحب النبض وتوديه الداتا بيز
def get_heart_rate():
    tokens = load_tokens()
    access_token = tokens.get("access_token")
    
    # اللينك ده بيسحب داتا النبض اللحظية (Intraday) بتاعة النهاردة بثانية بثانية
    url = "https://api.fitbit.com/1/user/-/activities/heart/date/today/1d/1sec.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        # لو الرد سليم (200 OK)
        if response.status_code == 200:
            data = response.json()
            try:
                dataset = data['activities-heart-intraday']['dataset']
                if dataset:
                    # بنجيب آخر قراية نبض اتسجلت (آخر عنصر في اللستة)
                    latest_hr = dataset[-1]['value']
                    latest_time = dataset[-1]['time']
                    print(f"❤️ أحدث نبض: {latest_hr} bpm (متسجل الساعة: {latest_time})")
                    
                    # 🔥 بنبعت النبض ده للداتا بيز الموحدة
                    # بنحطه في خانة emg_val مؤقتا كطريقة لدمج الفسيولوجي مع الحركي
                    db.upsert_exercise_data(session_id=session_id, emg_val=float(latest_hr))
                    
                    return latest_hr
                else:
                    print("⚠️ مفيش داتا نبض متسجلة النهاردة. اتأكد إنك لابس الساعة وعامل Sync.")
            except KeyError:
                pass
                
        # لو التوكن خلصان (401 Unauthorized)
        elif response.status_code == 401:
            new_tokens = refresh_access_token(tokens.get("refresh_token"))
            # لو عرف يجدد التوكن، بيرجع ينده على نفسه تاني عشان يسحب الداتا
            if new_tokens:
                return get_heart_rate() 
        else:
            print(f"❌ حصل مشكلة في السحب. كود الغلط: {response.status_code}")
            
    except Exception as e:
        print(f"❌ مشكلة في الاتصال بالإنترنت: {e}")

# 7. ده الـ Loop الأساسي اللي بيخلي الفايل يشتغل على طول أول ما تعمله Run
if __name__ == "__main__":
    print("🚀 تشغيل سيستم النبض الذكي المستمر...")
    try:
        while True:
            get_heart_rate()
            time.sleep(5) # بنسحب الداتا كل 5 ثواني عشان مفيش ضغط على API فيتبيت
    except KeyboardInterrupt:
        # لو قفلنا السكريبت بـ Ctrl+C
        print("\n🛑 بنقفل السيستم...")
    finally:
        # لازم نقفل الاتصال بالداتا بيز بنضافة عشان السيرفر ميهنجش
        db.close()