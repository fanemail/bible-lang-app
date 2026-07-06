# -*- coding: utf-8 -*-
"""
語塊音頻時間戳查表腳本（v2：新增日文支援）。

用途：把chunks_data.js裡的語塊（英文如"valley of the shadow of death"，
日文如"昼も夜も"），對照WhisperX批次對齊產出的逐詞/逐字時間戳
（bible_data/timestamps/{en,ja}/{BOOK}/NNN.json），
算出每個語塊在該章音頻裡的播放起訖時間（第一個詞/字的startTime ~ 最後一個詞/字的endTime）。

這不是另一次AI標注，純粹是文字比對查表，跑起來很快，不需要whisperx_env、不需要GPU。

★v2變更：新增日文比對邏輯。英文是逐詞對齊（時間戳json裡一個word是一個完整英文詞），
日文是逐字對齊（時間戳json裡一個word是一個假名/漢字），兩者顆粒度不同，
所以日文不能沿用英文「用空白.split()分詞」的做法（日文語塊本身沒有空白），
改成把語塊文字拆成單一字符的清單，逐字跟時間戳比對。英文原本的比對邏輯完全沒有改動。

輸入：
  1. chunks_data.js（跟index.html同資料夾）
  2. bible_data/timestamps/en/{BOOK}/*.json（英文WhisperX批次對齊產出）
  3. bible_data/timestamps/ja/{BOOK}/*.json（日文WhisperX批次對齊產出）

輸出：
  chunk_audio.js —— 全域變數 CHUNK_AUDIO，格式：
  {
    "CK-EN-PSA023-02": { "book":"PSA","chapter":23,"verse":4,"audioFile":"023.mp3",
                          "startTime":19.2,"endTime":20.5,"matchedText":"valley of the shadow of death," },
    "CK-JA-PSA023-02": { "book":"PSA","chapter":23,"verse":4,"audioFile":"023.mp3",
                          "startTime":18.9,"endTime":20.1,"matchedText":"死の陰の谷を" }
  }
  只收錄「有對應語言WhisperX對齊資料」的語塊，其他書卷/語言暫時跳過（不算錯誤，之後補上再重跑即可）。
  比對不到的語塊會印出來，人工確認是文字差異還是真的資料有誤。

用法（3.14主環境，不需要whisperx_env）：
  python build_chunk_audio.py
"""
import os, re, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHUNKS_DATA_JS = os.path.join(BASE_DIR, "chunks_data.js")
TIMESTAMPS_BASE_DIR = os.path.join(BASE_DIR, "bible_data", "timestamps")
OUTPUT_JS = os.path.join(BASE_DIR, "chunk_audio.js")

# 依序處理的語言清單。之後若擴展到其他語言（如繁中），只要在這裡加一個字串，
# 並比照下面ja的邏輯多寫一組比對函式即可，不用動主流程。
LANGS = ["en", "ja"]


# ============================================================
# 英文比對邏輯（原封不動，沿用舊版）
# ============================================================

# 動詞詞形對照表：只收錄實際遇到、需要跟語塊「詞典引用形」互相對應的變化，
# 刻意不做廣泛的字尾猜測（例如去掉字尾s/ed），避免把不相關的詞誤判成同一個詞。
_LEMMA_MAP = {
    "take": "take", "takes": "take", "took": "take", "taken": "take", "taking": "take",
    "call": "call", "calls": "call", "called": "call", "calling": "call",
}


def normalize_en(word):
    """去掉單詞頭尾的標點符號（逗號、句號、分號等），把印刷體彎引號（'）統一成直引號(')避免
       跟chunks_data.js裡的直引號比對失敗，轉小寫，並套用小範圍動詞詞形對照表，用來比對。"""
    w = word.replace("\u2019", "'").replace("\u2018", "'")
    w = re.sub(r"^\W+|\W+$", "", w, flags=re.UNICODE).lower()
    return _LEMMA_MAP.get(w, w)


