✅ 문제 1: 가장 친구가 많은 사람 찾기

# 그래프(친구 관계)
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

def most_friends(g):
    max_count = -1
    max_person = None
    for person in g:
        count = len(g[person])   # 친구 수 세기
        if count > max_count:
            max_count = count
            max_person = person
    return max_person, max_count

print(most_friends(fr_info))
# 결과: ('Justin', 4)



✅ 문제 2: 두 사람 사이의 친밀도(거리) 구하기

def friend_distance(g, start, target):
    from collections import deque
    qu = deque()
    qu.append((start, 0))  # (사람 이름, 거리)
    done = set()
    done.add(start)

    while qu:
        person, dist = qu.popleft()
        if person == target:
            return dist
        for x in g[person]:
            if x not in done:
                qu.append((x, dist + 1))
                done.add(x)
    return -1  # 연결되지 않은 경우

print(friend_distance(fr_info, 'Summer', 'Kim'))
# 결과: 3


✅ 문제 3: 동명이인 + 친구 관계 찾기

# 동명이인 찾기 (딕셔너리 활용)
def find_same_name(a):
    name_dict = {}
    for name in a:
        if name in name_dict:
            name_dict[name] += 1
        else:
            name_dict[name] = 1

    result = set()
    for name in name_dict:
        if name_dict[name] >= 2:
            result.add(name)
    return result

# 동명이인의 친구 찾기
def duplicate_friends(names, g):
    duplicates = find_same_name(names)
    result = {}
    for name in duplicates:
        if name in g:
            result[name] = g[name]
        else:
            result[name] = []
    return result

name_list = ["Tom", "Jerry", "Mike", "Tom"]
print(duplicate_friends(name_list, fr_info))
# 결과: {'Tom': ['Jerry']}


