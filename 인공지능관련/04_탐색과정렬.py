탐색과 정렬


[기본1] 순차 탐색 (Linear Search)  - 163페이지
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




--------------------------------------------------------------
--------------------------------------------------------------


[기본2] 선택 정렬 (Selection Sort)  - 165페이지 예시
def find_min_idx(a):
    """
    리스트 a에서 '가장 작은 값'이 있는 위치(인덱스)를 찾아 돌려준다.
    - min_idx 에 '지금까지 본 값 중 최소의 위치'를 기억하고, 더 작은 걸 만나면 바꿔준다.
    """
    n = len(a)
    min_idx = 0                     # 처음엔 0번 자리가 최소라고 가정
    for i in range(1, n):           # 1번부터 끝까지 차례대로
        if a[i] < a[min_idx]:       # 더 작은 값을 만나면
            min_idx = i             # 최소 위치를 그 자리로 바꾸기
    return min_idx

def sel_sort(a):
    """
    [설명용 선택정렬]
    남아 있는 값들 중 '최솟값'을 골라(b권에서 '선택') 빼서 새 리스트(result)에 담는다.
    이 과정을 a가 빌 때까지 반복하면 오름차순 정렬이 된다.
    """
  #  a = a[:]           # 원본 보존용 복사(설명 편하게 하기 위함)
    result = []        # 정렬된 값들이 들어갈 새 리스트
    step = 1

    while a:           # a에 값이 남아 있는 동안 반복
        print(f"\n[단계 {step}] 남은 리스트: {a}")
        min_idx = find_min_idx(a)       # 남은 값 중 최솟값의 인덱스
        min_val = a.pop(min_idx)        # 최솟값을 꺼내서
        print(f"  → 이번에 뽑은 최솟값: {min_val} (원래 위치 {min_idx})")
        result.append(min_val)          # 결과 리스트 끝에 붙이기
        print(f"  → 현재 결과(result): {result}")
        step += 1

    print(f"\n✅ 최종 정렬 결과: {result}")
    return result
# 실행 예시
d = [2, 4, 5, 1, 3]
sel_sort(d)

--------------------------------------------------------------
--------------------------------------------------------------

일반적인 선택 정렬 알고리즘   - 166 페이지 예시
def sel_sort(a):
    """
    선택 정렬(제자리 정렬, in-place):
    i번째 자리에 들어갈 '최솟값'을 i~끝 구간에서 찾아 i와 교환한다.
    이를 i=0..n-2까지 반복하면 오름차순 정렬 완료.
    시간복잡도 O(n^2), 추가 메모리 O(1)
    """
    n = len(a)                       # 데이터 개수 n
    for i in range(0, n-1):          # 0 ~ n-2까지
        min_idx = i                  # '지금 구간의 최솟값' 위치를 i로 가정
        for j in range(i+1, n):      # i 다음부터 끝까지 훑으면서
            if a[j] < a[min_idx]:    # 더 작은 값 발견하면
                min_idx = j          # 최솟값 위치 갱신
        a[i], a[min_idx] = a[min_idx], a[i]  # i번째와 최솟값 자리 교환

d = [2, 4, 5, 1, 3]
sel_sort(d)
print(d) 

--------------------------------------------------------------
--------------------------------------------------------------

[기본3] 삽입 정렬 (Insertion Sort)   
(1) 설명용 – 적당한 위치 찾아 끼워 넣기   - 167페이지 예시
삽입 정렬 기본 코드 + 자세한 주석
def find_ins_idx(r, v):
    """
    이미 정렬된 리스트 r에서 값 v가 '들어가야 할 인덱스'를 찾아주는 함수
    """
    for i in range(0, len(r)):     # 앞에서부터 차례대로 비교
        if v < r[i]:               # 자신보다 큰 값 발견 시
            return i              # 그 앞에 들어가야 하므로 인덱스 i 반환
    return len(r)                 # 끝까지 없으면 제일 뒤에 삽입

