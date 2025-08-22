
# ===============================================================
# ch6_extras_colab_and_improvements.py
# Colab 외부 그림 예측 + 정확도 개선 팁 — 초등 눈높이 주석
# ===============================================================

import numpy as np


def preprocess_digit_image(path):
    """외부 숫자 그림을 MNIST처럼 전처리 (Colab 권장)
    1) 흑백으로 읽기, 2) 28x28로 줄이기, 3) 0~1 정규화, 4) (1,784)로 펴기
    - 사진 배경/글씨 색이 반전되면 255-x 처리가 필요할 수 있음
    """
    try:
        from PIL import Image
    except Exception:
        raise RuntimeError("PIL(Pillow) 설치 필요: pip install pillow")
    img = Image.open(path).convert('L').resize((28,28))
    x = np.array(img).astype(np.float32)
    # 필요 시 x = 255 - x (배경/글씨 반전)
    x = x / 255.0
    x = x.reshape(1, 784)
    return x


IMPROVEMENT_TIPS = """
[정확도 올리는 대표 비법]
1) 은닉층 활성화 ReLU + He 초기화(코드에 내장)
2) 에폭/배치/학습률 조정: epochs up, batch 128, lr 0.05~0.2 탐색
3) 은닉층 크기 늘리기: 50 -> 100~300
4) L2 정규화 적용으로 과적합 완화
5) 입력 전처리 점검: 0~1 정규화, 배경/글씨 방향 확인
"""


if __name__ == "__main__":
    print(IMPROVEMENT_TIPS)
