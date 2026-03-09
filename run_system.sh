#!/bin/bash

echo "=================================================="
echo "🚀 جاري تشغيل سيستم SmartCoach الشامل (Full-Stack)"
echo "👨‍💻 برمجة وإعداد: م. أحمد سامر"
echo "=================================================="

# 1. تفعيل البيئة الوهمية (عشان كل المكتبات زي Streamlit و FastAPI تقرأ صح)
source ~/myenv/bin/activate

# 2. دالة الطوارئ (Graceful Shutdown)
# الفنكشن دي بتشتغل أوتوماتيك لما تدوس Ctrl+C، بتلف على كل البرامج اللي شغالة وتقفلها بنضافة
cleanup() {
    echo ""
    echo "🛑 جاري إغلاق كل السيرفرات والسنسورز بنظافة..."
    # بيقفل كل العمليات اللي شغالة في الخلفية
    kill $(jobs -p) 2>/dev/null
    echo "✅ تم إغلاق السيستم بنجاح. عاش يا هندسة!"
    exit
}

# بنربط دالة الطوارئ بأزرار القفل (Ctrl+C)
trap cleanup SIGINT SIGTERM

# 3. تشغيل الباك إند (العقل) في الخلفية وتسجيل اللوجات
echo "⚙️ [1/6] تشغيل الباك إند (FastAPI)..."
cd SmartCoach_Backend || exit
# حفظنا اللوجات في ملف عشان لو الباك إند وقع نعرف السبب
uvicorn api:app --host 127.0.0.1 --port 8000 > ../uvicorn.log 2>&1 &
cd ..
sleep 3 # بندي فرصة 3 ثواني للسيرفر يقوم قبل ما نشغل باقي الحاجات

# 4. تشغيل الفرونت إند (واجهة الموبايل/الداشبورد)
echo "📱 [2/6] تشغيل واجهة التطبيق (Streamlit)..."
streamlit run frontend_app.py > streamlit.log 2>&1 &
sleep 3

# 5. تشغيل السنسورز (عيون وحواس السيستم) مع حفظ اللوجات
echo "👁️ [3/6] تشغيل كاميرا الذكاء الاصطناعي..."
python3 camera_tracker.py > camera.log 2>&1 &

echo "❤️ [4/6] تشغيل قارئ نبضات القلب (Fitbit)..."
python3 fitbit_reader.py > fitbit.log 2>&1 &

echo "💪 [5/6] تشغيل قارئ إشارات العضلات (EMG)..."
python3 emg_reader.py > emg.log 2>&1 &

# 6. تشغيل الـ Ngrok (عشان نطلع السيستم على النت)
MY_NGROK_DOMAIN="octangular-maxim-sparkishly.ngrok-free.dev"
echo "🌐 [6/6] تشغيل Ngrok للربط الخارجي على الدومين الثابت..."
# بنربط الـ Ngrok ببورت 8000 عشان يرفع الـ API بتاعك على النت
ngrok http --domain=$MY_NGROK_DOMAIN 8000 > ngrok.log 2>&1 &
NGROK_URL="https://$MY_NGROK_DOMAIN"
sleep 2

echo "=================================================="
echo "✅ السيستم كله شغال دلوقتي في الخلفية بالتوازي!"
echo "📍 API Local: http://localhost:8000"
echo "📍 Dashboard: http://localhost:8501"
echo "🔥 Live API Link: $NGROK_URL"
echo "=================================================="
echo "💡 تلميح: لو في حاجة مشغلتش، افتح ملفات الـ (.log) عشان تعرف السبب."
echo "⚠️ لما تحب تقفل السيستم وتنهي كل حاجة، دوس هنا (Ctrl + C)"
echo "=================================================="

# السطر ده بيمنع السكريبت إنه يقفل لوحده، وبيخليه يفضل شغال يراقب البرامج
wait