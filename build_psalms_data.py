# -*- coding: utf-8 -*-
"""
把 psalms_full_output.json 轉成 psalms_data.js（給 index.html 用 <script src> 載入）。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe build_psalms_data.py
"""
import json

INPUT_PATH = r"E:\bible-lang-app\bible_data\psalms_full_output.json"
OUTPUT_PATH = r"E:\bible-lang-app\psalms_data.js"

def main():
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    total_verses = sum(len(c["verses"]) for c in data["chapters"].values())
    print(f"讀取完成：{len(data['chapters'])} 章，共 {total_verses} 節")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("/* 由 build_psalms_data.py 自 psalms_full_output.json 自動產生，請勿手動編輯 */\n")
        f.write("const PSALMS_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    print(f"已寫出：{OUTPUT_PATH}")

if __name__ == "__main__":
    main()