def ins_sort(a):
    """
    삽입 정렬: 값을 하나씩 꺼내면서 result에 '정렬된 상태로' 삽입
    """
    result = []                   # 정렬될 리스트

    while a:                      # a에 남은 값이 있을 동안 반복
        value = a.pop(0)          # a에서 첫 값을 꺼냄
        ins_idx = find_ins_idx(result, value)  # 삽입할 위치 찾기
        result.insert(ins_idx, value)          # 해당 위치에 삽입
        # 나머지 값들은 한 칸씩 밀림 (파이썬의 insert)

    return result

사용 예:
d = [2, 4, 5, 1, 3]
print(ins_sort(d))  # [1, 2, 3, 4, 5]

--------------------------------------------------------------

일반적인 삽입 정렬 알고리즘 - 168페이지 예제제
def ins_sort(a):
    n = len(a)  # 전체 데이터 길이 n

    for i in range(1, n):  # 1번 인덱스부터 n-1까지 반복
        key = a[i]         # 현재 삽입할 대상 값을 key에 저장
        j = i - 1          # j는 key 왼쪽 위치부터 시작

        # key보다 큰 값은 오른쪽으로 한 칸씩 이동
        while j >= 0 and a[j] > key:
            a[j+1] = a[j]  # 오른쪽으로 밀기
            j -= 1         # 왼쪽으로 이동하며 계속 비교

        # 올바른 자리를 찾았으므로 key를 삽입
        a[j+1] = key


사용 예:

d = [2, 4, 5, 1, 3]
ins_sort(d)
print(d)  # [1, 2, 3, 4, 5]

🔍 삽입 정렬 동작 과정 (리스트 변화 추적)

[2, 4, 5, 1, 3] 이 정렬될 때 과정:

초기 상태:
a = [2, 4, 5, 1, 3]

i=1, key=4

a[0]=2 < key, 아무것도 이동 안함 → 그대로 삽입
→ [2, 4, 5, 1, 3]

i=2, key=5

a[1]=4 < key, 그대로 삽입
→ [2, 4, 5, 1, 3]

i=3, key=1

a[2]=5 > key → 5 오른쪽으로

a[1]=4 > key → 4 오른쪽으로

a[0]=2 > key → 2 오른쪽으로

삽입: a[0]=1
→ [1, 2, 4, 5, 3]

i=4, key=3

a[3]=5 > key → 5 오른쪽으로

a[2]=4 > key → 4 오른쪽으로

a[1]=2 < key → 정지

삽입: a[2]=3
→ [1, 2, 3, 4, 5]


-------------------------------------------------------------------

쉽게 설명한 병합 정렬 알고리즘 - 169페이지 예제

📘 병합 정렬 알고리즘 (Merge Sort)
def merge_sort(a):
    n = len(a)  # 리스트 길이 구하기

    # 종료 조건: 길이가 1 이하이면 정렬할 필요 없음
    if n <= 1:
        return a

    # 중간 지점을 기준으로 두 그룹으로 나누기
    mid = n // 2
    g1 = merge_sort(a[:mid])   # 왼쪽 그룹을 재귀 호출로 정렬
    g2 = merge_sort(a[mid:])   # 오른쪽 그룹을 재귀 호출로 정렬

    # 두 정렬된 그룹을 병합 (merge)
    result = []  # 병합 결과를 저장할 리스트

    # 두 그룹에 모두 데이터가 남아있는 동안 반복
    while g1 and g2:
        if g1[0] < g2[0]:               # g1의 첫 값이 더 작으면
            result.append(g1.pop(0))    # g1의 첫 값을 빼서 result에 저장
        else:
            result.append(g2.pop(0))    # g2의 첫 값을 빼서 result에 저장

    # 위 반복에서 한 그룹이 먼저 끝났을 수 있음 → 남은 값들을 모두 result에 추가
    while g1:                           # g1에 값이 남아 있다면
        result.append(g1.pop(0))        # 남은 값을 모두 result에 추가
    while g2:                           # g2에 값이 남아 있다면
        result.append(g2.pop(0))        # 남은 값을 모두 result에 추가

    return result

