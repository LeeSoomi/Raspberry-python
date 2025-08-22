A. “가장 친구가 많은 사람” 찾기
아이디어
각 사람의 친구 수(리스트 길이)를 재고, 최댓값을 가진 사람(들)을 고른다.
동점(여러 명이 같은 최댓값)도 고려해서 여러 명 리스트로 돌려준다.

def most_popular_people(g):
    # g: 이름 -> 친구목록(리스트)
    # 1) 각 사람의 친구 수 세기
    degree = {person: len(friends) for person, friends in g.items()}
    # 2) 가장 큰 친구 수 구하기
    max_deg = max(degree.values())
    # 3) 그 수를 가진 사람(들) 모아 돌려주기
    winners = [p for p, d in degree.items() if d == max_deg]
    return winners, max_deg

print(most_popular_people(fr_info))
# 예) (['Justin'], 4)  ← Justin이 친구 4명으로 1등


B. 두 사람 사이의 최단 친밀도(거리) 구하기 + 경로까지
아이디어
BFS는 “가까운 곳부터” 보므로, 처음 목적지를 만나면 그때 거리가 최단이에요.
줄에 (이름, 지금까지의 거리, 지나온 경로) 형태로 넣어 추적하면 실제 경로도 복원.

from collections import deque

def shortest_distance_and_path(g, start, goal):
    if start == goal:
        return 0, [start]  # 자기 자신은 거리 0

    qu = deque()
    qu.append((start, 0, [start]))  # (현재사람, 거리, 경로)
    visited = {start}

    while qu:
        cur, dist, path = qu.popleft()
        for nb in g[cur]:
            if nb in visited: 
                continue
            if nb == goal:
                return dist + 1, path + [nb]  # 목표 발견!
            visited.add(nb)
            qu.append((nb, dist + 1, path + [nb]))
    return None, []  # 연결 안 되어 있으면 없음

print(shortest_distance_and_path(fr_info, 'Summer', 'Kim'))
# 예) (3, ['Summer', 'Justin', 'May', 'Kim'])


C. “동명이인이 있는 이름들”과 그들의 친구 목록 묶어보기
아이디어
어떤 반의 이름 목록 names에서 동명이인을 찾고(2번 이상),
그래프 fr_info에 같은 이름의 노드가 있을 때 그 친구 목록까지 함께 모은다.
반환은 이름 → {'count': 등장횟수, 'friends': 친구리스트 또는 없음} 형태의 딕셔너리.

def duplicate_names_with_friends(names, g):
    # 1) 이름 등장 횟수 세기
    cnt = {}
    for nm in names:
        cnt[nm] = cnt.get(nm, 0) + 1

    result = {}
    for nm, c in cnt.items():
        if c >= 2:  # 동명이인만 뽑기
            result[nm] = {
                'count': c,
                'friends': g.get(nm, None)  # 그래프에 없을 수도 있으니 .get()
            }
    return result

names = ["Tom", "Jerry", "Mike", "Tom", "Alex", "Alex", "Kim"]
print(duplicate_names_with_friends(names, fr_info))
# 예) {'Tom': {'count': 2, 'friends': ['Jerry']}, 'Alex': {'count': 2, 'friends': None}}


