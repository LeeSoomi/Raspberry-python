탐색과 정렬


[기본1] 순차 탐색 (Linear Search)
def search_list(a, x):
    """
    리스트 a 안에서 값 x를 앞에서부터 하나씩 차례대로 찾는 함수
    - 찾으면 그 위치(인덱스)를 돌려줌
    - 끝까지 못 찾으면 -1을 돌려줌
    """
    n = len(a)   # 리스트 크기
    for i in range(n):   # 0번부터 n-1번까지 차례로
        if x == a[i]:    # 만약 찾는 값과 같다면
            return i     # 그 위치를 바로 돌려줌
    return -1            # 끝까지 못 찾았다면 -1

# 예시
v = [17, 92, 18, 33, 58, 7, 33, 42]
print(search_list(v, 18))   # 2 (세 번째 위치)
print(search_list(v, 33))   # 3 (처음 등장한 위치)
print(search_list(v, 900))  # -1 (없음)


👉 포인트: 차례대로 비교 → 간단하지만 오래 걸릴 수 있음 (O(n))

--------------------------------------------------------------

[보충] 순차 탐색 (모든 위치 찾기)
def search_list_all(a, x):
    """
    리스트 안에서 값 x가 있는 모든 위치를 찾아 돌려줌
    """
    result = []
    for i in range(len(a)):
        if a[i] == x:
            result.append(i)
    return result

print(search_list_all(v, 33))  # [3, 6] (33은 두 번 나옴)


--------------------------------------------------------------


[기본2] 선택 정렬 (Selection Sort)
(1) 설명용 – 최소값을 하나씩 꺼내 새 리스트에 저장
def sel_sort_explain(a):
    """
    설명용 선택정렬:
    - 남은 값 중에서 가장 작은 값을 뽑아 새로운 리스트에 추가
    """
    result = []
    while a:  # a가 빌 때까지 반복
        min_value = min(a)     # 가장 작은 값 찾기
        a.remove(min_value)    # 원래 리스트에서 제거
        result.append(min_value) # 결과 리스트에 추가
    return result

d = [2, 4, 5, 1, 3]
print(sel_sort_explain(d[:]))   # [1,2,3,4,5]

(2) 일반 선택 정렬 – 리스트 안에서 직접 교환
def sel_sort(a):
    """
    일반 선택정렬:
    - 매번 남은 구간에서 가장 작은 값을 앞으로 보내기
    """
    n = len(a)
    for i in range(n-1):      # 0부터 n-2까지
        min_idx = i
        for j in range(i+1, n):   # i 뒤쪽 탐색
            if a[j] < a[min_idx]:
                min_idx = j
        a[i], a[min_idx] = a[min_idx], a[i]  # 값 교환
    return a

d = [2, 4, 5, 1, 3]
print(sel_sort(d[:]))  # [1,2,3,4,5]

--------------------------------------------------------------


[기본3] 삽입 정렬 (Insertion Sort)
(1) 설명용 – 적당한 위치 찾아 끼워 넣기
def ins_sort_explain(a):
    """
    설명용 삽입정렬:
    - 꺼낸 값을 적당한 자리에 끼워 넣기
    """
    result = []
    while a:
        value = a.pop(0)   # 맨 앞 값 꺼내기
        # result에서 적당한 위치를 찾아 끼워 넣음
        ins_idx = 0
        while ins_idx < len(result) and result[ins_idx] < value:
            ins_idx += 1
        result.insert(ins_idx, value)
    return result

d = [2,4,5,1,3]
print(ins_sort_explain(d[:]))  # [1,2,3,4,5]

(2) 일반 삽입 정렬
def ins_sort(a):
    """
    일반 삽입정렬:
    - 이미 정렬된 부분에 새로운 수를 적당히 끼워 넣음
    """
    n = len(a)
    for i in range(1, n):
        key = a[i]   # 끼워 넣을 값
        j = i-1
        while j >= 0 and a[j] > key:
            a[j+1] = a[j]  # 오른쪽으로 한 칸 밀기
            j -= 1
        a[j+1] = key       # 빈 자리에 삽입
    return a

