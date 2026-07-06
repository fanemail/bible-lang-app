# -*- coding: utf-8 -*-
"""
直接檢查幾個知名聖經人名是否存在於 proper_nouns.json 裡，
確認上次交叉比對「0條相符」是清單本身缺漏，還是程式邏輯有bug。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe check_specific_names.py
"""
import json

PATH = r"E:\bible-lang-app\bible_data\proper_nouns.json"

# 挑幾個知名度很高、幾乎不可能被漏收的人名，加上前次結果裡的幾個生僻名字對照
CHECK_WORDS = ["amos", "asa", "abner", "abdon", "abishai", "ahikam", "aaron", "moses"]

def main():
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    print(f"清單總長度：{len(data)}")
    print(f"型態：{type(data).__name__}，元素型態：{type(data[0]).__name__ if data else '空'}\n")

    lower_set = set(str(x).lower() for x in data)

    for w in CHECK_WORDS:
        found_exact = w in data
        found_lower = w.lower() in lower_set
        print(f"  {w:12s} 原始比對={found_exact}  轉小寫比對={found_lower}")

if __name__ == "__main__":
    main()
