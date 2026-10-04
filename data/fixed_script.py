# -*- coding: utf-8 -*-
"""sales_report.py — 일자별 매출 CSV에서 평균/최대 매출일을 구한다. (버그 수정 완료)"""
import csv

def load_sales(path):
    rows = []
    with open(path, encoding='utf-8') as f:  # 한글 csv 인코딩 지정
        reader = csv.DictReader(f)
        for r in reader:
            r["sales"] = int(r["sales"])  # 문자열을 정수로 변환
            rows.append(r)
    return rows

def average_sales(rows):
    total = 0
    for r in rows:
        total += r["sales"]  # 정수끼리 더하기
    return total / len(rows)

def best_day(rows):
    best = rows[0]
    for r in rows:
        if r["sales"] > best["sales"]:  # 정수 비교
            best = r
    return best

if __name__ == "__main__":
    data = load_sales("data/sales_daily.csv")
    print("평균 매출:", average_sales(data))
    print("최대 매출일:", best_day(data)["date"])