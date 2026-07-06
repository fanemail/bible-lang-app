# -*- coding: utf-8 -*-
"""
用跟 step1_extract_vocab.py 完全相同的nltk詞形還原邏輯，
處理一次全本聖經(bible_text/*.json)的英文詞，還原成詞根，
才能跟 vocab_db.jsonl 的7042詞根做真正對等（蘋果比蘋果）的覆蓋率比較。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe check_vocab_coverage_v2.py
"""
import os
import re
import json
import glob

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
VOCAB_PATH = os.path.join(WORK_DIR, "vocab_db.jsonl")
BIBLE_TEXT_DIR = os.path.join(WORK_DIR, "bible_text")
OUTPUT_PATH = os.path.join(WORK_DIR, "vocab_coverage_missing_v2.txt")

try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import wordnet

    def _ensure_nltk_data(pkg_id, download_name):
        try:
            nltk.data.find(pkg_id)
        except LookupError:
            print(f"首次使用，正在下載nltk資源：{download_name} ...")
            nltk.download(download_name)

    _ensure_nltk_data('corpora/wordnet', 'wordnet')
    _ensure_nltk_data('corpora/omw-1.4', 'omw-1.4')
    try:
        _ensure_nltk_data('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng')
    except Exception:
        pass
    try:
        _ensure_nltk_data('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger')
    except Exception:
        pass

    _lemmatizer = WordNetLemmatizer()

    def _wordnet_pos(treebank_tag):
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        return wordnet.NOUN

    def lemmatize_tokens(tokens):
        tagged = nltk.pos_tag(tokens)
        result = []
        for w, tag in tagged:
            lemma = _lemmatizer.lemmatize(w.lower(), pos=_wordnet_pos(tag))
            result.append((w, tag, lemma))
        return result

    print("已使用nltk（含詞性標註）做詞形還原，跟 step1 完全一致的方法。")
    USE_NLTK = True
except ImportError:
    print("未安裝nltk！這次比對沒辦法跟 step1 用同一套方法，結果會不準確。")
    print("請先執行：pip install nltk")
    USE_NLTK = False


def main():
    if not USE_NLTK:
        return

    vocab_words = set()
    with open(VOCAB_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                item = json.loads(line)
                vocab_words.add(item["en"].lower())
    print(f"現有字典詞根數：{len(vocab_words)}")

    files = glob.glob(os.path.join(BIBLE_TEXT_DIR, "*.json"))
    print(f"讀取到 {len(files)} 卷聖經文字檔案，開始詞形還原（可能需要幾分鐘）...")

    bible_lemmas = set()
    proper_nouns_found = set()
    for fi, filepath in enumerate(files, 1):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        for ch_obj in data["chapters"].values():
            for v in ch_obj["verses"].values():
                en_text = v.get("en", "")
                tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", en_text)
                if not tokens:
                    continue
                for word, tag, lemma in lemmatize_tokens(tokens):
                    if tag.startswith("NNP"):
                        proper_nouns_found.add(word.lower())
                    elif len(lemma) >= 2:
                        bible_lemmas.add(lemma)
        if fi % 10 == 0:
            print(f"  進度：{fi}/{len(files)} 卷")

    print(f"\n全本聖經詞根數（已排除人名地名）：{len(bible_lemmas)}")
    print(f"（識別出的人名地名：{len(proper_nouns_found)}，不計入缺字清單）")

    missing = bible_lemmas - vocab_words
    covered = bible_lemmas & vocab_words

    print(f"\n已被字典涵蓋：{len(covered)} 個")
    print(f"字典裡真正缺少的詞根：{len(missing)} 個")
    print(f"真實覆蓋率：{len(covered)/len(bible_lemmas)*100:.1f}%")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for w in sorted(missing):
            f.write(w + "\n")
    print(f"\n真正缺少的詞根清單已寫出：{OUTPUT_PATH}")
    print("這份清單才是準確的，可以直接拿去查詢補進字典。")


if __name__ == "__main__":
    main()
