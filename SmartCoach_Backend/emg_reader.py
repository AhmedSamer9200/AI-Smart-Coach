# 5. ملف emg_reader.py (سحب إشارات العضلات الذكي)
# التعديل: توجيه الداتا للسحابة مباشرة مع نظام Session Caching لتقليل الضغط على الداتا بيز وزيادة السرعة.

import serial
import time
from db_manager import DatabaseManager # 🔥 ربط الداتا بيز

# إعدادات الاتصال بالهاردوير (ESP32)
SERIAL_PORT = '/dev/ttyUSB0'   
BAUD_RATE = 115200

# بنفتح الاتصال بالداتا بيز
db = DatabaseManager()

def record_smart_emg():
    print(f"🔌 بنحاول نتصل بالبوردة على {SERIAL_PORT}...")
    try:
        # بنفتح بوابات الاتصال مع البوردة
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(1.5) # انتظار لحد ما البوردة تعمل ريستارت وتستقر
        ser.reset_input_buffer()
        
        print("▶️ بعتنا أمر START للـ ESP32")
        ser.write(b"START\n")
        
        # 🔥 متغيرات تنظيم الوقت والـ Caching
        last_db_update = 0 
        last_session_check = 0 
        cached_session_id = None # بنخزن هنا الـ ID عشان منسألش الداتا بيز عمال على بطال
        
        while True:
            # لو في داتا جاية من البوردة
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8',errors='ignore').strip()
                
                # نتأكد إنها داتا حقيقية مش خطوط فواصل
                if not line.startswith("---"):
                    try:
                        emg_val = float(line)
                        current_time = time.time()
                        
                        # 🚀 السحر المعماري الأول (Session Caching):
                        # بدل ما نسأل الداتا بيز كل نص ثانية، هنسألها كل 5 ثواني بس ونسجل النتيجة عندنا
                        if current_time - last_session_check > 5.0:
                            active_session = db.get_active_session_tokens()
                            if active_session:
                                cached_session_id = active_session["session_id"]
                            else:
                                cached_session_id = None # لو مفيش حد بيتمرن بنفضي الذاكرة
                            last_session_check = current_time
                        
                        # 🚀 السحر المعماري التاني (Throttling):
                        # بنبعت الإشارة للسحابة كل 0.5 ثانية عشان منعملش اختناق للنت (Network Bottleneck)
                        if current_time - last_db_update > 0.5:
                            
                            if cached_session_id:
                                print(f"💪 إشارة العضلة -> {emg_val:.2f} (Session: {cached_session_id})")
                                # بنرمي القراية في الداتا بيز في الجلسة المحفوظة
                                db.upsert_exercise_data(session_id=cached_session_id, emg_val=emg_val)
                            else:
                                # لو مفيش جلسة، بنطبع الداتا بس ومش بنسجلها
                                print(f"⏳ مفيش تمرينة شغالة دلوقتي.. العضلة ({emg_val:.2f}) مش هتتسجل.")
                                
                            last_db_update = current_time
                            
                        # بننظف الكابل عشان نستقبل القراية اللي بعدها بأعلى سرعة
                        ser.reset_input_buffer()
                    except ValueError:
                        pass # لو البوردة بعتت كلام غريب بدل الأرقام يتجاهله
                        
    except serial.SerialException as e:
        print(f"❌ مش قادرين نوصل للبورت (تأكد إن الكابل متوصل): {e}")
    except KeyboardInterrupt:
        print("\n🛑 بنقفل السيستم...")
    finally:
        # 🔥 خطوة الأمان (Graceful Shutdown)
        if 'ser' in locals() and ser.is_open:
            print("⏸️ بنبعت أمر STOP للـ ESP32 عشان تنام (Deep Sleep)")
            ser.write(b"STOP\n")
            time.sleep(0.1) 
            ser.close()
        # إغلاق الداتا بيز بنضافة
        db.close()

if __name__ == "__main__":
    record_smart_emg()