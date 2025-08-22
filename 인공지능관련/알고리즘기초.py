2장 심화 문제
문제: 1부터 1,000까지 더할 때, 반복문 방법과 공식 방법 중 어떤 것이 더 빠를까요?

풀이:
반복문: 1부터 1000까지 하나씩 더해야 하므로, 총 1000번의 덧셈이 필요해요.

공식: n*(n+1)//2를 한 번만 계산하면 돼요.
👉 따라서 공식 방법이 훨씬 빠릅니다.


3장 심화 문제

문제: 반 친구들의 키 [150, 160, 145, 170, 155] 중에서 최댓값을 구하세요.

풀이 (코드):

def find_max(a):
    n = len(a)
    max_v = a[0]
    for i in range(1, n):
        if a[i] > max_v:
            max_v = a[i]
    return max_v

heights = [150, 160, 145, 170, 155]
print(find_max(heights))  # 출력: 170

👉 최댓값은 170cm


4장 심화 문제
문제: ["Anna", "Lina", "Anna", "Mina", "Lina"] 에서 동명이인을 모두 찾아보세요.

풀이 (코드):

def find_same_name(a):
    n = len(a)
    result = set()
    for i in range(0, n-1):
        for j in range(i+1, n):
            if a[i] == a[j]:
                result.add(a[i])
    return result

names = ["Anna", "Lina", "Anna", "Mina", "Lina"]
print(find_same_name(names))  # 출력: {'Anna', 'Lina'}

👉 동명이인은 Anna, Lina

5장 심화 문제

문제: 하노이의 탑에서 원반 3개를 옮기는 과정을 단계별로 쓰세요.

풀이:
규칙: n개의 원반을 옮기려면 → n-1개를 먼저 옮기고, 제일 큰 원반을 옮긴 뒤, 다시 n-1개를 옮긴다.

1번 기둥 → 3번 기둥 (보조: 2번)

원반1: 1 → 3

원반2: 1 → 2

원반1: 3 → 2

원반3: 1 → 3

원반1: 2 → 1

원반2: 2 → 3

원반1: 1 → 3

👉 총 7번에 옮길 수 있어요. 일반적으로 원반 n개를 옮기는 데 필요한 횟수는 2^n - 1 번입니다.
