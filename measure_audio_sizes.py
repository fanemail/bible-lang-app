# -*- coding: utf-8 -*-
"""
音頻資料夾大小量測腳本。

用途：列出 bible_data/audio/{en,ja}/{書卷}/ 每個資料夾的實際大小，
由大到小排序，方便決定1GB預算內，優先放哪些書卷、哪個語言。

用法（不需要whisperx_env，一般Python環境即可）：
  python measure_audio_sizes.py
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "bible_data", "audio")


def folder_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def main():
    if not os.path.isdir(AUDIO_DIR):
        print(f"!! 找不到 {AUDIO_DIR}")
        return

    results = []
    grand_total = 0
    for lang in sorted(os.listdir(AUDIO_DIR)):
        lang_dir = os.path.join(AUDIO_DIR, lang)
        if not os.path.isdir(lang_dir):
            continue
        for book in sorted(os.listdir(lang_dir)):
            book_dir = os.path.join(lang_dir, book)
            if not os.path.isdir(book_dir):
                continue
            size = folder_size(book_dir)
            results.append((lang, book, size))
            grand_total += size

    results.sort(key=lambda x: -x[2])

    print(f"{'語言':<6}{'書卷':<8}{'大小(MB)':>12}")
    print("-" * 30)
    for lang, book, size in results:
        print(f"{lang:<6}{book:<8}{size/1024/1024:>10.1f} MB")

    print("-" * 30)
    print(f"總計：{grand_total/1024/1024:.1f} MB（約 {grand_total/1024/1024/1024:.2f} GB）")


if __name__ == "__main__":
    main()
