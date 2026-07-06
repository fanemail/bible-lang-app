# -*- coding: utf-8 -*-
"""
把 bad_vocab_ids_deepl.txt 裡的污染詞條，對照 proper_nouns.json（人名地名清單），
分成「合理的人名/地名（不算真正問題）」跟「真正翻譯失敗的普通詞（需要處理）」兩組。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe crosscheck_proper_nouns.py
"""
import json

VOCAB_PATH = r"E:\bible-lang-app\bible_data\vocab_db_deepl.jsonl"
BAD_IDS_PATH = r"E:\bible-lang-app\bible_data\bad_vocab_ids_deepl.txt"
PROPER_NOUNS_PATH = r"E:\bible-lang-app\bible_data\proper_nouns.json"
REAL_ISSUES_OUTPUT = r"E:\bible-lang-app\bible_data\real_translation_issues.txt"

def load_proper_nouns():
    with open(PROPER_NOUNS_PATH, encoding='utf-8') as f:
        data = json.load(f)
    # 兼容不同可能的結構：list of str，或 list of dict帶某個詞欄位，或 dict
    words = set()
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                words.add(item.lower())
            elif isinstance(item, dict):
                for key in ('en', 'word', 'name'):
                    if key in item and item[key]:
                        words.add(str(item[key]).lower())
                        break
    elif isinstance(data, dict):
        words = set(k.lower() for k in data.keys())
    return words

def main():
    try:
        proper_nouns = load_proper_nouns()
        print(f"人名地名清單載入：{len(proper_nouns)} 條")
    except Exception as e:
        print(f"讀取 proper_nouns.json 失敗：{e}")
        print("將視為沒有人名清單可比對，全部列為待確認。")
        proper_nouns = set()

    with open(BAD_IDS_PATH, encoding='utf-8') as f:
        bad_ids = set(line.strip() for line in f if line.strip())

    entries_by_id = {}
    with open(VOCAB_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                item = json.loads(line)
                if item['id'] in bad_ids:
                    entries_by_id[item['id']] = item

    is_name = []
    real_issue = []
    for id_, item in entries_by_id.items():
        en = (item.get('en') or '').lower()
        if en in proper_nouns:
            is_name.append(item)
        else:
            real_issue.append(item)

    print(f"\n污染清單總數：{len(entries_by_id)}")
    print(f"其中屬於人名/地名（合理不翻譯）：{len(is_name)}")
    print(f"真正需要處理的翻譯失敗：{len(real_issue)}\n")

    print("真正翻譯失敗的詞（前30條預覽）：")
    for item in real_issue[:30]:
        print(f"  {item['id']} / {item['en']} → {item['ja']!r}")

    with open(REAL_ISSUES_OUTPUT, 'w', encoding='utf-8') as f:
        for item in real_issue:
            f.write(item['id'] + "\t" + item['en'] + "\t" + str(item['ja']) + "\n")
    print(f"\n完整清單已寫出：{REAL_ISSUES_OUTPUT}")

if __name__ == "__main__":
    main()
