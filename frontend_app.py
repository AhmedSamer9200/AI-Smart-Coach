# ملف frontend_app.py (الواجهة الشاملة للمشروع - Full Stack)
# المشروع بالكامل من برمجة وإشراف: م. أحمد سامر

import streamlit as st
import requests
import time
from datetime import datetime

# 1. إعدادات الصفحة (عشان تدي شكل الموبايل أبلكيشن)
st.set_page_config(page_title="SmartCoach App", page_icon="🏋️‍♂️", layout="centered")

# رابط الباك إند
BASE_URL = "http://127.0.0.1:8000" 

# 2. إدارة الذاكرة (State Management)
# بنحفظ 3 حاجات: رقم اللاعب، رقم الجلسة الحالية، وبيانات التقرير النهائي
if 'player_id' not in st.session_state:
    st.session_state.player_id = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'summary_data' not in st.session_state:
    st.session_state.summary_data = None

st.title("🏋️‍♂️ AI SmartCoach System")

# ==========================================
# 📺 الشاشة الأولى: التسجيل وربط الساعة
# ==========================================
if st.session_state.player_id is None:
    st.header("1️⃣ حساب جديد وربط الساعة")
    name = st.text_input("👤 اسم اللاعب:")
    access_token = st.text_input("🔑 Fitbit Access Token:", type="password")
    refresh_token = st.text_input("🔄 Fitbit Refresh Token:", type="password")
    
    if st.button("🚀 Connect Fitbit & Register", use_container_width=True):
        if name and access_token and refresh_token:
            payload = {"name": name, "fitbit_access_token": access_token, "fitbit_refresh_token": refresh_token}
            try:
                with st.spinner('جاري تسجيل بياناتك...'):
                    response = requests.post(f"{BASE_URL}/register", json=payload)
                    time.sleep(0.5) 
                if response.status_code == 200:
                    st.session_state.player_id = response.json()["player_id"]
                    st.rerun()
                else:
                    st.error(f"❌ خطأ من السيرفر: {response.text}")
            except:
                st.error("❌ مش قادرين نوصل للباك إند!")
        else:
            st.warning("⚠️ لازم تملا الخانات كلها يا هندسة!")

# ==========================================
# 📺 الشاشة التانية: اختيار التمرين 
# ==========================================
# بتظهر لو هو مسجل دخول، ومفيش جلسة شغالة، ومفيش تقرير بيتعرض
elif st.session_state.session_id is None and st.session_state.summary_data is None:
    st.success(f"👋 أهلاً بيك يا بطل! رقم حسابك: {st.session_state.player_id}")
    st.header("2️⃣ إعدادات التمرينة")
    exercise = st.selectbox("🎯 هتتكسر إيه النهاردة؟", ["Squats", "Biceps Curl", "Pushups"])
    st.divider()
    
    if st.button("▶️ Start Workout (ابدأ التمرينة)", use_container_width=True):
        payload = {"player_id": st.session_state.player_id, "exercise_type": exercise}
        try:
            with st.spinner('جاري تجهيز السحابة...'):
                response = requests.post(f"{BASE_URL}/start_session", json=payload)
            if response.status_code == 200:
                st.session_state.session_id = response.json()["session_id"]
                st.success("✅ الجلسة اتفتحت!")
                time.sleep(0.5)
                st.rerun() 
            else:
                st.error(f"❌ مشكلة: {response.text}")
        except:
            st.error("❌ السيرفر واقع!")
            
    if st.button("🔄 تبديل الحساب"):
        st.session_state.player_id = None
        st.rerun()

# ==========================================
# 📺 الشاشة التالتة: التتبع المباشر (اللايف)
# ==========================================
elif st.session_state.session_id is not None:
    st.header("3️⃣ 🔴 Live Tracking Dashboard")
    st.caption(f"رقم الجلسة الحالية: {st.session_state.session_id}")
    live_mode = st.toggle("🔄 تفعيل السحب المباشر", value=True)
    
    col1, col2, col3 = st.columns(3)
    try:
        live_response = requests.get(f"{BASE_URL}/live_data/{st.session_state.session_id}")
        if live_response.status_code == 200:
            live_data = live_response.json().get("data", {})
            st.markdown(f"**⏳ آخر تحديث للداتا:** `{datetime.now().strftime('%H:%M:%S')}`")
            with col1:
                st.metric(label="📐 الزاوية", value=f"{int(live_data.get('angle', 0))}°")
            with col2:
                st.metric(label="🔄 العداد", value=live_data.get('reps', 0))
                st.markdown(f"**الحركة:** :blue[{live_data.get('stage', 'N/A')}]")
            with col3:
                st.metric(label="❤️ نبض/عضلة", value=f"{live_data.get('emg', 0):.2f}")
        else:
            st.info("⏳ مستنيين السنسورز...")
    except:
        st.error("❌ مش قادرين نوصل للباك إند.")

    st.divider()
    
    # 🔥 السحر الجديد: زرار الإنهاء مع حماية من الأخطاء وتأثير تحميل
    if st.button("🛑 إنهاء التمرينة", type="primary", use_container_width=True):
        with st.spinner("جاري حفظ الجلسة وتحليل بياناتك..."):
            try:
                # 1. نقفل الجلسة
                requests.post(f"{BASE_URL}/end_session/{st.session_state.session_id}")
                
                # 2. نسحب التقرير النهائي
                summary_resp = requests.get(f"{BASE_URL}/session_summary/{st.session_state.session_id}")
                
                if summary_resp.status_code == 200:
                    # لو في داتا، بنحفظ التقرير في الذاكرة
                    st.session_state.summary_data = summary_resp.json()["summary"]
                else:
                    # لو التمرينة كانت فاضية ومفيش داتا اتسجلت
                    st.warning("⚠️ الجلسة انتهت بس مفيش داتا كفاية لعمل تقرير.")
                
                # 3. نمسح رقم الجلسة من الذاكرة عشان نخرج من اللايف
                st.session_state.session_id = None
                time.sleep(1) # تأخير بسيط عشان اليوزر يقرأ الرسالة
                st.rerun()
                
            except requests.exceptions.ConnectionError:
                st.error("❌ مشكلة في الاتصال بالشبكة وقت إنهاء الجلسة.")

    # ميكانيزم التحديث التلقائي
    if live_mode:
        time.sleep(0.5)
        st.rerun()

# ==========================================
# 📺 الشاشة الرابعة: ملخص التمرينة (التقرير النهائي)
# ==========================================
# لو الذاكرة فيها تقرير، نعرضه لليوزر
elif st.session_state.summary_data is not None:
    st.header("4️⃣ 🏆 تقرير التمرينة (Workout Summary)")
    st.balloons() # احتفال بنهاية التمرينة!
    
    summary = st.session_state.summary_data
    
    st.success(f"عاش يا بطل! إنت خلصت تمرينة **{summary.get('exercise_type', 'N/A')}** بنجاح.")
    
    # عرض التقرير في شكل احترافي
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🏅 إجمالي العدادات", value=summary.get("total_reps", 0))
    with col2:
        st.metric(label="📊 متوسط النبض/العضلة", value=summary.get("avg_emg", 0))
        
    st.divider()
    
    # زرار للرجوع للصفحة الرئيسية عشان يبدأ تمرينة جديدة
    if st.button("🏠 رجوع للصفحة الرئيسية", use_container_width=True):
        st.session_state.summary_data = None # بنمسح التقرير من الذاكرة عشان يرجعه لشاشة اختيار التمرين
        st.rerun()