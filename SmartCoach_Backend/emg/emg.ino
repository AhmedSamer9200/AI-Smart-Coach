#define EMG_PIN 33        
#define WEAR_PIN 25       

unsigned long lastReadTime = 0; 
unsigned long lastSendTime = 0; 
const int readInterval = 2;   
const int sendInterval = 200; 

float filteredEMG = 0;
const float EMA_ALPHA = 0.2; 

// 🔥 المتغير الجديد: الحنفية مقفولة في البداية
bool isStreaming = false; 

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(EMG_PIN, ADC_11db); 
  pinMode(WEAR_PIN, INPUT_PULLDOWN); 

  // حقنة البداية للفلتر
  filteredEMG = analogRead(EMG_PIN);
}

void loop() {
  // 🔥 استقبال الأوامر من البايثون
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // تنظيف الكلمة من أي مسافات
    
    if (command == "START") {
      isStreaming = true;
    } 
    else if (command == "STOP") {
      isStreaming = false;
    }
  }

  int isWearing = digitalRead(WEAR_PIN);
  
  if (isWearing == HIGH) {
    // 1. القراءة السريعة للفلتر (شغالة دايماً عشان الداتا تفضل دقيقة)
    if (millis() - lastReadTime >= readInterval) {
      lastReadTime = millis();
      int sum = 0;
      for(int i = 0; i < 4; i++) sum += analogRead(EMG_PIN);
      filteredEMG = (EMA_ALPHA * (sum / 4)) + ((1 - EMA_ALPHA) * filteredEMG);
    }

    // 2. الإرسال للبايثون (🔥 مش هيبعت غير لو البايثون قاله START)
    if (millis() - lastSendTime >= sendInterval) {
      lastSendTime = millis();
      if (isStreaming == true) {
        Serial.println(filteredEMG);
      }
    }
    
  } else {
    // لو قلعت السنسور اقفل الحنفية ونام
    isStreaming = false; 
    delay(100); 
    esp_sleep_enable_ext0_wakeup((gpio_num_t)WEAR_PIN, 1);
    esp_deep_sleep_start(); 
  }
}