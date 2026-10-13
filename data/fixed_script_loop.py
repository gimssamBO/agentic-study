# -*- coding: utf-8 -*-
"""sales_report.py — 일자별 매출 CSV에서 평균/최대 매출일을 구한다. (버그 포함)"""
import csv

def load_sales(path):
    rows = []
    with open(path, encoding='utf-8') as f:            # 한글 csv 인코딩 수정
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

def average_sales(rows):
    total = 0
    for r in rows:
        total += int(r["sales"])          # 문자열 + 정수 버그 수정
    return total / len(rows)

def best_day(rows):
    best = rows[0]
    for r in rows:
        if int(r["sales"]) > int(best["sales"]):   # 문자열 비교 버그 수정
            best = r
    return best

if __name__ == "__main__":
    data = load_sales("data/sales_daily.csv")
    print("평균 매출:", average_sales(data))
    print("최대 매출일:", best_day(data)["date"])