import cv2
import mediapipe as mp
import numpy as np
import csv
import os

# بنجهز ملف الـ CSV اللي هيشيل الداتا
csv_file = 'squats_dataset.csv'
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        # بنعمل 132 عمود للنقط (33 نقطة * 4 قيم) + عمود للـ Label
        columns = ['label'] + [f'val_{i}' for i in range(132)]
        writer.writerow(columns)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

print("🎥 تعليمات تجميع الداتا:")
print("- اقف في وضع الـ UP (فوق) ودوس على حرف 'u' كتير عشان تسجل صور.")
print("- انزل في وضع الـ DOWN (تحت) ودوس على حرف 'd' كتير.")
print("- اعمل الحركة غلط (مثلا ضهرك متني) ودوس على حرف 'e'.")
print("- دوس 'q' عشان تقفل.")

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # استخراج الـ 132 نقطة
            landmarks = results.pose_landmarks.landmark
            row = list(np.array([[res.x, res.y, res.z, res.visibility] for res in landmarks]).flatten())

            key = cv2.waitKey(1) & 0xFF
            # لو دوست u هيسجل الحركة إنها رقم 0 (Up)
            if key == ord('u'):
                row.insert(0, 0)
                with open(csv_file, mode='a', newline='') as f:
                    csv.writer(f).writerow(row)
                print("✅ تم تسجيل وضع الـ UP")
            
            # لو دوست d هيسجل الحركة إنها رقم 1 (Down)
            elif key == ord('d'):
                row.insert(0, 1)
                with open(csv_file, mode='a', newline='') as f:
                    csv.writer(f).writerow(row)
                print("✅ تم تسجيل وضع الـ DOWN")
                
            # لو دوست e هيسجل الحركة إنها رقم 2 (Error - حركة غلط)
            elif key == ord('e'):
                row.insert(0, 2)
                with open(csv_file, mode='a', newline='') as f:
                    csv.writer(f).writerow(row)
                print("❌ تم تسجيل وضع الـ ERROR")
                
            elif key == ord('q'):
                break

        cv2.imshow('Data Collection', image)

cap.release()
cv2.destroyAllWindows()