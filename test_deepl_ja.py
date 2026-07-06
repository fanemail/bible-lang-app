# -*- coding: utf-8 -*-
"""
DeepL 小規模測試：只測15個詞，確認翻譯品質可接受，不寫入任何資料庫檔案。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe test_deepl_ja.py
"""
import requests

API_KEY = "3ea148d0-5067-402a-b6e4-374c72452a4b:fx"
API_URL = "https://api-free.deepl.com/v2/translate"  # 注意：Free版金鑰要用 api-free 這個domain

# 混合挑選：有原本demo裡的常見詞，也有之前發現MyMemory翻錯/翻壞的詞，方便對照品質
TEST_WORDS = [
    "shepherd", "covenant", "counsel", "wicked", "righteous",
    "fruit", "dapple", "clan", "them", "abandon",
    "blessed", "meditate", "congregation", "perish", "wither"
]

def translate_batch(words):
    headers = {"Authorization": f"DeepL-Auth-Key {API_KEY}"}
    data = [("text", w) for w in words] + [("target_lang", "JA"), ("source_lang", "EN")]
    resp = requests.post(API_URL, headers=headers, data=data, timeout=15)
    print(f"HTTP狀態碼：{resp.status_code}")
    resp.raise_for_status()
    result = resp.json()
    return [t["text"] for t in result["translations"]]

def main():
    print(f"測試 {len(TEST_WORDS)} 個詞...\n")
    try:
        translations = translate_batch(TEST_WORDS)
    except Exception as e:
        print(f"請求失敗：{e}")
        return

    for word, ja in zip(TEST_WORDS, translations):
        print(f"  {word:15s} -> {ja}")

    print("\n請檢查以上翻譯是否像正常的日文單詞/短語（不是整句怪異機翻、不是原詞未翻譯）。")

if __name__ == "__main__":
    main()
