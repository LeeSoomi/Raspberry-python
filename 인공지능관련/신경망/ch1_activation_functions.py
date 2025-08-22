
# ===============================================================
# ch1_activation_functions.py
# 활성화 함수: 계단/시그모이드/ReLU  (초등 눈높이 주석)
# ===============================================================

import numpy as np

try:
    import matplotlib.pyplot as plt
    HAS_PLT = True
except Exception:
    HAS_PLT = False


def step_function(x):
    """계단 함수: 0 기준으로 '뚝!' 하고 0 또는 1을 내보냄"""
    return np.where(x >= 0, 1, 0)


def sigmoid(x):
    """시그모이드: 부드럽게 0~1 사이 값을 내는 함수(확률 느낌)"""
    return 1 / (1 + np.exp(-x))


def sigmoid_grad(x):
    """시그모이드의 미분(기울기) = s(x)*(1-s(x))"""
    s = sigmoid(x)
    return (1.0 - s) * s


def relu(x):
    """ReLU: 0 이하는 0, 0 초과는 그 값 그대로(요즘 제일 많이 씀)"""
    return np.maximum(0, x)


def relu_grad(x):
    """ReLU의 미분: 0 이하는 0, 0 초과는 1"""
    g = np.zeros_like(x)
    g[x > 0] = 1
    return g


def draw_activation_curves():
    """[예시문제 풀이] 세 가지 활성화 함수를 그림으로 비교"""
    if not HAS_PLT:
        print("matplotlib이 없어 그래프는 생략됩니다.")
        return
    x = np.linspace(-10, 10, 400)

    plt.figure(); plt.plot(x, step_function(x), label="Step"); plt.grid(True)
    plt.title("Step Function"); plt.axhline(0, color='k', lw=0.5); plt.axvline(0, color='k', lw=0.5); plt.legend()

    plt.figure(); plt.plot(x, sigmoid(x), label="Sigmoid"); plt.grid(True)
    plt.title("Sigmoid Function"); plt.axhline(0, color='k', lw=0.5); plt.axvline(0, color='k', lw=0.5); plt.legend()

    plt.figure(); plt.plot(x, relu(x), label="ReLU"); plt.grid(True)
    plt.title("ReLU Function"); plt.axhline(0, color='k', lw=0.5); plt.axvline(0, color='k', lw=0.5); plt.legend()
    plt.show()


if __name__ == "__main__":
    # 그래프를 보고 싶다면 아래 주석을 해제하세요.
    # draw_activation_curves()
    print("[체크] step( [-1,0,1] ) =", step_function(np.array([-1,0,1])))
    print("[체크] sigmoid(0) =", sigmoid(0.0))
    print("[체크] relu([-1,2]) =", relu(np.array([-1.0, 2.0])))