def explode_verse_words_en(verse_words):
    """把逐詞清單展開成(比對用token, 原始詞物件)的配對清單。
       主要處理「標點跟下一個詞黏在一起、中間沒有空白」的情況，例如經文原文
       "face—even"這種用破折號、沒有空白分隔的寫法，會被切成face、even兩個token，
       但兩者仍指回同一個原始詞物件（因為WhisperX只給了這一整串一個時間戳，
       拆出來的子詞只能共用同一個起訖時間，這是可接受的精度取捨）。"""
    exploded = []
    for w in verse_words:
        raw = w["wordText"].replace("\u2019", "'").replace("\u2018", "'")
        # 撇號(')跟連字號(-)都當作「詞內連接符」，例如heart's、two-edged都應該保持一整個詞；
        # 破折號(—，em dash)不在這個字元類別裡，所以face—even這種沒空白的黏字仍會正確拆開。
        pieces = re.findall(r"[^\W_]+(?:['-][^\W_]+)*", raw, flags=re.UNICODE)
        for piece in pieces:
            tok = normalize_en(piece)
            if tok:
                exploded.append((tok, w))
    return exploded


# ============================================================
# 日文比對邏輯（新增）
# ============================================================
# 日文時間戳是逐字元對齊（一個word就是一個假名/漢字，不含標點），語塊文字本身
# 也沒有空白分隔（如"昼も夜も"）。所以不能用英文那套「空白分詞+動詞詞形對照」，
# 改成：把語塊文字跟時間戳word都拆成「單一字符」清單，直接逐字比對即可。
# \w在Python的re模組對unicode字串預設就會把漢字、假名當作單詞字元，標點符號
# （。、「」等）不會被算進去，天然就能達到「過濾標點、只留文字」的效果。

def tokenize_ja(text):
    """把日文文字拆成單一字符的清單，過濾掉標點符號、空白。"""
    return re.findall(r"\w", text, flags=re.UNICODE)


def explode_verse_words_ja(verse_words):
    """日文時間戳裡每個word本身就已經是一個字符，不需要像英文那樣拆解黏字，
       只需濾掉萬一混進來的標點符號（正常情況下時間戳json不會有標點word，這裡是保險）。"""
    exploded = []
    for w in verse_words:
        ch = w["wordText"]
        if re.match(r"^\w$", ch, flags=re.UNICODE):
            exploded.append((ch, w))
    return exploded


# ============================================================
# 共用的比對演算法（跟語言無關，操作的是「token清單」，不管token是英文詞還是日文字）
# ============================================================

def find_contiguous(target_tokens, verse_tokens):
    """嚴格比對：target_tokens必須在verse_tokens裡連續出現。回傳(起點index, 訖點index)或None。"""
    n, m = len(verse_tokens), len(target_tokens)
    for i in range(0, n - m + 1):
        if verse_tokens[i:i + m] == target_tokens:
            return i, i + m - 1
    return None


def find_in_order_with_gaps(target_tokens, verse_tokens):
    """寬鬆比對：target_tokens依序出現在verse_tokens裡即可，中間允許夾雜其他字
       （用來處理"raises up...out of the dust"這種本身就不連續的片語動詞）。
       回傳(起點index, 訖點index)或None，取第一個可行的貪婪比對結果。"""
    pos = 0
    first_idx = None
    last_idx = None
    for tok in target_tokens:
        while pos < len(verse_tokens) and verse_tokens[pos] != tok:
            pos += 1
        if pos >= len(verse_tokens):
            return None
        if first_idx is None:
            first_idx = pos
        last_idx = pos
        pos += 1
    return first_idx, last_idx


def span_from_indices(exploded, i, j, joiner):
    """把exploded清單裡第i到第j個token對應回原始詞/字物件，算出起訖時間跟命中文字。
       joiner=" "用於英文（詞跟詞之間要有空白），joiner=""用於日文（字跟字之間直接相連）。"""
    start_word, end_word = exploded[i][1], exploded[j][1]
    seen = []
    for k in range(i, j + 1):
        w = exploded[k][1]
        if not seen or seen[-1] is not w:
            seen.append(w)
    matched_text = joiner.join(w["wordText"] for w in seen)
    return start_word["startTime"], end_word["endTime"], matched_text


