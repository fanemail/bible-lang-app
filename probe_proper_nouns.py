# -*- coding: utf-8 -*-
"""
探測 proper_nouns.json 的實際資料結構，印出型態和前5筆內容，
用來確認之前交叉比對腳本抓錯欄位的問題出在哪。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe probe_proper_nouns.py
"""
import json

PATH = r"E:\bible-lang-app\bible_data\proper_nouns.json"

def main():
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    print(f"最外層型態：{type(data).__name__}")

    if isinstance(data, list):
        print(f"列表長度：{len(data)}")
        print("前5筆內容：")
        for item in data[:5]:
            print(f"  型態={type(item).__name__}  內容={item!r}")
    elif isinstance(data, dict):
        keys = list(data.keys())
        print(f"字典鍵值數量：{len(keys)}")
        print(f"前5個key：{keys[:5]}")
        print("對應前5筆內容：")
        for k in keys[:5]:
            print(f"  {k!r} -> {data[k]!r}")
    else:
        print(f"內容：{data!r}"[:500])

if __name__ == "__main__":
    main()