🔍 예제
d = [6, 8, 3, 9, 10, 1, 2, 4, 7, 5]
print(merge_sort(d))


출력 결과:
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

📌 병합 정렬의 동작 흐름 요약
리스트를 2개로 계속 쪼갬 → 하나씩 남을 때까지 (재귀)
나눠진 리스트들을 차례대로 병합하면서 정렬
각 병합 단계에서 가장 작은 값부터 차례대로 추가

----------------------------------------------------


일반적인 병합 정렬(인덱스 병합) -  171페이지 예제
def merge_sort(a):
    n = len(a)                 # 1) 현재 리스트의 길이 n

    # 2) 종료 조건: 원소가 0개 또는 1개면 이미 정렬된 상태
    if n <= 1:
        return                 # in-place 버전이므로 그냥 돌아감(리스트 a는 그대로)

    # 3) 중간을 기준으로 두 그룹으로 나누기
    mid = n // 2               # 왼쪽 길이
    g1 = a[:mid]               # 왼쪽 절반 복사
    g2 = a[mid:]               # 오른쪽 절반 복사

    # 4) 두 그룹을 각각 다시 병합 정렬(재귀 호출)
    merge_sort(g1)             # 왼쪽 그룹 정렬
    merge_sort(g2)             # 오른쪽 그룹 정렬

    # 5) 세 개의 인덱스 포인터 준비
    i1 = 0                     # g1에서 읽을 위치
    i2 = 0                     # g2에서 읽을 위치
    ia = 0                     # a(원본)에 다시 써 넣을 위치

    # 6) g1, g2 둘 다 남아 있는 동안, 더 작은 값을 골라 a에 채워 넣기
    while i1 < len(g1) and i2 < len(g2):
        # 안정성 유지: 같을 때는 g1 값을 먼저 넣으면 stable
        if g1[i1] <= g2[i2]:
            a[ia] = g1[i1]     # 더 작은(같거나 작은) 값을 a[ia]에 씀
            i1 += 1            # g1에서 다음 값으로
        else:
            a[ia] = g2[i2]     # g2의 값이 더 작으면 그 값을 씀
            i2 += 1            # g2에서 다음 값으로
        ia += 1                # a에 쓴 위치도 오른쪽으로 한 칸

    # 7) 한쪽이 다 소비되고 남은 나머지 값들을 a에 그대로 복사
    while i1 < len(g1):
        a[ia] = g1[i1]
        i1 += 1
        ia += 1

    while i2 < len(g2):
        a[ia] = g2[i2]
        i2 += 1
        ia += 1


사용 예:
d = [6, 8, 3, 9, 10, 1, 2, 4, 7, 5]
merge_sort(d)
print(d)  # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

🔎 변수 역할 한눈에
g1, g2: 반으로 나눠 복사한 왼쪽/오른쪽 부분 리스트(각각 재귀적으로 먼저 정렬됨)
i1, i2: g1·g2에서 다음에 꺼낼 값의 위치
ia: 병합한 결과를 원본 a에 써 넣을 위치
루프 본체: g1[i1]과 g2[i2]를 비교해 작은 값부터 차례로 a[ia]에 기록


---------------------------------------------------------------


퀵 정렬(간단 설명 버전, 새 리스트로 반환)  - 173페이지 예제

