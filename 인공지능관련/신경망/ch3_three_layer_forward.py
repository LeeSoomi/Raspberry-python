
# ===============================================================
# ch3_three_layer_forward.py
# 3층 신경망 순전파 데모 (입력2 -> 은닉3 -> 은닉2 -> 출력2)
# ===============================================================

import numpy as np


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def identity_function(x):
    return x


def softmax(x):
    """안정적 소프트맥스(1D/2D 모두 지원)"""
    if x.ndim == 2:
        x = x.T
        x = x - np.max(x, axis=0)
        y = np.exp(x) / np.sum(np.exp(x), axis=0)
        return y.T
    x = x - np.max(x)
    return np.exp(x) / np.sum(np.exp(x))


def three_layer_forward_demo(x):
    """[예시문제] 3층 순전파
    x: (1,2) 입력
    """
    W1 = np.array([[0.1, 0.3, 0.5],
                   [0.2, 0.4, 0.6]])        # (2x3)
    b1 = np.array([0.1, 0.2, 0.3])          # (3,)
    W2 = np.array([[0.1, 0.4],
                   [0.2, 0.5],
                   [0.3, 0.6]])             # (3x2)
    b2 = np.array([0.1, 0.2])               # (2,)
    W3 = np.array([[0.1, 0.3],
                   [0.2, 0.4]])             # (2x2)
    b3 = np.array([0.1, 0.2])               # (2,)

    a1 = np.dot(x, W1) + b1
    z1 = sigmoid(a1)
    a2 = np.dot(z1, W2) + b2
    z2 = sigmoid(a2)
    a3 = np.dot(z2, W3) + b3
    y  = identity_function(a3)  # 회귀라면 항등, 분류라면 softmax를 자주 씀
    return y


if __name__ == "__main__":
    y = three_layer_forward_demo(np.array([[1.0, 0.5]]))
    print("3층 데모 출력:", y)
