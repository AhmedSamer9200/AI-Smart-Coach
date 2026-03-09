# 5. ملف dashboard.py (شاشة عرض المدرب)
# الملف ده مبني بمكتبة Streamlit، وظيفته إنه يسحب الداتا من الداتا بيز السحابية (Neon) 
# ويعرضها في شكل Dashboard لايف (رسومات بيانية وأرقام) للمدرب كأنه واقف مع اللاعب.

import streamlit as st
import pandas as pd
import time
from db_manager import DatabaseManager

# 1. إعدادات الشاشة الأساسية (الـ UI)
st.set_page_config(page_title="SmartCoach Dashboard", layout="wide")
st.title("🏋️‍♂️ SmartCoach - Live Analytics Dashboard")

# 2. بنفتح اتصال بقاعدة البيانات السحابية
db = DatabaseManager()

# 🔥 التعديل السحري: توحيد الـ Session ID
# هنا خلينا الديفولت بتاع الشاشة هو "smartcoach_live_session" 
# عشان أول ما تفتح الشاشة، تقرأ نفس الداتا اللي الكاميرا والفيتبيت بيرموها في نفس اللحظة
session_id = st.text_input("دخل الـ Session ID بتاع اللاعب:", "smartcoach_live_session")

# 3. بنجهز أماكن فاضية (Placeholders) في الشاشة عشان نحط فيها الداتا بعدين وتتحدث لايف
# دالة empty() دي بتسمحلنا نغير الرقم اللي جوه المربع من غير ما نعمل ريفريش للصفحة كلها
col1, col2, col3 = st.columns(3)
angle_metric = col1.empty()
reps_metric = col2.empty()
stage_metric = col3.empty()

st.subheader("تحليل الأداء (Live Feed)")
# مكان مخصص للرسم البياني اللي هيعرض زاوية الحركة
chart_placeholder = st.empty()

# لستة نحتفظ بيها بالداتا القديمة (آخر 50 قراية) عشان نرسم بيها الـ Line Chart
history_data = []

# 4. زرار التشغيل اللي هيبدأ يسحب الداتا ويعرضها
if st.button("🔴 ابدأ المتابعة اللايف"):
    with st.spinner("بيسحب الداتا..."):
        # الـ Loop ده (while True) بيفضل شغال على طول عشان يخلي الشاشة (Live)
        while True:
            # بنسحب أجدد داتا من الداتا بيز بناءً على الجلسة الموحدة
            data = db.get_live_data(session_id)
            
            if data:
                # 5. تحديث الأرقام اللي فوق في الشاشة
                angle_metric.metric("الزاوية (Angle)", f"{data['angle']:.1f}°")
                reps_metric.metric("العداد (Reps)", data['reps'])
                
                # بنعرض المرحلة اللي اللاعب فيها (up, down, Error)
                # في المناقشة ممكن تضيف فكرة إن لو بيلعب غلط اللون يتغير
                stage_metric.metric("الحركة (Stage)", data['stage'])
                
                # 6. بنحفظ الزاوية الحالية والوقت في اللستة عشان الرسم البياني
                history_data.append({"Time": pd.Timestamp.now(), "Angle": data['angle']})
                
                # بنمسح الداتا القديمة لو زادت عن 50 قراية عشان الشاشة متزحمش واللاب توب ميهنجش (Optimization)
                if len(history_data) > 50:
                    history_data.pop(0)
                    
                # بنحول اللستة لـ DataFrame (جدول) عشان Streamlit تفهمها وترسمها بسرعة
                df = pd.DataFrame(history_data).set_index("Time")
                chart_placeholder.line_chart(df)
            
            # 7. بنعمل سليب نص ثانية عشان منهلكش الداتا بيز بطلبات كتير ورا بعض
            time.sleep(0.5)