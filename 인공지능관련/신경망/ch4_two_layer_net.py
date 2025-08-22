
# ===============================================================
# ch4_two_layer_net.py
# 2층 신경망 클래스(예측/손실/정확도/역전파) — 초등 눈높이 주석
# ===============================================================

import numpy as np


# --- 활성화/출력/손실 함수들 ---
def sigmoid(x): return 1/(1+np.exp(-x))
def sigmoid_grad(x): 
    s = sigmoid(x); return (1.0 - s) * s

def relu(x): return np.maximum(0, x)
def relu_grad(x): 
    g = np.zeros_like(x); g[x>0]=1; return g

def softmax(x):
    if x.ndim == 2:
        x = x.T; x = x - np.max(x, axis=0)
        y = np.exp(x) / np.sum(np.exp(x), axis=0)
        return y.T
    x = x - np.max(x)
    return np.exp(x) / np.sum(np.exp(x))

def cross_entropy_error(y, t):
    if y.ndim == 1:
        t = t.reshape(1, t.size); y = y.reshape(1, y.size)
    if t.size == y.size:
        t = t.argmax(axis=1)
    batch_size = y.shape[0]
    return -np.sum(np.log(y[np.arange(batch_size), t] + 1e-7)) / batch_size


class TwoLayerNet:
    """입력 -> 은닉 -> 출력 의 2층 신경망 (분류용)
    - 은닉층 활성화: sigmoid / relu 선택 가능
    """
    def __init__(self, input_size, hidden_size, output_size,
                 weight_init_std=0.01, act_hidden="sigmoid"):
        self.params = {}
        if act_hidden.lower() == "relu":
            # ReLU면 He 초기화가 유리(학습 안정)
            self.params['W1'] = np.sqrt(2.0/input_size) * np.random.randn(input_size, hidden_size)
        else:
            self.params['W1'] = weight_init_std * np.random.randn(input_size, hidden_size)
        self.params['b1'] = np.zeros(hidden_size)
        self.params['W2'] = weight_init_std * np.random.randn(hidden_size, output_size)
        self.params['b2'] = np.zeros(output_size)
        self.act_hidden = act_hidden.lower()

    def _hidden(self, a):
        return relu(a) if self.act_hidden == "relu" else sigmoid(a)

    def _hidden_grad(self, a):
        return relu_grad(a) if self.act_hidden == "relu" else sigmoid_grad(a)

    def predict(self, x):
        W1, b1 = self.params['W1'], self.params['b1']
        W2, b2 = self.params['W2'], self.params['b2']
        a1 = np.dot(x, W1) + b1
        z1 = self._hidden(a1)
        a2 = np.dot(z1, W2) + b2
        y  = softmax(a2)
        return y

    def loss(self, x, t):
        y = self.predict(x)
        return cross_entropy_error(y, t)

    def accuracy(self, x, t):
        y = self.predict(x)
        y = np.argmax(y, axis=1)
        t = np.argmax(t, axis=1) if t.ndim != 1 else t
        return np.sum(y == t) / float(x.shape[0])

    def gradient(self, x, t):
        W1, b1 = self.params['W1'], self.params['b1']
        W2, b2 = self.params['W2'], self.params['b2']

        # forward
        a1 = np.dot(x, W1) + b1
        z1 = self._hidden(a1)
        a2 = np.dot(z1, W2) + b2
        y  = softmax(a2)

        # backward
        batch_num = x.shape[0]
        dy = (y - t) / batch_num
        grads = {}
        grads['W2'] = np.dot(z1.T, dy)
        grads['b2'] = np.sum(dy, axis=0)
        dz1 = np.dot(dy, W2.T)
        da1 = self._hidden_grad(a1) * dz1
        grads['W1'] = np.dot(x.T, da1)
        grads['b1'] = np.sum(da1, axis=0)
        return grads


def apply_l2(grads, params, weight_decay=1e-4):
    """보충: L2 정규화 — 가중치가 너무 커지지 않도록 살짝 잡아줌"""
    grads['W1'] += weight_decay * params['W1']
    grads['W2'] += weight_decay * params['W2']


if __name__ == "__main__":
    # 작은 더미 데이터로 동작 점검
    np.random.seed(0)
    x = np.random.rand(5, 4)               # 입력 4개
    t = np.eye(3)[np.random.randint(0,3,5)]# 클래스 3개
    net = TwoLayerNet(input_size=4, hidden_size=5, output_size=3, act_hidden="relu")
    print("초기 손실:", net.loss(x, t))
    g = net.gradient(x, t)
    for k in g: print(k, g[k].shape)
