# 3. ملف camera_tracker.py (كاميرا الذكاء الاصطناعي المدمجة مع السحابة)
# التعديل: دمج الـ Deep Learning Model مع الـ Multi-User Architecture وحماية الأداء.

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import time
from db_manager import DatabaseManager # 🔥 ربط الداتا بيز

# 1. تحميل الموديل بتاعنا اللي اتدرب (AI Brain)
try:
    model = tf.keras.models.load_model('squats_dl_model.keras')
    print("✅ تم تحميل موديل الـ Deep Learning بنجاح")
except Exception as e:
    print(f"❌ الموديل مش موجود أو فيه مشكلة: {e}")
    print("لازم ترن train_model.py الأول عشان تطلع ملف squats_dl_model.keras")
    exit()

# قاموس لترجمة أرقام الموديل لحركات مفهومة
stage_map = {0: "up", 1: "down", 2: "Error! Fix Posture"}

# 2. بنفتح الاتصال بالداتا بيز
db = DatabaseManager()

# تجهيز أدوات Mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# 3. دالة حساب الزاوية (عشان الـ Dashboard تفضل ترسم الجراف بتاعها وميبقاش خط مستقيم)
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    if angle > 180.0: angle = 360-angle
    return angle 

# 4. متغيرات التشغيل
counter = 0 
stage = "up"
last_db_update = 0 # 🔥 تايمر التحديث السحابي عشان نحمي السيرفر من التهنيج

cap = cv2.VideoCapture(0)

# 5. بداية البرنامج والتقاط الحركة
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue

        # تحويل الألوان عشان Mediapipe يفهمها
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        angle_val = 0.0 # قيمة مبدئية للزاوية

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # حساب الزاوية للعرض على الداشبورد
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            angle_val = calculate_angle(shoulder, elbow, wrist)

            # 🔥 استخراج نفس الـ 132 نقطة عشان نبعتها للموديل
            row = np.array([[res.x, res.y, res.z, res.visibility] for res in landmarks]).flatten()
            
            # 🔥 الموديل بيشتغل هنا: استخدام Numpy لسرعة الأداء
            X = np.array([row]) 
            # (verbose=0) عشان نمنع التيرمينال إنه يتملي رسايل مزعجة من تنزرفلو
            prediction = model.predict(X, verbose=0)
            predicted_class = np.argmax(prediction[0])
            predicted_stage = stage_map[predicted_class]

            # منطق العداد (الموديل هو اللي بيحدد إنت فين)
            if predicted_stage == "down":
                stage = "down"
            elif predicted_stage == "up" and stage == "down":
                stage = "up"
                counter += 1
                print(f"✅ Rep Completed: {counter}")
            elif predicted_stage == "Error! Fix Posture":
                stage = "Error"
                # رسم تحذير أحمر كبير لو اللاعب بيتمرن غلط
                cv2.putText(image, 'WARNING: WRONG POSTURE!', (50,200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3, cv2.LINE_AA)

            # 🔥 السحر هنا (إرسال الداتا لليوزر النشط حالياً):
            current_time = time.time()
            # بنكلم الداتا بيز مرة كل 0.5 ثانية بس عشان الفيديو ميهنجش
            if current_time - last_db_update > 0.5:
                # بنسأل: مين اللي فاتح التمرينة دلوقتي على الموبايل أبلكيشن؟
                active_session = db.get_active_session_tokens()
                if active_session:
                    session_id = active_session["session_id"]
                    # بنبعت الزاوية، والحالة (من الموديل)، والعداد للجلسة دي تحديداً
                    db.upsert_exercise_data(
                        session_id=session_id, 
                        angle=float(angle_val), 
                        stage=stage,
                        reps=counter
                    )
                last_db_update = current_time # تصفير التايمر

            # رسم الهيكل العظمي على الشاشة
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        # رسم الـ UI الأساسي
        cv2.rectangle(image, (0,0), (280,73), (245,117,16), -1)
        cv2.putText(image, 'REPS', (15,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, str(counter), (10,60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(image, 'STAGE', (100,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, stage, (100,60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 2, cv2.LINE_AA)

        cv2.imshow('SmartCoach - DL & Multi-User Tracker', image)

        # الخروج لو دوسنا 'q'
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
db.close() # قفل الاتصال بالسحابة بنظافة