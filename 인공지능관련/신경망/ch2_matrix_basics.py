
# ===============================================================
# ch2_matrix_basics.py
# 다차원 배열과 행렬 곱 (초등 눈높이 주석)
# ===============================================================

import numpy as np


def matrix_multiply_examples():
    """[예시문제] 교재에 나온 행렬 곱을 파이썬으로 계산"""
    # 예1) 2x2 @ 2x2
    A = np.array([[1, 2], [3, 4]])   # 2행 2열
    B = np.array([[5, 6], [7, 8]])   # 2행 2열
    C = np.dot(A, B)                  # 결과도 2x2
    print("예1 결과(2x2):\n", C)

    # 예2) 모양(차원) 주의: 앞 행렬의 '열 수' == 뒤 행렬의 '행 수'
    A = np.array([[1,2,3], [4,5,6]])          # 2x3
    B = np.array([[1,2], [3,4], [5,6]])       # 3x2
    print("A.shape=", A.shape, "B.shape=", B.shape)
    C = np.dot(A, B)                          # 결과 2x2
    print("예2 결과 모양:", C.shape, "\n", C)

    # 예3) 신경망 모양 상상: 입력(1x2) @ 가중치(2x3) = 은닉(1x3)
    X = np.array([[1.0, 0.5]])                # 1x2
    W = np.array([[1,3,5],[2,4,6]])           # 2x3
    Y = np.dot(X, W)                           # 1x3
    print("예3 (1x2)@(2x3)->(1x3):", Y)


if __name__ == "__main__":
    matrix_multiply_examples()