def find_chunk_span_en(chunk_text, verse_words):
    """英文語塊比對，邏輯跟舊版完全一樣。"""
    exploded = explode_verse_words_en(verse_words)
    verse_tokens = [t for t, _ in exploded]

    segments = [s.strip() for s in re.split(r"\.\.\.|…", chunk_text) if s.strip()]
    if len(segments) > 1:
        cursor = 0
        first_idx = last_idx = None
        for seg in segments:
            seg_tokens = [normalize_en(w) for w in seg.split()]
            found = find_contiguous(seg_tokens, verse_tokens[cursor:])
            if not found:
                return None
            s, e = found[0] + cursor, found[1] + cursor
            if first_idx is None:
                first_idx = s
            last_idx = e
            cursor = e + 1
        start, end, matched_text = span_from_indices(exploded, first_idx, last_idx, joiner=" ")
        return start, end, matched_text, "不連續片語比對"

    target_tokens = [normalize_en(w) for w in chunk_text.split()]
    found = find_contiguous(target_tokens, verse_tokens)
    method = "嚴格連續比對"
    if not found:
        found = find_in_order_with_gaps(target_tokens, verse_tokens)
        method = "寬鬆比對(允許中間夾字，建議抽查)"
    if not found:
        return None
    start, end, matched_text = span_from_indices(exploded, *found, joiner=" ")
    return start, end, matched_text, method


def find_chunk_span_ja(chunk_text, verse_words):
    """日文語塊比對：逐字版本，邏輯結構跟英文對應，但token是單一字符、不需要動詞詞形處理。"""
    exploded = explode_verse_words_ja(verse_words)
    verse_tokens = [t for t, _ in exploded]

    segments = [s.strip() for s in re.split(r"\.\.\.|…", chunk_text) if s.strip()]
    if len(segments) > 1:
        cursor = 0
        first_idx = last_idx = None
        for seg in segments:
            seg_tokens = tokenize_ja(seg)
            found = find_contiguous(seg_tokens, verse_tokens[cursor:])
            if not found:
                return None
            s, e = found[0] + cursor, found[1] + cursor
            if first_idx is None:
                first_idx = s
            last_idx = e
            cursor = e + 1
        start, end, matched_text = span_from_indices(exploded, first_idx, last_idx, joiner="")
        return start, end, matched_text, "不連續片語比對(日文)"

    target_tokens = tokenize_ja(chunk_text)
    found = find_contiguous(target_tokens, verse_tokens)
    method = "嚴格連續比對(日文逐字)"
    if not found:
        found = find_in_order_with_gaps(target_tokens, verse_tokens)
        method = "寬鬆比對(日文，允許中間夾字，建議抽查)"
    if not found:
        return None
    start, end, matched_text = span_from_indices(exploded, *found, joiner="")
    return start, end, matched_text, method


def find_chunk_span(chunk_text, verse_words, lang):
    if lang == "ja":
        return find_chunk_span_ja(chunk_text, verse_words)
    return find_chunk_span_en(chunk_text, verse_words)


# ============================================================
# 主流程（跟語言無關，只是多了一層lang參數）
# ============================================================

