1단원 퍼셉트론
[기본1] AND 게이트 구현

풀이 요약: 두 입력이 모두 1일 때만 1을 내도록 가중치/편향을 고른다.

# AND: 두 입력 x1,x2가 모두 1일 때만 1
def AND(x1, x2):
    w1, w2, b = 0.5, 0.5, -0.7  # 가중치/편향(문턱: 합이 0을 넘으면 1)
    s = x1*w1 + x2*w2 + b       # 가중합
    return 1 if s > 0 else 0    # 계단함수

# 간단 검증
for a in [0,1]:
    for b in [0,1]:
        print(a,b, AND(a,b))  # 00→0, 01→0, 10→0, 11→1


검토체크: 진리표와 일치(✅).

[기본2] OR 게이트 구현

풀이 요약: 하나라도 1이면 1.

def OR(x1, x2):
    w1, w2, b = 0.5, 0.5, -0.2
    s = x1*w1 + x2*w2 + b
    return 1 if s > 0 else 0

for a in [0,1]:
    for b in [0,1]:
        print(a,b, OR(a,b))  # 00→0, 나머지→1


검토체크: 진리표 일치(✅).

[기본3] NAND 게이트 구현

풀이 요약: AND의 반대. 둘 다 1일 때만 0.

def NAND(x1, x2):
    w1, w2, b = -0.5, -0.5, 0.7
    return 1 if (x1*w1 + x2*w2 + b) > 0 else 0

for a in [0,1]:
    for b in [0,1]:
        print(a,b, NAND(a,b))  # 11→0, 나머지→1


검토체크: 진리표 일치(✅).

[기본4] XOR 게이트 (조합)

풀이 요약: 단층 퍼셉트론으로는 불가 → NAND/OR/AND 조합.

def XOR(x1, x2):
    s1 = NAND(x1, x2)
    s2 = OR(x1, x2)
    return AND(s1, s2)

for a in [0,1]:
    for b in [0,1]:
        print(a,b, XOR(a,b))  # 01/10→1, 00/11→0


검토체크: XOR 진리표 일치(✅).

[심화] 퍼셉트론으로 직선 분류

풀이 요약: 선 ax+by+c=0 을 경계로 분류(≥0 → 1).

def classify_linear(x, y, a=2, b=1, c=-3):
    # 2x + y - 3 = 0 선 위/위쪽이면 1, 아래면 0
    return 1 if (a*x + b*y + c) >= 0 else 0

print(classify_linear(1,2))  # 2*1+2-3=1 ≥0 → 1
print(classify_linear(0,1))  # 0+1-3=-2 <0 → 0


검토체크: 선 위/아래 판정 논리 확인(✅).

[보충] 가중치/편향을 바꿔 경계 실험

풀이 요약: 여러 (w1,w2,b)를 바꿔가며 점들의 라벨이 어떻게 바뀌는지 관찰.

def perceptron_binary(x, y, w1, w2, b):
    return 1 if (w1*x + w2*y + b) >= 0 else 0

pts = [(0,0),(1,0),(0,1),(1,1),(2,1),(1,2)]
params = [(1,1,-1), (1,-1,0), (0.5,0.3,-0.2)]
for (w1,w2,b) in params:
    labels = [perceptron_binary(x,y,w1,w2,b) for (x,y) in pts]
    print((w1,w2,b), labels)


검토체크: 파라미터 변화에 따라 경계가 바뀌는지 확인(✅).