def quick_sort(a):
    n = len(a)                         # 정렬할 리스트 길이
    if n <= 1:                         # 원소가 0개/1개면 이미 정렬 끝
        return a

    # ① 기준값(pivot) 선택: 여기서는 편의상 '마지막 원소'
    pivot = a[-1]

    # ② 기준값보다 작은 값들/큰 값들을 담을 임시 리스트
    g1 = []                            # group1: pivot보다 작은 값들(< pivot)
    g2 = []                            # group2: pivot보다 큰 값들(>= pivot)

    # ③ 마지막(=pivot 자리)은 제외하고 앞의 원소들을 pivot과 비교해 분할
    for i in range(0, n-1):            # 0 ~ n-2까지
        if a[i] < pivot:               # pivot보다 작으면 g1로
            g1.append(a[i])
        else:                          # 크거나 같으면 g2로
            g2.append(a[i])

    # ④ 각 그룹을 재귀적으로 퀵 정렬 → [정렬된 g1] + [pivot] + [정렬된 g2]
    return quick_sort(g1) + [pivot] + quick_sort(g2)


사용 예:

d = [6, 8, 3, 9, 10, 1, 2, 4, 7, 5]
print(quick_sort(d))   # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


@@@ 과정이 보이게(디버그 출력) @@@
pivot, g1/g2가 어떻게 만들어지는지 보고 싶으면:

def quick_sort_debug(a, depth=0):
    indent = "  " * depth
    print(f"{indent}call: {a}")
    if len(a) <= 1:
        print(f"{indent}return: {a}")
        return a

    pivot = a[-1]
    g1, g2 = [], []
    for i in range(0, len(a)-1):
        print(f"{indent}compare {a[i]} vs pivot {pivot}")
        if a[i] < pivot:
            g1.append(a[i]); print(f"{indent} -> g1: {g1}")
        else:
            g2.append(a[i]); print(f"{indent} -> g2: {g2}")

    print(f"{indent}split => g1:{g1}, pivot:{pivot}, g2:{g2}")
    left  = quick_sort_debug(g1, depth+1)
    right = quick_sort_debug(g2, depth+1)
    res = left + [pivot] + right
    print(f"{indent}merge => {res}")
    return res

-------------------------------------------------------

퀵 정렬 (제자리 in-place 방식)
# 리스트 a의 start부터 end까지를 정렬하는 함수
def quick_sort_sub(a, start, end):
    if end - start <= 0:               # 종료 조건: 정렬 대상이 0개 또는 1개면 그대로 종료
        return

    # ① 기준값(pivot)을 정함: 편의상 가장 오른쪽 값
    pivot = a[end]
    i = start                          # i는 pivot보다 작은 값들이 채워질 자리

    # ② pivot보다 작거나 같은 값을 왼쪽으로 모으기
    for j in range(start, end):       # 마지막은 제외 (pivot 자리니까)
        if a[j] <= pivot:             # pivot보다 작거나 같으면
            a[i], a[j] = a[j], a[i]   # 현재 위치 j와 작은 값들 영역 끝 i를 교환
            i += 1                    # 작은 값들 끝 위치를 한 칸 뒤로 이동

    # ③ pivot을 자기 자리(i)로 이동 (i보다 오른쪽은 모두 큰 값들)
    a[i], a[end] = a[end], a[i]

    # ④ 재귀 호출: pivot 기준으로 좌우 부분을 각각 다시 퀵 정렬
    quick_sort_sub(a, start, i - 1)   # pivot보다 작거나 같은 값들 정렬
    quick_sort_sub(a, i + 1, end)     # pivot보다 큰 값들 정렬

# 전체 리스트를 정렬하기 위한 wrapper 함수
def quick_sort(a):
    quick_sort_sub(a, 0, len(a) - 1)  # 전체 리스트(0 ~ len-1)를 정렬

🔍 사용 예제
d = [6, 8, 3, 9, 10, 1, 2, 4, 7, 5]
quick_sort(d)
print(d)  # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


@@@ 핵심 아이디어 정리 @@@@
   단계	           설명
1. pivot 선택	마지막 원소를 기준값으로 정함
2. 분할(partition)	pivot보다 작거나 같은 값을 왼쪽으로, 큰 값을 오른쪽으로 이동
3. 위치 교환	pivot을 '중간에 위치한 자기 자리(i)'로 옮김
4. 재귀 호출	좌측 그룹과 우측 그룹을 각각 퀵 정렬함