def load_chunks_data(path):
    """chunks_data.js是 `const CHUNKS_DATA = {...};\nconst CHAPTER_DENSITY = {...};` 這種結構，
       裡面不只一個變數，所以不能整份當JSON解析，要精準只抓CHUNKS_DATA那一段。
       用json.JSONDecoder.raw_decode從第一個大括號開始解析，遇到它自己的結束大括號就停止，
       後面不管接了什麼變數都不影響。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    marker = "CHUNKS_DATA"
    idx = text.index(marker)
    brace_start = text.index("{", idx)
    obj, _ = json.JSONDecoder().raw_decode(text, brace_start)
    return obj


def process_book(book_code, lang, chunk_list, chunk_audio_out, unmatched_out):
    book_ts_dir = os.path.join(TIMESTAMPS_BASE_DIR, lang, book_code)
    if not os.path.isdir(book_ts_dir):
        return  # 這卷這個語言還沒有WhisperX對齊產出，跳過（不算錯誤，之後補上再重跑即可）

    # 依章節分組，一次載入一份時間戳檔案，查完該章所有語塊再換下一章
    by_chapter = {}
    for c in chunk_list:
        by_chapter.setdefault(c["chapter"], []).append(c)

    for chapter, chunk_group in sorted(by_chapter.items()):
        ts_path = os.path.join(book_ts_dir, f"{chapter:03d}.json")
        if not os.path.exists(ts_path):
            for c in chunk_group:
                unmatched_out.append((c["id"], book_code, chapter, "該章尚無時間戳檔案（WhisperX還沒對齊到這章）"))
            continue
        with open(ts_path, encoding="utf-8") as f:
            ts_data = json.load(f)
        audio_file = ts_data.get("audioFile", f"{chapter:03d}.mp3")
        verses_by_num = {v["verse"]: v["words"] for v in ts_data["verses"]}

        for c in chunk_group:
            verse_words = verses_by_num.get(c["verse"])
            result = None
            if verse_words:
                result = find_chunk_span(c["text"], verse_words, lang)
            if result is None:
                # 保險機制：文字可能因版本差異或標點差異落在鄰節，往前後各一節再找一次
                for neighbor in (c["verse"] - 1, c["verse"] + 1):
                    nw = verses_by_num.get(neighbor)
                    if nw:
                        result = find_chunk_span(c["text"], nw, lang)
                        if result:
                            break
            if result:
                start, end, matched_text, method = result
                chunk_audio_out[c["id"]] = {
                    "book": book_code, "lang": lang, "chapter": chapter, "verse": c["verse"],
                    "audioFile": audio_file, "startTime": round(start, 3), "endTime": round(end, 3),
                    "matchedText": matched_text, "matchMethod": method,
                }
            else:
                unmatched_out.append((c["id"], book_code, chapter, f'"{c["text"]}"（第{c["verse"]}節及鄰節都找不到）'))


def main():
    chunks_data = load_chunks_data(CHUNKS_DATA_JS)
    chunk_audio = {}
    unmatched = []

    for book_code, langs in chunks_data.items():
        for lang in LANGS:
            lang_chunks = langs.get(lang, [])
            if lang_chunks:
                process_book(book_code, lang, lang_chunks, chunk_audio, unmatched)

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("// 自動產生檔案，請勿手動編輯 —— 執行 build_chunk_audio.py 重新產生\n")
        f.write("// 語塊音頻時間戳查表（含已對齊書卷的英文+日文語塊）\n\n")
        f.write("const CHUNK_AUDIO = ")
        json.dump(chunk_audio, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    # 未配對的訊息分兩類處理：「章節還沒跑完」是預期中的過渡狀態，只統計數字；
    # 「文字真的比對不上」才是需要人工檢查的異常，逐條列出。
    pending = [u for u in unmatched if "尚無時間戳檔案" in u[3]]
    real_mismatch = [u for u in unmatched if "尚無時間戳檔案" not in u[3]]

    en_count = sum(1 for cid in chunk_audio if cid.startswith("CK-EN-"))
    ja_count = sum(1 for cid in chunk_audio if cid.startswith("CK-JA-"))
    print(f"完成：共{len(chunk_audio)}條語塊成功配對時間戳（英文{en_count}條、日文{ja_count}條），寫入 {OUTPUT_JS}")

    loose = [cid for cid, v in chunk_audio.items() if v["matchMethod"] not in ("嚴格連續比對", "嚴格連續比對(日文逐字)")]
    if loose:
        print(f"  其中{len(loose)}條用了「不連續片語」或「寬鬆比對」，建議挑幾條對照chunk_audio.js裡的matchedText欄位抽查是否合理：")
        for cid in loose[:15]:
            v = chunk_audio[cid]
            print(f"    {cid}（{v['matchMethod']}）：matchedText=\"{v['matchedText']}\"")
        if len(loose) > 15:
            print(f"    ...其餘{len(loose)-15}條省略，完整清單在chunk_audio.js裡搜尋matchMethod欄位")
    if pending:
        pending_chapters = sorted(set((b, c) for _, b, c, _ in pending))
        print(f"\n{len(pending)}條語塊所屬章節還沒有時間戳檔案（WhisperX尚未跑到，屬正常過渡狀態，"
              f"涉及{len(pending_chapters)}個章節，跑完重新執行本腳本即可自動補上）")
    if real_mismatch:
        print(f"\n⚠ {len(real_mismatch)}條語塊在已有時間戳的章節裡，文字真的比對不上，需要人工檢查：")
        for cid, book, chapter, reason in real_mismatch:
            print(f"  [{book} {chapter}] {cid}：{reason}")
    elif not pending:
        print("\n全部語塊都成功配對，沒有需要人工檢查的項目。")


if __name__ == "__main__":
    main()
