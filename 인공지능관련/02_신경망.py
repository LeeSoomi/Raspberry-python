[기본1] 2층 신경망 forward

풀이 요약: x→(W1,b1,활성)→z1→(W2,b2)→y

import numpy as np

def sigmoid(x): return 1/(1+np.exp(-x))

def two_layer_forward(x):
    W1 = np.array([[0.1,0.3,0.5],[0.2,0.4,0.6]])  # (2×3)
    b1 = np.array([0.1,0.2,0.3])
    W2 = np.array([[0.1,0.3],[0.2,0.4],[0.3,0.5]])  # (3×2)
    b2 = np.array([0.1,0.2])

    a1 = x@W1 + b1
    z1 = sigmoid(a1)
    a2 = z1@W2 + b2
    return a2  # (출력층 활성 전) 회귀라면 항등/분류면 softmax

print(two_layer_forward(np.array([1.0, 0.5])))


검토체크: 차원 맞는지 (2×3, 3×2) 확인(✅).

[기본2] Sigmoid 구현
def sigmoid(x): return 1/(1+np.exp(-x))
# 검토: sigmoid(0)=0.5, 큰 음수→0, 큰 양수→1 (✅)

[기본3] Softmax 구현 (수치안정)
def softmax(x):
    x = x - np.max(x)           # overflow 방지
    ex = np.exp(x)
    return ex / np.sum(ex)

# 검토: 합이 1인지 확인(✅)

[기본4] 손실 함수 (MSE, CE)
def mse(y, t):  # 평균제곱오차
    return 0.5*np.sum((y-t)**2)

def cross_entropy(y, t):  # t: 라벨 정수 또는 원-핫
    y = y.reshape(1,-1)
    if t.ndim==1 or (t.ndim==2 and t.shape[0]==1 and t.shape[1]==y.shape[1]):
        # t가 원-핫이면 정수라벨로
        if t.size==y.size: t = t.argmax(axis=1)
    t = np.array(t).reshape(-1)
    return -np.log(y[0, t[0]] + 1e-7)

# 검토: y는 softmax 출력, CE는 작을수록 좋은 값(✅)

[기본5] 정확도 계산
def accuracy(y_pred, t_true):
    # y_pred: (N, C) 확률, t_true: (N,) 정수라벨 또는 (N,C) 원-핫
    y_lab = np.argmax(y_pred, axis=1)
    if t_true.ndim != 1:
        t_true = np.argmax(t_true, axis=1)
    return np.mean(y_lab == t_true)

# 검토: 정답 라벨과 예측 라벨 일치 비율(✅)

[기본6] 2층 네트워크 클래스(순전파/손실/정확도)
class TwoLayerNet:
    def __init__(self, D_in, H, D_out, wstd=0.01):
        self.W1 = wstd*np.random.randn(D_in, H); self.b1 = np.zeros(H)
        self.W2 = wstd*np.random.randn(H, D_out); self.b2 = np.zeros(D_out)

    def predict(self, x):
        z1 = sigmoid(x@self.W1 + self.b1)
        y  = softmax(z1@self.W2 + self.b2)
        return y

    def loss(self, x, t):
        y = self.predict(x)
        return cross_entropy(y, t)

    def acc(self, x, t):
        return accuracy(self.predict(x), t)

# 검토: 차원/반환형태 확인(✅)

[기본7] 오차역전파(gradient)
def grad_two_layer(net, x, t):
    # forward
    a1 = x@net.W1 + net.b1
    z1 = sigmoid(a1)
    a2 = z1@net.W2 + net.b2
    y  = softmax(a2)
    # t 정수라벨
    if t.ndim != 1: t = np.argmax(t, axis=1)
    N = x.shape[0]
    # backward
    dy = y.copy()
    dy[np.arange(N), t] -= 1
    dy /= N
    dW2 = z1.T@dy
    db2 = dy.sum(axis=0)
    dz1 = dy@net.W2.T * (z1*(1-z1))
    dW1 = x.T@dz1
    db1 = dz1.sum(axis=0)
    return dW1, db1, dW2, db2

# 검토: 차원 (W1: D×H, W2: H×C) 맞는지(✅)

[기본8] 미니배치 학습 루프(요지)
def train_step(net, x_batch, t_batch, lr=0.1):
    dW1, db1, dW2, db2 = grad_two_layer(net, x_batch, t_batch)
    net.W1 -= lr*dW1; net.b1 -= lr*db1
    net.W2 -= lr*dW2; net.b2 -= lr*db2

# 검토: 손실이 점차 감소하는지 소규모 데이터로 확인(✅)

[심화] Colab에서 그림 업로드 인식

풀이 요약: PIL로 28×28 흑백→정규화→(1,784)→net.predict→argmax.

# from PIL import Image
# img = Image.open('my_digit.png').convert('L').resize((28,28))
# x = (np.array(img).astype(np.float32)/255.0).reshape(1,784)
# print(np.argmax(net.predict(x)))
# 검토: 반전 필요 시 255-x 적용(✅)

[보충] 학습률/에폭 변화 비교

풀이 요약: (lr, epochs) 조합을 바꿔 train/test acc를 표로 비교.

# for lr in [0.05, 0.1, 0.2]:
#   for ep in [3,5,10]:
#       ... 학습 → 정확도 기록
# 검토: 과대/과소적합 경향 관찰(✅)
