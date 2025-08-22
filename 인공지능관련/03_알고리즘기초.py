3단원 알고리즘 기초
[기본1] 1부터 n까지 합

풀이 요약: 반복문/공식 두 가지.

def sum_loop(n):
    s = 0
    for i in range(1, n+1):
        s += i
    return s

def sum_gauss(n):
    return n*(n+1)//2

print(sum_loop(10), sum_gauss(10))  # 55 55
# 검토: 두 값 일치(✅)

[기본2] 최대값 찾기
def find_max(a):
    m = a[0]
    for x in a[1:]:
        if x > m: m = x
    return m

print(find_max([18,93,20,33,58,7,32,41]))  # 93
# 검토: 내장 max와 동일(✅)

[기본3] 동명이인 찾기(리스트)
def find_same_name(names):
    count = {}
    for nm in names:
        count[nm] = count.get(nm, 0) + 1
    return {nm for nm,c in count.items() if c >= 2}

print(find_same_name(["Tom","Jerry","Mike","Tom"]))  # {'Tom'}
# 검토: 중복만 집합으로(✅)

[기본4] 최대공약수(GCD)
def gcd(a,b):
    while b:
        a,b = b, a%b
    return a

print(gcd(60,24))  # 12
# 검토: 유클리드 호제법(✅)

[기본5] 최소공배수(LCM)
def lcm(a,b):
    from math import gcd as _g
    return a*b // _g(a,b)

print(lcm(12,18))  # 36
# 검토: a*b = gcd* lcm 성질로 확인(✅)

[기본6] 피보나치 (재귀/반복)
def fibo_rec(n):
    if n<=1: return n
    return fibo_rec(n-1) + fibo_rec(n-2)

def fibo_it(n):
    a,b = 0,1
    for _ in range(n):
        a,b = b, a+b
    return a

print(fibo_rec(10), fibo_it(10))  # 55 55
# 검토: 두 방식 일치(✅)  ※ 큰 n은 반복 권장

[심화] 하노이의 탑 이동 순서
def hanoi(n, a, b, c):  # a→c로 n개, 보조 b
    if n==1:
        print(a,'→',c); return
    hanoi(n-1, a, c, b)
    print(a,'→',c)
    hanoi(n-1, b, a, c)

# 예: hanoi(3,'A','B','C')
# 검토: 이동 횟수 2^n-1개(3개면 7번)(✅)
