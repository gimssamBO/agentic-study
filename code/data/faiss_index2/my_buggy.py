# data/my_buggy.py (의도적 버그 2개)
nums = [10, 20, 30, 0]
total = sum(nums)
count = nums.count(0)                  # 0의 개수 = 1
avg_of_zeros = total / count           # 버그1? count가 0이면 zerodivisionerror
# 일부러 0으로 나누기 유발
empty = []
print("평균:", sum(empty) / len(empty))   # 버그1: zerodivisionerror (len=0)
print("세 번째:", nums[5])                # 버그2: indexerror (인덱스 5는 범위 밖)