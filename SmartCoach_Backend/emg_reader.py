# 3. ملف emg_reader.py (قراية العضلات من الـ ESP32)
# وظيفة الملف ده إنه يشتغل كـ "وسيط" بين الهاردوير (ESP32) وبين السحابة (Neon DB).
# بيقرأ إشارات العضلات عن طريق كابل الـ USB (Serial Communication) ويرميها لايف في الداتا بيز.

import serial
import time
from db_manager import DatabaseManager

# 1. إعدادات الاتصال بالبوردة (ESP32)
# لو هتشتغل على ويندوز ممكن تتغير لـ COM3 أو COM4، بس على لينكس بتبقى غالباً ttyUSB0
SERIAL_PORT = '/dev/ttyUSB0'  
BAUD_RATE = 115200 # سرعة نقل الداتا (لازم تكون نفس السرعة اللي مكتوبة في كود الـ Arduino)

# 2. بنفتح اتصال بقاعدة البيانات السحابية
db = DatabaseManager()

# 🔥 التعديل السحري الأخير: توحيد الـ Session ID
# كده إشارة العضلة هتتسجل جوه نفس الجلسة بتاعة الكاميرا والنبض
session_id = "smartcoach_live_session" 

def read_emg_and_save():
    print(f"🔄 بنحاول نتصل بالبوردة على {SERIAL_PORT}...")
    try:
        # بنفتح بوابات الاتصال مع البوردة
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(1.5) # بنستنى ثانية ونص عشان البوردة تعمل Reset براحتها وتبقى جاهزة
        ser.reset_input_buffer() # بننظف أي داتا قديمة كانت متعلقة في الكابل
        
        # 3. التحكم الآلي في الهاردوير (State Machine)
        # بنبعت أمر START للبوردة عشان تفتح "حنفية" الداتا. 
        # (ده بيوفر استهلاك البوردة ومبيخليهاش تبعت داتا عمال على بطال)
        print("🟢 بعتنا أمر START للـ ESP32")
        ser.write(b"START\n")
        
        # الـ Loop ده بيفضل شغال يسحب الداتا طول ما السيستم قايم
        while True:
            # لو في داتا جاية في السكة من الكابل
            if ser.in_waiting > 0:
                # بنقرأ السطر، بنفك تشفيره (decode)، وبنشيل أي مسافات زيادة (strip)
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                try:
                    # بنحول القراية لرقم عشري (Float)
                    emg_val = float(line)
                    print(f"⚡ إشارة العضلة: {emg_val:.2f}")
                    
                    # 4. بنرمي الداتا في السحابة
                    # الفنكشن دي ذكية (Upsert) لو الجلسة موجودة بتحدثها، فالداتا بيز متضربش إيرور
                    db.upsert_exercise_data(
                        session_id=session_id,
                        emg_val=emg_val
                    )
                    
                    # بننظف الكابل تاني عشان نستقبل القراية اللي بعدها على نضافة
                    ser.reset_input_buffer()
                except ValueError:
                    # لو القراية جات فيها حروف أو مشوهة (Noise)، بنتجاهلها ونكمل عادي
                    pass

    except serial.SerialException as e:
        # لو الكابل مش متوصل أو البورت غلط، السيستم مش بيكراش، بيطبعلك الإيرور بس
        print(f"❌ مش قادرين نوصل للبورت: {e}")
    except KeyboardInterrupt:
        # لو إنت دوست Ctrl+C عشان تقفل السيستم
        print("\n🛑 بنقفل السيستم...")
    finally:
        # 5. خطوة الأمان الأخيرة (Graceful Shutdown)
        # لو قفلنا السيستم، لازم نبعت أمر STOP للبوردة عشان تقفل الحنفية وتدخل تنام (Deep Sleep)
        if 'ser' in locals() and ser.is_open:
            print("🔴 بنبعت أمر STOP للـ ESP32 عشان تنام")
            ser.write(b"STOP\n")
            time.sleep(0.1)
            ser.close() # بنقفل بوابات الاتصال
        
        # بنقفل الاتصال بالداتا بيز عشان منستهلكش موارد السيرفر
        db.close()

# السطر ده بيخلي الفنكشن تشتغل أول ما نرن الفايل
if __name__ == "__main__":
    read_emg_and_save()