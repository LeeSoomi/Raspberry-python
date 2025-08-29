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


2) 동명이인 찾기(딕셔너리 이용)   - 178페이지 예제

동명이인 찾기 알고리즘 설명
def find_same_name(a):
    # 1단계: 이름별 등장 횟수를 저장할 딕셔너리 생성
    name_dict = {}

    # 리스트 a의 이름을 하나씩 검사하며 등장 횟수를 저장
    for name in a:
        if name in name_dict:
            name_dict[name] += 1    # 이미 있는 이름이면 등장 횟수 +1
        else:
            name_dict[name] = 1     # 처음 등장한 이름이면 등장 횟수 1로 초기화

    # 2단계: 등장 횟수가 2회 이상인 이름만 결과로 모으기
    result = set()                  # 결과를 저장할 빈 집합 생성
    for name in name_dict:         # 딕셔너리에 있는 모든 이름 확인
        if name_dict[name] >= 2:   # 등장 횟수가 2 이상이면
            result.add(name)       # 결과 집합에 추가

    return result

📘 사용 예시
# 예시 1: "Tom"만 2번 등장 → 동명이인: {'Tom'}
name = ["Tom", "Jerry", "Mike", "Tom"]
print(find_same_name(name))   # 출력: {'Tom'}

# 예시 2: "Tom"과 "Mike"가 각각 2번 등장 → 동명이인: {'Mike', 'Tom'}
name2 = ["Tom", "Jerry", "Mike", "Tom", "Mike"]
print(find_same_name(name2))  # 출력: {'Mike', 'Tom'}

🔍 동작 원리 요약
단계	내용
1단계	이름 등장 횟수를 세기 위해 딕셔너리 생성
2단계	등장 횟수가 2 이상인 이름을 집합에 추가
출력	중복된 이름(동명이인)만 추려낸 결과 출력

------------------------------------------------------------------------

"모든 친구 찾기 알고리즘" 코드에 대해 자세하고 친절한 주석을 추가한 버전입니다. 
BFS(너비 우선 탐색)을 활용한 친구 탐색 방식이며, 
큐(qu)와 집합(done)을 사용하여 이미 방문한 사람을 중복 없이 처리

[모든 친구찾기 알고리즘] - 181페이지 예제

def print_all_friends(g, start):
    qu = []             # 앞으로 처리할 사람을 저장할 큐 (queue)
    done = set()        # 이미 처리한 사람을 저장할 집합 (중복 방지)
    
    qu.append(start)    # 시작점을 큐에 추가
    done.add(start)     # 시작점은 이미 방문했다고 표시

    while qu:           # 큐에 사람이 남아 있는 동안 반복
        p = qu.pop(0)   # 큐에서 한 명 꺼내기 (앞쪽부터)
        print(p)        # 현재 사람 출력

        for x in g[p]:              # 현재 사람의 친구들을 순회
            if x not in done:      # 아직 처리하지 않은 친구라면
                qu.append(x)       # 큐에 추가 (처리 예정)
                done.add(x)        # 처리한 것으로 표시

📦 친구 관계 그래프 (딕셔너리 형태)
fr_info = {
    'Summer': ['John', 'Justin', 'Mike'],
    'John': ['Summer', 'Justin'],
    'Justin': ['John', 'Summer', 'Mike', 'May'],
    'Mike': ['Summer', 'Justin'],
    'May': ['Justin', 'Kim'],
    'Kim': ['May'],
    'Tom': ['Jerry'],
    'Jerry': ['Tom']
}

▶ 실행 예시
print_all_friends(fr_info, 'Summer')

출력 결과:
Summer
John
Justin
Mike
May
Kim


print()
print_all_friends(fr_info, 'Jerry')

출력 결과:
Jerry
Tom

----------------------------------------------------------------

[ 친밀도 계산 알고리즘] = 183페이지 예제

친밀도 계산 알고리즘 (모든 친구의 이름과 친밀도 함께 출력)

def print_all_friends(g, start):
    qu = []                             # 📍 기억장소1: 앞으로 처리할 사람의 (이름, 친밀도) 정보 저장
    done = set()                        # 📍 기억장소2: 이미 큐에 추가한 사람들 (중복 방지용 집합)

    qu.append((start, 0))              # 🟢 첫 시작점: 자기 자신 (start)의 친밀도는 0
    done.add(start)                    # ✅ 자기 자신은 이미 방문한 것으로 처리

    while qu:                          # 🔁 큐에 처리할 대상이 남아 있는 동안 반복
        (p, d) = qu.pop(0)             # 🔻 큐에서 (이름, 친밀도) 한 명 꺼냄
        print(p, d)                    # 🖨️ 이름과 친밀도 출력

        for x in g[p]:                 # 👥 현재 사람 p의 친구들 중에서
            if x not in done:         # ✅ 아직 큐에 추가된 적이 없는 친구라면
                qu.append((x, d + 1)) # 🔺 친밀도를 1 증가시켜 큐에 추가
                done.add(x)           # 🟢 중복 추가 방지를 위해 집합에 기록

예시 데이터 (친구 관계 그래프)
fr_info = {
    'Summer': ['John', 'Justin', 'Mike'],
    'John': ['Summer', 'Justin'],
    'Justin': ['John', 'Summer', 'Mike', 'May'],
    'Mike': ['Summer', 'Justin'],
    'May': ['Justin', 'Kim'],
    'Kim': ['May'],
    'Tom': ['Jerry'],
    'Jerry': ['Tom']
}

사용 예시 (출력 포함)
print_all_friends(fr_info, 'Summer')
# 출력 결과:
# Summer 0
# John 1
# Justin 1
# Mike 1
# May 2
# Kim 3

print()  # 줄바꿈

print_all_friends(fr_info, 'Jerry')
# 출력 결과:
# Jerry 0
# Tom 1


💡 알고리즘 핵심 요약
BFS 방식으로 친구 관계를 탐색하면서, **친밀도(level)**를 함께 추적.
done 집합을 통해 이미 방문한 사람은 중복 방문하지 않도록 방지.
친밀도는 한 단계 멀어질 때마다 1씩 증가.
