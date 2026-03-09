#!/bin/bash

echo "🚀 Starting SmartCoach FULL Ecosystem (Bashmohndes Ahmed Edition)..."

# 1. الدخول لفولدر الباك إند وتفعيل البيئة الوهمية (عشان المكتبات تشتغل صح)
# ضفنا "|| exit" كحماية إضافية، عشان لو الفولدر مش موجود السكريبت يقف فوراً وميعملش مشاكل
cd SmartCoach_Backend || exit
source myenv/bin/activate

# 2. تشغيل الـ API (FastAPI) في الخلفية وتسجيل الـ Output في ملف uvicorn.log
echo "🌐 Starting FastAPI (Backend)..."
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
API_PID=$! # بنحفظ رقم الـ ID بتاع العملية دي عشان نقدر نقفلها بعدين بنضافة

# 3. تشغيل كود سحب النبض من الفيتبيت في الخلفية
echo "❤️ Starting Fitbit Reader..."
python3 fitbit_reader.py > fitbit.log 2>&1 &
FIT_PID=$!

# 4. تشغيل كود الكاميرا والذكاء الاصطناعي (Mediapipe & Deep Learning)
echo "📷 Starting Camera Tracker..."
python3 camera_tracker.py > camera.log 2>&1 &
CAM_PID=$!

# 5. تشغيل الداشبورد بتاعة المدرب (Streamlit)
echo "📊 Starting Streamlit Dashboard..."
python3 -m streamlit run dashboard.py > dashboard.log 2>&1 &
DASH_PID=$!

# 6. تشغيل سينسور العضلات (معمول كومنت مؤقتاً لحد ما البوردة توصل)
# echo "⚡ Starting EMG Reader..."
# python3 emg_reader.py > emg.log 2>&1 &
# EMG_PID=$!

# 7. 🔥 التعديل الجديد: تشغيل Ngrok على اللينك الثابت بتاعك
# الميزة هنا إننا مش بنعمل Extract أو نكلم الـ Local API، اللينك بيقوم فوراً ومستقر للأبد
MY_NGROK_DOMAIN="octangular-maxim-sparkishly.ngrok-free.dev"

echo "🌐 Starting Ngrok Tunnel on static domain: $MY_NGROK_DOMAIN..."
ngrok http --domain=$MY_NGROK_DOMAIN 8000 > ngrok.log 2>&1 &
NGROK_PID=$!

# بنستنى ثانيتين بس (بدل 5) عشان السيرفر يلحق يربط بالنت
sleep 2 

# 8. بنجهز اللينك النهائي عشان نطبعهولك تحت وتقدر تدوس عليه
NGROK_URL="https://$MY_NGROK_DOMAIN"

echo "===================================================="
echo "✅ All services are running in BACKGROUND, Handasa!"
echo "📍 API Local: http://localhost:8000"
echo "📍 Dashboard: http://localhost:8501"
echo "🔥 Live Mobile Link: $NGROK_URL"
echo "===================================================="
echo "💡 Hint: Check logs (e.g., uvicorn.log) if something fails."
echo "🛑 Press [Ctrl+C] to stop ALL services cleanly."
echo "===================================================="

# 9. الـ Safety Switch (مفتاح الأمان)
# الفنكشن دي (trap) بتراقب الكيبورد، أول ما تدوس Ctrl+C عشان تقفل السكريبت،
# بتروح تنفذ أمر kill لكل الـ PIDs اللي إحنا حفظناها فوق. 
# ده بيضمن إن مفيش أي سيرفر يفضل شغال في الخلفية وياكل رامات اللاب توب بتاعك.
trap "echo -e '\n🛑 Stopping all SmartCoach services...'; kill $API_PID $FIT_PID $CAM_PID $DASH_PID $NGROK_PID; exit" SIGINT

# الأمر ده بيخلي السكريبت يفضل صاحي وميقفلش التيرمينال لحد ما إنت تدوس Ctrl+C بنفسك
wait