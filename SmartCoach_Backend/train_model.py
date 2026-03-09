import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.model_selection import train_test_split

print("⏳ جاري قراءة الداتا...")
# قراءة الداتا اللي جمعناها
df = pd.read_csv('squats_dataset.csv')

# فصل المخرجات (الـ Label) عن المدخلات (الـ 132 نقطة)
X = df.drop('label', axis=1).values
y = df['label'].values

# تقسيم الداتا لتدريب واختبار
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("🧠 جاري بناء وتدريب الموديل...")
# بناء الشبكة العصبية
model = Sequential([
    Dense(128, activation='relu', input_shape=(132,)),
    Dropout(0.2),
    Dense(64, activation='relu'),
    Dense(3, activation='softmax') # 3 مخرجات (0=Up, 1=Down, 2=Error)
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# تدريب الموديل
model.fit(X_train, y_train, epochs=50, validation_data=(X_test, y_test))

# حفظ الموديل النهائي
model.save('squats_dl_model.keras')
print("🎉 مبروك! الموديل اتدرب واتحفظ باسم squats_dl_model.keras")