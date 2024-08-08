# AI 테스트
import tensorflow as tf
from tensorflow import keras
import numpy as np

# 데이터 생성
x_train = np.linspace(-1, 1, 100)
y_train = x_train ** 2 + np.random.normal(0, 0.1, 100)

# 모델 정의
model = keras.Sequential([
    keras.layers.Dense(10, input_shape=(1,), activation='relu'),
    keras.layers.Dense(10, activation='relu'),
    keras.layers.Dense(1)
])

# 모델 컴파일
model.compile(optimizer='adam', loss='mean_squared_error')

# 모델 훈련
model.fit(x_train, y_train, epochs=100)

# 결과 시각화
y_pred = model.predict(x_train)
plt.scatter(x_train, y_train, label='True Data')
plt.plot(x_train, y_pred, color='red', label='Model Prediction')
plt.legend()
plt.show()
