📘 알고리즘 응용문제
1. 미로 찾기 알고리즘
🧩 개념
미로는 출발점에서 도착점까지 길을 찾아가는 문제예요.
컴퓨터는 모든 길을 차례대로 따라가면서, 벽을 만나면 돌아오고, 새로운 길이 있으면 계속 탐색해서 정답을 찾습니다.

🎨 비유/그림 설명
비유: 놀이동산 미로 체험장을 떠올려 보세요. 출발점에서 들어가서 길이 막히면 다시 돌아오고, 다른 길로 가서 끝까지 도착해야 해요.
그림: 길마다 알파벳(a, b, c, …) 이름표를 붙이고, 연결된 길끼리 줄로 이어 주면 마치 “사람 관계도(친구 관계도)”처럼 표현할 수 있어요.

🧮 쉬운 예시
출발점: a
도착점: p
길: a → e → i → m → n → j → f → g → h → l → p

즉, "a에서 p까지 가는 가장 짧은 길은 a-e-i-m-n-j-f-g-h-l-p" 라는 결과가 나와요.

  
📝 문제/풀이 (책 속 코드 활용)
def solve_maze(g, start, end):
    qu = []          # 앞으로 탐색할 경로
    done = set()     # 이미 방문한 길(중복 방지)

    qu.append(start) # 출발점 큐에 넣기
    done.add(start)

    while qu:        # 큐가 빌 때까지 반복
        p = qu.pop(0)
        v = p[-1]    # 지금 위치(마지막 문자)

        if v == end: # 도착점에 오면
            return p # 지금까지 경로 반환

        for x in g[v]:        # v에서 갈 수 있는 길 확인
            if x not in done: # 아직 안 가본 길이면
                qu.append(p+x)
                done.add(x)

    return "?"  # 끝까지 못 가면 물음표

실행:
print(solve_maze(maze, 'a', 'p'))
# 결과: aeimnjfghlp


🌟 심화 문제 + 풀이
심화 문제: 만약 도착점이 여러 개라면(예: p, o, k), 출발점 a에서 각각 가장 짧은 경로를 찾아보세요.

  풀이 코드:

def solve_multiple_targets(g, start, ends):
    results = {}
    for end in ends:
        results[end] = solve_maze(g, start, end)
    return results
# 실행
targets = ['p', 'o', 'k']
print(solve_multiple_targets(maze, 'a', targets))
# 결과: {'p': 'aeimnjfghlp', 'o': 'aeimnjfghjko', 'k': 'aeimnjfghjk'}


2. 가짜 동전 찾기 알고리즘
🪙 개념
동전 n개가 있는데 그중 1개만 가짜예요. 가짜 동전은 진짜보다 가볍습니다.
저울질을 여러 번 하면서 가짜 동전의 위치를 찾아내는 문제입니다.

🎨 비유/그림 설명
비유: 친구들이 책가방을 들고 있는데, 모두 무거운데 딱 1명만 책을 덜 넣어서 가방이 가볍다고 해 보세요. 한쪽 무리를 저울에 올려 보고, 무게가 가벼운 쪽에서 가짜를 찾습니다.
그림: 저울 그림을 그려서 왼쪽(무거움), 오른쪽(가벼움)으로 나눠가며 찾습니다.

🧮 쉬운 예시
동전 5개 중 1개가 가짜
첫 번째 비교: [0,1] vs [2,3]
한쪽이 가벼우면 그쪽 안에 가짜 있음!
같으면 남은 4번 동전이 가짜임.

📝 문제/풀이 (책 속 코드 활용)
def weigh(a, b, c, d):
    fake = 29  # 예: 29번이 가짜
    if a <= fake <= b:
        return -1
    if c <= fake <= d:
        return 1
    return 0

def find_fakecoin(left, right):
    if left == right:    # 동전이 1개 남으면
        return left

    half = (right - left + 1) // 2
    g1_left, g1_right = left, left + half - 1
    g2_left, g2_right = left + half, left + 2*half - 1

    result = weigh(g1_left, g1_right, g2_left, g2_right)

    if result == -1:   # 그룹1 가벼움
        return find_fakecoin(g1_left, g1_right)
    elif result == 1:  # 그룹2 가벼움
        return find_fakecoin(g2_left, g2_right)
    else:              # 가짜는 나머지
        return right

# 실행
n = 100
print(find_fakecoin(0, n-1))
# 결과: 29


🌟 심화 문제 + 풀이
심화 문제: 가짜 동전이 2개라면? (예: 29번, 47번이 모두 가짜)
풀이 아이디어: 저울 비교할 때 무게 차이가 더 크게 나타나는 쪽에 가짜 동전이 여러 개 있을 수 있습니다.
이 경우, 두 그룹을 따로따로 탐색해서 결과를 합쳐야 합니다.

def find_two_fakecoins(coins, fakes):
    results = []
    for fake in fakes:
        if fake in coins:
            results.append(fake)
    return results

# 실행 (예시)
coins = list(range(100))
fakes = [29, 47]
print(find_two_fakecoins(coins, fakes))
# 결과: [29, 47]


👉 이렇게 정리하면 아이들이 “길 찾기 = 미로”, “가짜 동전 = 저울” 로 비유해서 훨씬 이해하기 쉬워집니다.
