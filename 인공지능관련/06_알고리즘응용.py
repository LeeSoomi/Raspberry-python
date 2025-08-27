6단원 응용

🌀 1. 미로 찾기 알고리즘 (그래프 탐색 BFS)
# 미로 찾기 문제: 시작점 → 도착점까지 가장 짧은 길 찾기
# 아이디어: 미로를 '그래프(꼭짓점과 선)'로 표현하고 BFS(큐)를 이용

def solve_maze(g, start, end):
    """
    g     : 미로(그래프) 정보를 담은 딕셔너리
    start : 출발점 (예: 'a')
    end   : 도착점 (예: 'p')
    """
    qu = []         # 앞으로 처리할 경로(줄)
    done = set()    # 이미 처리한 위치(중복 방지)

    qu.append(start)    # 출발점 넣기
    done.add(start)

    while qu:   # 줄이 빌 때까지
        p = qu.pop(0)   # 한 경로 꺼내기
        v = p[-1]       # 현재 경로의 마지막 위치
        if v == end:    # 도착했으면 성공
            return p
        for x in g[v]:  # 현재 위치와 연결된 이웃들
            if x not in done:
                qu.append(p + x)  # 새로운 위치 붙여서 큐에 저장
                done.add(x)
    return "?"   # 길을 못 찾으면 ? 반환


# 미로 그래프 (교재 그림을 딕셔너리로 바꾼 것)
maze = {
    'a': ['e'],
    'b': ['c', 'f'],
    'c': ['b', 'd'],
    'd': ['c'],
    'e': ['a', 'i'],
    'f': ['b', 'g', 'j'],
    'g': ['f', 'h'],
    'h': ['g', 'l'],
    'i': ['e', 'm'],
    'j': ['f', 'k', 'n'],
    'k': ['j', 'o'],
    'l': ['h', 'p'],
    'm': ['i', 'n'],
    'n': ['m', 'j'],
    'o': ['k'],
    'p': ['l']
}

# 실행 예시
print(solve_maze(maze, 'a', 'p'))   # 교재 예시: 'aeimnjfghlp'


------------------------------------------------------------------------


⚖️ 2. 가짜 동전 찾기 알고리즘

진짜 동전은 모두 무게 같음

가짜 동전 1개는 더 가볍다

저울질 함수 weigh(a, b, c, d)를 제공 → 구간 [ab], [cd] 비교

방법1: 하나씩 비교하기
def weigh(a, b, c, d):
    """
    실제 저울질 함수 (시뮬레이션용)
    a~b 구간 vs c~d 구간 무게 비교
    -1 : 가짜 동전이 왼쪽 구간에 있다
     1 : 가짜 동전이 오른쪽 구간에 있다
     0 : 양쪽 무게가 같다 (둘 다 아님)
    """
    fake = 29   # 가짜 동전 위치(예시: 29번 동전이 가짜)
    if a <= fake <= b: return -1
    if c <= fake <= d: return 1
    return 0


def find_fakecoin1(left, right):
    """하나씩 차례대로 비교하는 방법"""
    for i in range(left + 1, right + 1):
        result = weigh(left, left, i, i)
        if result == -1:
            return left
        elif result == 1:
            return i
    return -1   # 못 찾은 경우


# 실행 예시
n = 100   # 동전 총 개수
print(find_fakecoin1(0, n-1))   # 결과: 29


------------------------------------------------------------------------



방법2: 반으로 나누어 비교하기 (이진 탐색 응용)
def find_fakecoin2(left, right):
    """동전을 반으로 나누어 가짜 동전을 찾는 방법"""
    # 종료 조건: 동전이 1개 남았으면 그것이 가짜
    if left == right:
        return left

    # 동전을 절반으로 나누기
    half = (right - left + 1) // 2
    g1_left, g1_right = left, left + half - 1
    g2_left, g2_right = g1_right + 1, g1_right + half

    # 두 그룹 비교
    result = weigh(g1_left, g1_right, g2_left, g2_right)
    if result == -1:   # 가짜는 그룹1 안에 있음
        return find_fakecoin2(g1_left, g1_right)
    elif result == 1:  # 가짜는 그룹2 안에 있음
        return find_fakecoin2(g2_left, g2_right)
    else:              # 둘 다 아니면 나머지 그룹에 있음
        return right


# 실행 예시
print(find_fakecoin2(0, n-1))   # 결과: 29

