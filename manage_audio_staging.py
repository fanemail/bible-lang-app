# -*- coding: utf-8 -*-
"""
音頻分階段部署管理腳本。

背景：GitHub空間有限（目前抓1GB預算），11卷全部真人語音約2GB，
沒辦法一次全部上傳，需要「先上傳做完的書卷、其他書卷之後對齊完再補上傳」。
但git是照資料夾實際存在的檔案決定要不要追蹤，沒辦法「檔案留著但不上傳」，
所以做法是：暫時把還不上傳的書卷音頻+時間戳資料夾，搬到這個repo資料夾以外的
地方（不影響git，因為git看不到repo以外的東西），之後要上傳該書卷時再搬回來。

★重要：時間戳資料夾(bible_data/timestamps/)也要跟著音頻一起搬，因為
build_chunk_audio.py / build_verse_audio.py是依「時間戳資料夾裡有哪些書卷」
來決定chunk_audio.js / verse_audio.js要包含哪些書卷的資料——如果只搬走音頻、
留著時間戳，查表檔還是會產生「指向不存在音頻檔案」的資料，前端會跳出
「音頻播放失敗」的錯誤彈窗，而不是預期的優雅退回TTS。兩者必須同進退。

用法（不需要whisperx_env，一般Python環境即可）：

  1. 編輯下面的 INCLUDE_BOOKS，填入這次要上傳真人語音的書卷代碼
     （例如 ["PSA"] 表示只有詩篇要上傳，其餘書卷音頻/時間戳都搬出去暫存）

  2. 執行搬出：
     python manage_audio_staging.py stage

  3. 搬完後，重新執行這兩支腳本，讓查表檔只包含INCLUDE_BOOKS範圍內的資料：
     python build_chunk_audio.py
     python build_verse_audio.py

  4. 之後想加回某卷（例如箴言對齊做完了），先執行還原：
     python manage_audio_staging.py restore
     再把 INCLUDE_BOOKS 改成 ["PSA", "PRO"]，重複步驟2、3。

暫存資料夾位置：跟本專案同一層的 bible-lang-app-audio-staging/
（在 E:\\bible-lang-app 的上一層，也就是 E:\\bible-lang-app-audio-staging，
故意放在repo資料夾以外，這樣git完全看不到，不會不小心又被加進commit）。
"""
import os, sys, shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "bible_data", "audio")
TIMESTAMPS_DIR = os.path.join(BASE_DIR, "bible_data", "timestamps")
STAGING_DIR = os.path.join(os.path.dirname(BASE_DIR), "bible-lang-app-audio-staging")

# ★這次要上傳真人語音的書卷代碼清單，之後要調整就改這裡
INCLUDE_BOOKS = ["PSA"]

LANGS = ["en", "ja"]


def stage():
    """把INCLUDE_BOOKS以外的書卷，音頻+時間戳資料夾搬到repo外面的暫存資料夾。"""
    os.makedirs(STAGING_DIR, exist_ok=True)
    moved = []
    skipped_already_staged = []

    for base_dir, subdir_name in [(AUDIO_DIR, "audio"), (TIMESTAMPS_DIR, "timestamps")]:
        if not os.path.isdir(base_dir):
            continue
        for lang in LANGS:
            lang_dir = os.path.join(base_dir, lang)
            if not os.path.isdir(lang_dir):
                continue
            for book in sorted(os.listdir(lang_dir)):
                book_path = os.path.join(lang_dir, book)
                if not os.path.isdir(book_path):
                    continue
                if book in INCLUDE_BOOKS:
                    continue  # 這卷要上傳，留在原地不動
                dest = os.path.join(STAGING_DIR, subdir_name, lang, book)
                if os.path.exists(dest):
                    skipped_already_staged.append(f"{subdir_name}/{lang}/{book}")
                    continue
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(book_path, dest)
                moved.append(f"{subdir_name}/{lang}/{book}")

    print(f"已搬出 {len(moved)} 個資料夾到 {STAGING_DIR}：")
    for m in moved:
        print(f"  {m}")
    if skipped_already_staged:
        print(f"\n{len(skipped_already_staged)} 個資料夾在暫存區已存在（可能之前搬過還沒還原），本次跳過未搬動：")
        for s in skipped_already_staged:
            print(f"  {s}")
    print(f"\n目前保留在repo裡、會被git追蹤的書卷：{INCLUDE_BOOKS}")
    print("下一步：重新執行 build_chunk_audio.py 和 build_verse_audio.py，")
    print("讓查表檔只包含這次實際會上傳的書卷，避免查表檔指向不存在的音頻檔案。")


def restore():
    """把暫存資料夾裡的所有內容，全部搬回bible_data原本的位置。"""
    if not os.path.isdir(STAGING_DIR):
        print(f"暫存資料夾 {STAGING_DIR} 不存在，沒有東西可以還原。")
        return

    restored = []
    for subdir_name, base_dir in [("audio", AUDIO_DIR), ("timestamps", TIMESTAMPS_DIR)]:
        staging_subdir = os.path.join(STAGING_DIR, subdir_name)
        if not os.path.isdir(staging_subdir):
            continue
        for lang in os.listdir(staging_subdir):
            lang_staging_dir = os.path.join(staging_subdir, lang)
            if not os.path.isdir(lang_staging_dir):
                continue
            for book in os.listdir(lang_staging_dir):
                src = os.path.join(lang_staging_dir, book)
                dest = os.path.join(base_dir, lang, book)
                if os.path.exists(dest):
                    print(f"  !! {subdir_name}/{lang}/{book} 目的地已存在，跳過（可能不需要還原這個）")
                    continue
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(src, dest)
                restored.append(f"{subdir_name}/{lang}/{book}")

    print(f"已還原 {len(restored)} 個資料夾回 bible_data：")
    for r in restored:
        print(f"  {r}")
    print("\n接下來可以編輯本檔案裡的 INCLUDE_BOOKS 清單，加入新的書卷代碼，")
    print("再執行一次 `python manage_audio_staging.py stage` 重新分階段。")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("stage", "restore"):
        print("用法：python manage_audio_staging.py stage   （搬出INCLUDE_BOOKS以外的書卷）")
        print("      python manage_audio_staging.py restore （全部搬回來，方便重新調整清單）")
        return
    if sys.argv[1] == "stage":
        stage()
    else:
        restore()


if __name__ == "__main__":
    main()
