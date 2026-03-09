# 2. ملف fitbit_reader.py (القارئ الذكي المتصل بقاعدة البيانات)
# التعديل الجديد: دعم الـ Multi-User، قراءة التوكن من الداتا بيز بدلاً من الملفات، وتجديد التوكن التلقائي لكل يوزر.

import requests
import time
import os
from db_manager import DatabaseManager
from dotenv import load_dotenv

# 1. بنفتح الخزنة السرية عشان نجيب بيانات الأبلكيشن (مش بيانات اليوزر)
load_dotenv()
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")

# خطوة أمان للتأكد من وجود البيانات
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("❌ بيانات Fitbit مش موجودة في ملف .env")

# 🔥 تنظيف ذكي (Clean up): 
# لو لقينا ملف التوكنات القديم اللي كنا بنستخدمه زمان، بنمسحه عشان السيستم يعتمد كلياً على الداتا بيز
if os.path.exists("fitbit_tokens.json"):
    os.remove("fitbit_tokens.json")
    print("🧹 تم مسح ملف التوكنات القديم للاعتماد على قاعدة البيانات.")

# بنفتح اتصال بالداتا بيز
db = DatabaseManager()

# 🚀 2. الفنكشن اللي بتجدد التوكن وبتحفظه في الداتا بيز للاعب ده بالذات
def refresh_access_token(player_id, current_refresh_token):
    print(f"🔄 التوكن خلص للاعب رقم {player_id}.. بنجدده دلوقتي!")
    url = "https://api.fitbit.com/oauth2/token"
    auth = (CLIENT_ID, CLIENT_SECRET)
    
    # بنبعت الـ Refresh Token القديم عشان ناخد واحد جديد
    data = {
        "grant_type": "refresh_token",
        "refresh_token": current_refresh_token
    }
    
    try:
        response = requests.post(url, auth=auth, data=data)
        
        if response.status_code == 200:
            new_tokens = response.json()
            new_access = new_tokens.get("access_token")
            new_refresh = new_tokens.get("refresh_token")
            
            # 🔥 السحر هنا: بنحفظ التوكن الجديد في الداتا بيز لليوزر ده تحديداً
            db.update_fitbit_tokens(player_id, new_access, new_refresh)
            print("✅ تم تجديد التوكن وحفظه في الداتا بيز بنجاح!")
            return new_access
        else:
            print("❌ فشل تجديد التوكن:", response.json())
            return None
    except Exception as e:
        print(f"❌ مشكلة في الاتصال بسيرفرات فيتبيت لتجديد التوكن: {e}")
        return None

# 🚀 3. الفنكشن الأساسية اللي بتسحب النبض
def get_heart_rate():
    # الخطوة الأولى: بنسأل الداتا بيز: "مين اللاعب اللي الجلسة بتاعته شغالة دلوقتي؟"
    active_session = db.get_active_session_tokens()
    
    # لو مفيش جلسة شغالة، السيستم بينتظر ومبيسحبش حاجة عشان ميعملش ضغط على الـ API
    if not active_session:
        print("⏳ مفيش حد بيتمرن دلوقتي.. السيستم في وضع الانتظار.")
        return
        
    session_id = active_session["session_id"]
    player_id = active_session["player_id"]
    access_token = active_session["access_token"]
    refresh_token = active_session["refresh_token"]

    # لو اللاعب مسجلش توكن من الأساس
    if not access_token:
        print(f"⚠️ اللاعب رقم {player_id} مش مسجل توكن فيتبيت.")
        return

    # الخطوة التانية: بنكلم فيتبيت بتوكن اللاعب ده بالتحديد
    url = "https://api.fitbit.com/1/user/-/activities/heart/date/today/1d/1sec.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        # لو الطلب نجح والتوكن شغال
        if response.status_code == 200:
            data = response.json()
            try:
                # بنحاول نوصل لأحدث قراية في الداتا اللي راجعة
                dataset = data.get('activities-heart-intraday', {}).get('dataset', [])
                if dataset:
                    latest_hr = dataset[-1]['value'] # بنسحب آخر نبض
                    print(f"❤️ نبض اللاعب {player_id}: {latest_hr} bpm (Session: {session_id})")
                    
                    # 🔥 بنرمي النبض في الداتا بيز تحت الـ Session ID اللي شغالة دلوقتي
                    db.upsert_exercise_data(session_id=session_id, emg_val=float(latest_hr))
                else:
                    print(f"⚠️ مفيش داتا نبض متسجلة للاعب {player_id} النهاردة.")
            except Exception as parse_error:
                print(f"⚠️ مشكلة في تحليل بيانات النبض: {parse_error}")
                
        # لو التوكن خلصان (401 Unauthorized)
        elif response.status_code == 401:
            # بننده على دالة التجديد، وبنديها الـ Refresh Token بتاع اللاعب ده
            new_access = refresh_access_token(player_id, refresh_token)
            # لو اتجدد بنجاح، بننده على دالة سحب النبض مرة تانية عشان منضيعش القراية
            if new_access:
                get_heart_rate() 
        else:
            print(f"❌ مشكلة في السحب. كود الغلط: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ مشكلة في الاتصال بالإنترنت: {e}")

# 4. الـ Loop الأساسي لتشغيل الفايل
if __name__ == "__main__":
    print("🚀 تشغيل سيستم النبض (Multi-User Mode)...")
    try:
        while True:
            get_heart_rate()
            # بنسحب الداتا كل 5 ثواني عشان منعديش الـ Rate Limit بتاع فيتبيت (150 طلب في الساعة)
            time.sleep(5) 
    except KeyboardInterrupt:
        print("\n🛑 بنقفل السيستم...")
    finally:
        # تأمين قفل الداتا بيز
        db.close()