d = [2,4,5,1,3]
print(ins_sort(d[:]))  # [1,2,3,4,5]

--------------------------------------------------------------


[기본4] 병합 정렬 (Merge Sort)
(1) 설명용 – 반씩 나눠서 합치기
def merge_sort_simple(a):
    """
    설명용 병합정렬:
    - 리스트를 반씩 나누어 정렬한 뒤 다시 합침
    """
    n = len(a)
    if n <= 1:
        return a
    mid = n//2
    g1 = merge_sort_simple(a[:mid])   # 앞쪽 절반
    g2 = merge_sort_simple(a[mid:])   # 뒤쪽 절반

    result = []
    while g1 and g2:
        if g1[0] < g2[0]:
            result.append(g1.pop(0))
        else:
            result.append(g2.pop(0))
    result.extend(g1)
    result.extend(g2)
    return result

d = [6,8,3,9,10,1,2,4,7,5]
print(merge_sort_simple(d))  # [1,2,3,4,5,6,7,8,9,10]

(2) 일반 병합 정렬 – 제자리 덮어쓰기
def merge_sort(a):
    """
    일반 병합정렬:
    - 리스트를 제자리에서 정렬
    """
    n = len(a)
    if n <= 1: return
    mid = n//2
    g1 = a[:mid]
    g2 = a[mid:]
    merge_sort(g1)
    merge_sort(g2)

    i1 = i2 = ia = 0
    while i1 < len(g1) and i2 < len(g2):
        if g1[i1] < g2[i2]:
            a[ia] = g1[i1]; i1+=1
        else:
            a[ia] = g2[i2]; i2+=1
        ia+=1
    while i1 < len(g1):
        a[ia] = g1[i1]; i1+=1; ia+=1
    while i2 < len(g2):
        a[ia] = g2[i2]; i2+=1; ia+=1

d = [6,8,3,9,10,1,2,4,7,5]
merge_sort(d)
print(d)  # [1,2,3,4,5,6,7,8,9,10]

--------------------------------------------------------------


[기본5] 퀵 정렬 (Quick Sort)
(1) 설명용 – 피벗 기준으로 나눠 이어붙이기
def quick_sort_simple(a):
    """
    설명용 퀵정렬:
    - 리스트를 피벗 기준으로 작/큰 그룹으로 나눈 뒤 재귀 정렬
    """
    n = len(a)
    if n <= 1:
        return a
    pivot = a[-1]      # 편의상 마지막 값을 피벗으로
    g1 = [x for x in a[:-1] if x < pivot]
    g2 = [x for x in a[:-1] if x >= pivot]
    return quick_sort_simple(g1) + [pivot] + quick_sort_simple(g2)

d = [6,8,3,9,10,1,2,4,7,5]
print(quick_sort_simple(d))  # [1,2,3,4,5,6,7,8,9,10]

(2) 일반 퀵 정렬 – 제자리 교환
def quick_sort_sub(a, start, end):
    if end - start <= 0: return
    pivot = a[end]
    i = start
    for j in range(start, end):
        if a[j] < pivot:
            a[i], a[j] = a[j], a[i]
            i+=1
    a[i], a[end] = a[end], a[i]
    quick_sort_sub(a, start, i-1)
    quick_sort_sub(a, i+1, end)

def quick_sort(a):
    quick_sort_sub(a, 0, len(a)-1)

d = [6,8,3,9,10,1,2,4,7,5]
quick_sort(d)
print(d)  # [1,2,3,4,5,6,7,8,9,10]

--------------------------------------------------------------


[심화] 보충 문제들
(1) 이진 탐색 (Binary Search, O(log n))
def binary_search(a, x):
    """
    이진 탐색:
    - 정렬된 리스트에서 중간값과 비교하며 범위를 반씩 줄여가기
    """
    start, end = 0, len(a)-1
    while start <= end:
        mid = (start+end)//2
        if a[mid] == x:
            return mid
        elif a[mid] < x:
            start = mid+1
        else:
            end = mid-1
    return -1

d = [1,2,3,4,5,6,7,8,9,10]
print(binary_search(d, 7))  # 6
print(binary_search(d, 99)) # -1
