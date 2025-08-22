4단원 탐색과 정렬

[기본1] 순차 탐색(선형 탐색)

풀이 요약: 왼쪽부터 하나씩 비교해서 찾으면 위치 반환, 못 찾으면 -1.

def search_list(a, x):
    """리스트 a에서 값 x의 위치를 왼쪽부터 찾는다. 없으면 -1."""
    for i, v in enumerate(a):
        if v == x:           # 같으면 위치 반환
            return i
    return -1                # 끝까지 못 찾으면 -1

# 검토
v = [17, 92, 18, 33, 58, 7, 33, 42]
print(search_list(v, 33))  # 3 (처음 등장 위치)
print(search_list(v, 999)) # -1
# ✅ 찾기/실패 동작 확인

[기본2] 선택 정렬

풀이 요약: 남은 구간에서 최솟값을 찾아 맨 앞과 교환.

def sel_sort(a):
    """선택 정렬: 매 단계 최솟값을 앞으로."""
    a = a[:]                 # 원본 보호
    n = len(a)
    for i in range(n-1):
        min_idx = i
        for j in range(i+1, n):
            if a[j] < a[min_idx]:
                min_idx = j
        a[i], a[min_idx] = a[min_idx], a[i]
    return a

# 검토
print(sel_sort([2,4,5,1,3]))          # [1,2,3,4,5]
# ✅ 오름차순 정렬 확인

[기본3] 삽입 정렬

풀이 요약: 이미 정렬된 왼쪽 구간에 현재 값을 알맞은 자리에 끼워 넣기.

def ins_sort(a):
    """삽입 정렬: 왼쪽 정렬구간에 삽입."""
    a = a[:]
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j+1] = a[j]   # 오른쪽으로 밀기
            j -= 1
        a[j+1] = key
    return a

# 검토
print(ins_sort([2,4,5,1,3]))          # [1,2,3,4,5]
# ✅ 동작 확인

[기본4] 병합 정렬(분할정복)

풀이 요약: 반으로 쪼개 재귀 정렬 → 두 정렬리스트 병합.

def merge_sort(a):
    """병합 정렬: 분할→정복→병합."""
    if len(a) <= 1:
        return a[:]
    mid = len(a)//2
    left = merge_sort(a[:mid])
    right = merge_sort(a[mid:])
    # 병합
    i = j = 0
    res = []
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            res.append(left[i]); i += 1
        else:
            res.append(right[j]); j += 1
    res.extend(left[i:]); res.extend(right[j:])
    return res

# 검토
print(merge_sort([6,8,3,9,10,1,2,4,7,5]))  # 1~10
# ✅ 정렬 완료 확인

[기본5] 퀵 정렬

풀이 요약: 피벗 기준으로 작/크 그룹 분할 → 재귀 정렬.

def quick_sort(a):
    """퀵 정렬: 피벗 기준 분할."""
    if len(a) <= 1:
        return a[:]
    pivot = a[-1]
    left  = [x for x in a[:-1] if x < pivot]
    right = [x for x in a[:-1] if x >= pivot]
    return quick_sort(left) + [pivot] + quick_sort(right)

# 검토
print(quick_sort([6,8,3,9,10,1,2,4,7,5]))
# ✅ 정렬 확인

[기본6] 이진 탐색(정렬된 리스트)

풀이 요약: 중간값과 비교해 왼/오쪽 절반만 계속 탐색.

def binary_search(a, x):
    """오름차순 정렬된 a에서 x의 인덱스(없으면 -1)."""
    l, r = 0, len(a)-1
    while l <= r:
        m = (l + r) // 2
        if a[m] == x: return m
        if a[m] < x:  l = m + 1
        else:         r = m - 1
    return -1

# 검토
arr = [1,3,5,7,9,11]
print(binary_search(arr, 7))   # 3
print(binary_search(arr, 2))   # -1
# ✅ 동작 확인

[기본7] 성적 순위 매기기

풀이 요약: 내림차순 정렬 순위를 원래 순서에 매핑.
※ 동점 처리 기준은 교재 정책 필요(확실하지 않음) — 아래에 두 방식 제공.

def rank_competition(scores):
    """경쟁 랭킹(1224식): 동점이면 같은 등수, 다음 등수는 건너뜀."""
    sorted_scores = sorted(scores, reverse=True)
    # 첫 등장 위치 +1을 등수로 사용
    return [sorted_scores.index(x) + 1 for x in scores]

def rank_dense(scores):
    """밀집 랭킹(1223식): 동점이면 같은 등수, 다음 등수는 바로 이어짐."""
    uniq = sorted(set(scores), reverse=True)
    pos = {v:i+1 for i,v in enumerate(uniq)}
    return [pos[x] for x in scores]

# 검토
scores = [100, 90, 90, 80]
print(rank_competition(scores))  # [1,2,2,4]
print(rank_dense(scores))        # [1,2,2,3]
# ✅ 두 방식 비교 출력. (교재 기준에 맞춰 선택)

[보충] 선택/삽입 정렬의 비교·교환 횟수 세기

풀이 요약: 알고리즘 내부에서 카운터를 증가시켜 성능 감각 익히기.

def sel_sort_stats(a):
    a = a[:]; comp = swap = 0
    n = len(a)
    for i in range(n-1):
        min_idx = i
        for j in range(i+1, n):
            comp += 1
            if a[j] < a[min_idx]:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]; swap += 1
    return a, comp, swap

def ins_sort_stats(a):
    a = a[:]; comp = swap = 0
    for i in range(1, len(a)):
        key = a[i]; j = i-1
        while j >= 0:
            comp += 1
            if a[j] > key:
                a[j+1] = a[j]; swap += 1; j -= 1
            else:
                break
        a[j+1] = key
    return a, comp, swap

# 검토
d = [5,4,3,2,1]
print(sel_sort_stats(d))  # (정렬된 리스트, 비교 수, 교환 수)
print(ins_sort_stats(d))
# ✅ 비교/교환 횟수 출력 확인
