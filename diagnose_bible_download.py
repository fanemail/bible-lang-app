# -*- coding: utf-8 -*-
"""
逐卷檢查 bible_text/{代碼}.json 實際抓到幾章，跟預期章數比對，
抓出「沒報錯，但內容其實缺漏」的書卷（例如書卷代碼兜不上，第1章就404，
程式判定為「這卷只有0章」而正常結束，不會被算成失敗）。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe diagnose_bible_download.py
"""
import os
import json

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
BIBLE_TEXT_DIR = os.path.join(WORK_DIR, "bible_text")

BOOKS = [
    ("創世記","GEN","gen",50), ("出埃及記","EXO","exod",40), ("利未記","LEV","lev",27),
    ("民數記","NUM","num",36), ("申命記","DEU","deut",34), ("約書亞記","JOS","josh",24),
    ("士師記","JDG","judg",21), ("路得記","RUT","ruth",4), ("撒母耳記上","1SA","1sam",31),
    ("撒母耳記下","2SA","2sam",24), ("列王紀上","1KI","1kgs",22), ("列王紀下","2KI","2kgs",25),
    ("歷代志上","1CH","1chr",29), ("歷代志下","2CH","2chr",36), ("以斯拉記","EZR","ezra",10),
    ("尼希米記","NEH","neh",13), ("以斯帖記","EST","esth",10), ("約伯記","JOB","job",42),
    ("詩篇","PSA","ps",150), ("箴言","PRO","prov",31), ("傳道書","ECC","eccl",12),
    ("雅歌","SNG","song",8), ("以賽亞書","ISA","isa",66), ("耶利米書","JER","jer",52),
    ("耶利米哀歌","LAM","lam",5), ("以西結書","EZK","ezek",48), ("但以理書","DAN","dan",12),
    ("何西阿書","HOS","hos",14), ("約珥書","JOL","joel",3), ("阿摩司書","AMO","amos",9),
    ("俄巴底亞書","OBA","obad",1), ("約拿書","JON","jonah",4), ("彌迦書","MIC","mic",7),
    ("那鴻書","NAM","nah",3), ("哈巴谷書","HAB","hab",3), ("西番雅書","ZEP","zeph",3),
    ("哈該書","HAG","hag",2), ("撒迦利亞書","ZEC","zech",14), ("瑪拉基書","MAL","mal",4),
    ("馬太福音","MAT","matt",28), ("馬可福音","MRK","mark",16), ("路加福音","LUK","luke",24),
    ("約翰福音","JHN","john",21), ("使徒行傳","ACT","acts",28), ("羅馬書","ROM","rom",16),
    ("哥林多前書","1CO","1cor",16), ("哥林多後書","2CO","2cor",13), ("加拉太書","GAL","gal",6),
    ("以弗所書","EPH","eph",6), ("腓立比書","PHP","phil",4), ("歌羅西書","COL","col",4),
    ("帖撒羅尼迦前書","1TH","1thess",5), ("帖撒羅尼迦後書","2TH","2thess",3),
    ("提摩太前書","1TI","1tim",6), ("提摩太後書","2TI","2tim",4), ("提多書","TIT","titus",3),
    ("腓利門書","PHM","phlm",1), ("希伯來書","HEB","heb",13), ("雅各書","JAS","jas",5),
    ("彼得前書","1PE","1pet",5), ("彼得後書","2PE","2pet",3), ("約翰一書","1JN","1john",5),
    ("約翰二書","2JN","2john",1), ("約翰三書","3JN","3john",1), ("猶大書","JUD","jude",1),
    ("啟示錄","REV","rev",22),
]

def main():
    problems = []
    ok_count = 0
    total_verses_all = 0

    for zh_name, en_code, ja_code, expected_ch in BOOKS:
        filepath = os.path.join(BIBLE_TEXT_DIR, f"{en_code}.json")
        if not os.path.exists(filepath):
            problems.append((en_code, zh_name, "檔案不存在", 0, expected_ch))
            continue

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        actual_ch = len(data["chapters"])
        total_verses = sum(len(c["verses"]) for c in data["chapters"].values())
        total_verses_all += total_verses

        empty_en = empty_zh = empty_ja = 0
        for ch_obj in data["chapters"].values():
            for v in ch_obj["verses"].values():
                if not v.get("en"): empty_en += 1
                if not v.get("zh"): empty_zh += 1
                if not v.get("ja"): empty_ja += 1

        if actual_ch < expected_ch * 0.5:
            problems.append((en_code, zh_name, f"章數過少：實際{actual_ch}章，預期約{expected_ch}章", actual_ch, expected_ch))
        elif total_verses > 0 and (empty_en > total_verses * 0.3 or empty_zh > total_verses * 0.3 or empty_ja > total_verses * 0.3):
            problems.append((en_code, zh_name, f"大量欄位空白：en缺{empty_en}/zh缺{empty_zh}/ja缺{empty_ja}（共{total_verses}節）", actual_ch, expected_ch))
        else:
            ok_count += 1

    print(f"正常的書卷：{ok_count}/{len(BOOKS)}")
    print(f"全部書卷加總節數：{total_verses_all}\n")

    if problems:
        print(f"發現 {len(problems)} 卷有問題：")
        for code, name, issue, actual, expected in problems:
            print(f"  [{code}] {name}：{issue}")
    else:
        print("沒有發現異常，所有書卷章節數量都在合理範圍內。")

if __name__ == "__main__":
    main()
