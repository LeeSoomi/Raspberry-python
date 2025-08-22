
# ===============================================================
# ch5_mnist_training.py
# MNIST 숫자 분류 (2층 신경망, Colab 권장) — 초등 눈높이 주석
# ===============================================================

import numpy as np
from ch4_two_layer_net import TwoLayerNet, apply_l2

def load_mnist_via_sklearn():
    """MNIST 내려받기(인터넷 필요)
    - X: (N,784) 0~1 정규화
    - y: 원-핫(10차원)
    """
    from sklearn.datasets import fetch_openml
    mnist = fetch_openml('mnist_784', version=1, cache=True)
    X = mnist['data'].astype(np.float32).values / 255.0
    y_int = mnist['target'].astype(np.int64).values
    y = np.eye(10)[y_int]
    return X[:60000], y[:60000], X[60000:], y[60000:]


def train_two_layer_on_mnist(act_hidden="relu", learning_rate=0.1,
                             hidden_size=100, batch_size=100, epochs=3, use_l2=False):
    x_train, t_train, x_test, t_test = load_mnist_via_sklearn()
    net = TwoLayerNet(input_size=784, hidden_size=hidden_size, output_size=10,
                      act_hidden=act_hidden)

    train_acc_list, test_acc_list = [], []
    iter_per_epoch = max(x_train.shape[0] // batch_size, 1)
    iters_num = iter_per_epoch * epochs

    for it in range(1, iters_num + 1):
        mask = np.random.choice(x_train.shape[0], batch_size)
        x_batch = x_train[mask]; t_batch = t_train[mask]

        grad = net.gradient(x_batch, t_batch)

        # (선택) L2 정규화로 과적합 완화
        if use_l2:
            apply_l2(grad, net.params, weight_decay=1e-4)

        for k in net.params:
            net.params[k] -= learning_rate * grad[k]

        if it % iter_per_epoch == 0:
            train_acc = net.accuracy(x_train[:2000], t_train[:2000])
            test_acc  = net.accuracy(x_test[:2000],  t_test[:2000])
            train_acc_list.append(train_acc); test_acc_list.append(test_acc)
            print(f"[epoch {it//iter_per_epoch}] train_acc={train_acc:.3f}, test_acc={test_acc:.3f}")

    return net, train_acc_list, test_acc_list


if __name__ == "__main__":
    # Colab에서 실행하세요. (sklearn/pandas/인터넷 필요)
    net, tr, te = train_two_layer_on_mnist()
