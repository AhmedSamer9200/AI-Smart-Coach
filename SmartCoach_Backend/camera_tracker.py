import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
from db_manager import DatabaseManager

# 1. تحميل الموديل بتاعنا اللي اتدرب
try:
    model = tf.keras.models.load_model('squats_dl_model.keras')
    print("✅ تم تحميل موديل الـ Deep Learning بنجاح")
except:
    print("❌ الموديل مش موجود، لازم ترن train_model.py الأول")
    exit()

# قاموس لترجمة الأرقام لحركات
stage_map = {0: "up", 1: "down", 2: "Error! Fix Posture"}

# 2. فتح اتصال بقاعدة البيانات السحابية
db = DatabaseManager()

# 🔥 التعديل السحري: توحيد الـ Session ID
# بدل ما الكاميرا تعمل ID عشوائي وكل حاجة تتوه مننا، وحدناه هنا
current_session_id = "smartcoach_live_session"

# خطوة أمان (Data Integrity): بنأكد إن اللاعب موجود الأول عشان الداتا بيز مترفضش الجلسة
db.cursor.execute("INSERT INTO players (player_id, name) VALUES (1, 'Ahmed') ON CONFLICT (player_id) DO NOTHING;")

# بنسجل الجلسة الموحدة دي في الداتا بيز.
# استخدام (ON CONFLICT DO NOTHING) بيخلي السيستم ذكي، لو الجلسة موجودة مبيعملش إيرور وبيكمل شغل عادي
db.cursor.execute("INSERT INTO sessions (session_id, player_id, exercise_type) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;", (current_session_id, 1, "Squats DL"))
db.conn.commit()

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# 🔥 دالة حساب الزاوية عشان الـ Dashboard تفضل ترسم الجراف بتاعها وميبقاش خط مستقيم
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    if angle > 180.0: angle = 360-angle
    return angle 

counter = 0 
stage = "up"
frame_skip = 0 
cap = cv2.VideoCapture(0)

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        angle_val = 0.0 # قيمة مبدئية

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # حساب الزاوية للعرض فقط في الداشبورد
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            angle_val = calculate_angle(shoulder, elbow, wrist)

            # استخراج نفس الـ 132 نقطة عشان نبعتها للموديل
            row = np.array([[res.x, res.y, res.z, res.visibility] for res in landmarks]).flatten()
            
            # 🔥 تعديل مهم لسرعة الأداء: استخدام Numpy بدل Pandas
            X = np.array([row]) 
            prediction = model.predict(X, verbose=0)
            predicted_class = np.argmax(prediction[0])
            predicted_stage = stage_map[predicted_class]

            # منطق العداد (الموديل هو اللي بيحدد إنت فين)
            if predicted_stage == "down":
                stage = "down"
            elif predicted_stage == "up" and stage == "down":
                stage = "up"
                counter += 1
            elif predicted_stage == "Error! Fix Posture":
                stage = "Error"
                cv2.putText(image, 'WARNING: WRONG POSTURE!', (100,200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3, cv2.LINE_AA)

            # تسجيل الداتا في الداتا بيز كل 5 فريمات عشان منعملش Overload على السيرفر
            frame_skip += 1
            if frame_skip % 5 == 0:
                db.upsert_exercise_data(
                    session_id=current_session_id, # هنا بنبعت للـ ID الموحد
                    angle=float(angle_val), 
                    stage=stage,
                    reps=counter
                )

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        cv2.rectangle(image, (0,0), (250,73), (245,117,16), -1)
        cv2.putText(image, 'REPS', (15,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, str(counter), (10,60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(image, 'STAGE', (90,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, stage, (90,60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 2, cv2.LINE_AA)

        cv2.imshow('SmartCoach - DL Tracker', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
db.close()