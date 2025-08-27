5단원 자료구조

1) 딕셔너리 기초(빠른 요약 + 안전 사용 팁)
# 딕셔너리: '이름표(키) → 값'을 연결해 보관하는 상자
# 예) 사람 이름(키) → 나이(값)
ages = {"Justin": 13, "John": 10, "Mike": 9}

# 길이(몇 개 들어 있나)
print(len(ages))  # 3

# 값 읽기(키로 찾기)
print(ages["Mike"])  # 9

# 값 넣기/덮어쓰기
ages["Summer"] = 1   # 새로 추가
ages["Summer"] = 2   # 같은 키에 넣으면 '덮어쓰기' 됨(이제 2)

# 안전하게 읽기: 없으면 기본값 주기(KeyError 예방!)
print(ages.get("Alex", "없음"))  # 없음

# 삭제/비우기
del ages["Summer"]  # 'Summer' 항목 제거
ages.clear()        # 모두 삭제(빈 딕셔너리)


------------------------------------------------------------------------

2) 동명이인 찾기(딕셔너리 이용)
def find_same_name(names):
    """
    [문제] 이름 목록에서 '두 번 이상' 나온 이름들을 찾아 집합으로 반환
    [생각] 이름이 나오면 '횟수'를 1씩 올린다 → 2 이상이면 중복!
    """
    count = {}                 # 이름표 사전: 이름 → 등장 횟수
    for nm in names:           # 이름을 하나씩 꺼내서
        count[nm] = count.get(nm, 0) + 1  # 없으면 0부터, 있으면 +1

    # 횟수가 2 이상인 이름만 골라 '중복 이름집합' 만들기
    result = {nm for nm, c in count.items() if c >= 2}
    return result


# 예시
name1 = ["Tom", "Jerry", "Mike", "Tom"]
print(find_same_name(name1))   # {'Tom'}

name2 = ["Tom", "Jerry", "Mike", "Tom", "Mike"]
print(find_same_name(name2))   # {'Tom', 'Mike'}


------------------------------------------------------------------------


3) 그래프로 “친구의 친구” 찾기
3-1) 친구 관계를 그래프로 표현(무방향 그래프, 인접 리스트)
# 교재의 친구 관계를 그대로 '양쪽 방향'으로 적어 준 그래프
fr_info = {
    "Summer": ["John", "Justin", "Mike"],
    "John":   ["Summer", "Justin"],
    "Justin": ["John", "Summer", "Mike", "May"],
    "Mike":   ["Summer", "Justin"],
    "May":    ["Justin", "Kim"],
    "Kim":    ["May"],
    "Tom":    ["Jerry"],
    "Jerry":  ["Tom"],
}


꼭 기억: “서로 친구”면 두 사람 둘 다의 리스트에 서로의 이름이 들어 있어야 해요(무방향).

3-2) 모든 친구(직접/간접)를 한 번씩 방문해 출력(BFS)
def print_all_friends(g, start):
    """
    [문제] start 사람부터 '친구의 친구의 친구…'를 줄서서 모두 찾아 출력
    [아이디어] 큐(줄) + 체크(visited)
      1) 줄(qu)에 'start'를 넣고 시작
      2) 줄에서 한 명 꺼내 출력
      3) 그 사람 친구들을 보며, 아직 줄에 안 넣어봤다면 줄 뒤에 추가
      4) 줄이 빌 때까지 2~3 반복
    """
    qu = []         # 앞으로 처리할 사람들(줄)
    done = set()    # 이미 줄에 넣어 본 사람들(중복 방지)

    qu.append(start)    # 자기 자신부터 줄 세우기
    done.add(start)     # '이 사람은 줄에 넣어봤다' 표시

    order = []          # 보기 좋게 출력하기 위해 모아 두기
    while qu:           # 줄이 빌 때까지 반복
        p = qu.pop(0)   # 맨 앞 사람 한 명 꺼내기
        order.append(p) # 출력 목록에 추가
        for friend in g[p]:      # p의 친구들을 훑으며
            if friend not in done:
                qu.append(friend)  # 아직 줄에 안 섰으면 줄 뒤에!
                done.add(friend)   # 이제 넣어 봤다고 표시
    print(", ".join(order))


# 예시(교재와 동일 순서로 나올 수 있음)
print_all_friends(fr_info, "Summer")
# 예시 출력: Summer, John, Justin, Mike, May, Kim

print_all_friends(fr_info, "Jerry")
# 예시 출력: Jerry, Tom


왜 BFS?
가까운 친구부터 차례차례(0단계 → 1단계 → 2단계 …) 살펴보게 해 줘요. 그래서 “친밀도(몇 단계 떨어져 있는지)”를 알기에도 딱 좋아요.


------------------------------------------------------------------------


3-3) 친밀도(단계 수)까지 함께 출력하는 BFS(심화)
def print_all_friends_with_degree(g, start):
    """
    [문제] start로부터 모든 사람의 '친밀도(몇 단계 떨어졌는지)'를 함께 출력
    [아이디어] 큐에 (사람이름, 친밀도) 튜플로 저장
       - 나 자신은 0단계
       - 친구는 1단계, 친구의 친구는 2단계 …로 1씩 증가
    """
    qu = []
    done = set()
    qu.append((start, 0))  # (이름, 친밀도)
    done.add(start)

    items = []
    while qu:
        person, d = qu.pop(0)
        items.append(f"{person} {d}")
        for friend in g[person]:
            if friend not in done:
                qu.append((friend, d + 1))  # 친밀도 1 증가해서 줄에 넣기
                done.add(friend)

    print(", ".join(items))


# 예시(교재와 같은 형태)
print_all_friends_with_degree(fr_info, "Summer")
# 예시: Summer 0, John 1, Justin 1, Mike 1, May 2, Kim 3

print_all_friends_with_degree(fr_info, "Jerry")
# 예시: Jerry 0, Tom 1


------------------------------------------------------------------------


(선택 보충) 유틸: 친구 쌍 목록으로부터 그래프 만들기
def build_graph_from_pairs(pairs):
    """
    [입력] [('Summer','John'), ('Summer','Justin'), ...] 같은 친구 쌍 목록
    [출력] 무방향 그래프 딕셔너리(서로 친구이므로 양쪽에 모두 추가)
    """
    g = {}
    for a, b in pairs:
        g.setdefault(a, []).append(b)
        g.setdefault(b, []).append(a)
    return g

pairs = [
    ("Summer","John"), ("Summer","Justin"), ("Summer","Mike"),
    ("Justin","May"), ("May","Kim"), ("John","Justin"),
    ("Justin","Mike"), ("Tom","Jerry")
]
g2 = build_graph_from_pairs(pairs)
print_all_friends_with_degree(g2, "Summer")

한 장 요약(개념)

딕셔너리: 이름표(키)로 값을 바로 찾는 빠른 상자. get()을 쓰면 안전!

그래프(인접 리스트): 사람 → 친구목록. “서로 친구”면 양쪽에 모두 넣기.

BFS: 가까운 사람부터 차례로 방문(큐 사용) → 친밀도 계산에 딱!
