
# 신경망 학습서 (초등 눈높이) — 장별 코드

각 장은 **독립 실행**이 가능하도록 작성했습니다.  
Colab에서 실행하면 MNIST 다운로드(인터넷 필요)도 문제없이 동작합니다.

## 파일 구성
- `ch1_activation_functions.py` : 계단/시그모이드/ReLU와 그래프
- `ch2_matrix_basics.py`        : 다차원 배열과 행렬 곱 예제
- `ch3_three_layer_forward.py`  : 3층 신경망 순전파 데모(은닉층 2개)
- `ch4_two_layer_net.py`        : 2층 신경망 클래스(예측/손실/정확도/역전파)
- `ch5_mnist_training.py`       : MNIST 숫자 분류 학습(Colab 권장)
- `ch6_extras_colab_and_improvements.py` : 외부 그림 예측/정확도 향상 팁

## 빠른 시작
```bash
# 1) 활성화 함수 그래프 보기 (로컬 환경엔 matplotlib 설치 필요)
python ch1_activation_functions.py

# 2) 행렬 곱 예시
python ch2_matrix_basics.py

# 3) 3층 순전파 데모
python ch3_three_layer_forward.py

# 4) (선택) 2층 신경망 동작 점검
python ch4_two_layer_net.py

# 5) MNIST 학습 (Colab 권장: sklearn/pandas/인터넷 필요)
python ch5_mnist_training.py
```

## 주의
- 한글 주석이 많아 **학습용**으로 최적화되어 있습니다.
- Colab에서 실행 시 런타임 유형을 Python(기본)으로 두고 실행하세요.
