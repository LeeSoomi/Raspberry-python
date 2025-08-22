5단원 자료구조

[기본1] 리스트 기본

풀이 요약: 추가/삭제/탐색 등 기본 연습.

a = [10, 20, 30]
a.append(40)        # [10,20,30,40]
a.remove(20)        # [10,30,40]
idx = a.index(30)   # 1
# 검토
print(a, idx)       # [10, 30, 40] 1
# ✅ 기본 조작 확인


[기본2] 딕셔너리로 동명이인 찾기

풀이 요약: 이름 → 횟수 카운팅, 2회 이상만 집합으로 반환.

def find_same_name_dict(names):
    """동명이인(2회 이상) 이름 집합 반환."""
    cnt = {}
    for nm in names:
        cnt[nm] = cnt.get(nm, 0) + 1
    return {nm for nm, c in cnt.items() if c >= 2}

# 검토
print(find_same_name_dict(["Tom","Jerry","Mike","Tom"]))  # {'Tom'}
# ✅ 동작 확인


[기본3] 그래프(친구 관계) 표현

풀이 요약: 사람→친구목록(인접 리스트).

fr_info = {
    'Summer': ['John', 'Justin', 'Mike'],
    'John':   ['Summer', 'Justin'],
    'Justin': ['John', 'Summer', 'Mike', 'May'],
    'Mike':   ['Summer', 'Justin'],
    'May':    ['Justin', 'Kim'],
    'Kim':    ['May'],
    'Tom':    ['Jerry'],
    'Jerry':  ['Tom'],
}
# 검토: 노드/간선 수 확인(간단 프린트)
print(len(fr_info), sum(len(v) for v in fr_info.values()))
# ✅ 구조 확인


[기본4] BFS로 모든 친구 출력

풀이 요약: 큐로 “가까운 친구부터” 방문(중복 방지).

def print_all_friends(g, start):
    """start부터 BFS 순서로 이름 출력."""
    qu = [start]
    seen = {start}
    order = []
    while qu:
        p = qu.pop(0)
        order.append(p)
        for x in g[p]:
            if x not in seen:
                seen.add(x); qu.append(x)
    return order

# 검토
print(print_all_friends(fr_info, 'Summer'))
# 예: ['Summer','John','Justin','Mike','May','Kim']
# ✅ BFS 순서 확인


[기본5] BFS로 친밀도(단계) 계산

풀이 요약: (이름, 거리) 튜플로 큐에 넣어 레벨 증가.

def friend_distance_table(g, start):
    """start에서 각 사람까지의 단계 수(최단거리) 딕셔너리."""
    dist = {start: 0}
    qu = [start]
    while qu:
        p = qu.pop(0)
        for x in g[p]:
            if x not in dist:
                dist[x] = dist[p] + 1
                qu.append(x)
    return dist

# 검토
print(friend_distance_table(fr_info, 'Summer'))
# 예: {'Summer':0,'John':1,'Justin':1,'Mike':1,'May':2,'Kim':3}
# ✅ 단계 확인


[보충1] 큐 자료구조 직접 구현

풀이 요약: 리스트로 큐 클래스(append/popleft) 구현.

class Queue:
    """간단 큐 구현(학습용)."""
    def __init__(self):
        self._d = []
    def push(self, x):
        self._d.append(x)
    def pop(self):
        if not self._d: return None
        return self._d.pop(0)   # 학습용 간단 구현(효율은 낮음)
    def empty(self):
        return len(self._d) == 0

# 검토
q = Queue(); q.push(1); q.push(2)
print(q.pop(), q.pop(), q.pop())  # 1 2 None
# ✅ 동작 확인


[보충2] 두 사람 사이 최단 경로 출력

풀이 요약: BFS에서 prev로 역추적해 경로 복원.

from collections import deque

def shortest_path(g, s, t):
    """그래프 g에서 s→t 최단 경로(리스트). 없으면 []."""
    qu = deque([s]); prev = {s: None}
    while qu:
        v = qu.popleft()
        if v == t:
            # 경로 복원
            path = []
            while v is not None:
                path.append(v); v = prev[v]
            return list(reversed(path))
        for w in g[v]:
            if w not in prev:
                prev[w] = v
                qu.append(w)
    return []

# 검토
print(shortest_path(fr_info, 'Summer', 'Kim'))  # ['Summer','Justin','May','Kim']
# ✅ 최단 경로 확인
