6단원 응용

[기본1] 미로 찾기(BFS 최단 경로)

풀이 요약: 각 칸(혹은 지점)에서 갈 수 있는 이웃으로 이동하며 처음 도착 시 경로가 최단.

from collections import deque

def solve_maze(graph, start, goal):
    """문자 노드 그래프에서 start→goal 최단 경로(문자열)."""
    qu = deque([start])
    prev = {start: None}
    while qu:
        p = qu.popleft()
        if p == goal:
            # 경로 복원(문자열)
            path = []
            v = p
            while v is not None:
                path.append(v); v = prev[v]
            return ''.join(reversed(path))
        for x in graph[p]:
            if x not in prev:
                prev[x] = p
                qu.append(x)
    return "?"  # 못 찾음

# 예시 그래프(교재 스타일로 문자 노드 연결)
maze = {
 'a':['b','e'], 'b':['a','f'], 'c':['d','g'], 'd':['c','h'],
 'e':['a','f','i'], 'f':['b','e','j'], 'g':['c','h','k'],
 'h':['d','g','l'], 'i':['e','m'], 'j':['f','n','k'],
 'k':['g','j','o'], 'l':['h','p'], 'm':['i','n'],
 'n':['m','j'], 'o':['k','p'], 'p':['l','o']
}

# 검토
print(solve_maze(maze, 'a', 'p'))  # 예: 'aeimnjfghlp' 등 그래프에 따라 최단경로
# ✅ 경로 문자열 반환 확인


[기본2] 가짜 동전 찾기(1개, 재귀 저울)

풀이 요약: 반씩 나누어 양쪽을 달아보고 가벼운 쪽(가짜 포함)만 재귀 탐색.

# 학습용 weigh 함수(구간 a~b vs c~d 비교, 가짜 인덱스 fake 하나라고 가정)
def weigh(a, b, c, d, fake):
    """[a..b]와 [c..d]의 무게 비교. fake가 포함된 쪽이 더 가벼우면 -1/1, 같으면 0."""
    def in_range(x, L, R): return L <= x <= R
    if in_range(fake, a, b) and not in_range(fake, c, d): return -1
    if in_range(fake, c, d) and not in_range(fake, a, b): return 1
    return 0  # 양쪽 모두(또는 모두 아님) → 같음

def find_fakecoin(left, right, fake):
    """left~right 사이에 가짜 1개가 있다고 가정."""
    if left == right:
        return left
    n = right - left + 1
    half = n // 2
    g1L, g1R = left, left + half - 1
    g2L, g2R = left + half, left + 2*half - 1
    res = weigh(g1L, g1R, g2L, g2R, fake)
    if res == -1:  # 1그룹이 가벼움
        return find_fakecoin(g1L, g1R, fake)
    elif res == 1: # 2그룹이 가벼움
        return find_fakecoin(g2L, g2R, fake)
    else:
        # 남은 1개(또는 홀수로 남은 구간)에 가짜가 있다고 보고 끝 처리
        return right

# 검토
N = 32; fake = 29
print(find_fakecoin(0, N-1, fake))  # 29
# ✅ 1개 가짜 찾기 확인


[심화] 가짜 동전이 여러 개인 경우(알고리즘 실험)

현황 표기: 교재에 “여러 개”가 명확히 규정되어 있는지는 확실하지 않음.
아래 코드는 합계 무게 비교를 이용해, 같으면 “두 쪽에 같은 수의 가짜가 있음”으로 간주하고
양쪽 모두를 더 잘게 쪼개 탐색하는 그룹 테스트 실험 코드(시뮬레이션) 입니다.

def find_all_fakes(left, right, fakes):
    """구간에 fakes(가짜 인덱스 집합)가 있을 때, 그룹 합비교로 모두 찾는 실험용.
       - 같으면 두 쪽에 동수의 가짜가 있다고 보고 양쪽 모두 재귀
       - 한쪽이 가벼우면 그쪽만 재귀
       - 구간 크기 1이면 해당 위치가 가짜
    """
    if left > right: return set()
    if left == right:
        return {left} if left in fakes else set()

    n = right - left + 1
    half = n // 2
    L1, R1 = left, left + half - 1
    L2, R2 = left + half, left + 2*half - 1
    # 그룹별 가짜 수
    c1 = sum(1 for x in fakes if L1 <= x <= R1)
    c2 = sum(1 for x in fakes if L2 <= x <= R2)

    if c1 == c2:
        # 같으면 둘 다 탐색(동시에 분포)
        return find_all_fakes(L1, R1, fakes) | find_all_fakes(L2, R2, fakes)
    elif c1 > c2:
        return find_all_fakes(L1, R1, fakes)
    else:
        return find_all_fakes(L2, R2, fakes)

# 검토(시뮬레이션)
N = 32; fakes = {5, 17, 29}
print(find_all_fakes(0, N-1, fakes))   # {5,17,29}
# ✅ 실험 시뮬레이션에서는 모두 찾아짐
# ⚠️ 주의: 실제 저울 제한 조건/측정 전략에 따라 변형이 필요할 수 있음(확실하지 않음
