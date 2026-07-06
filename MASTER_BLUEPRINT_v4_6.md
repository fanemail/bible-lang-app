# 聖經多語言學習App — 主控技術藍圖

> **這份文件的作用**：任何時候、任何新窗口，只要上傳這一份，就能完整重建目前的技術狀態，
> 不需要翻對話記錄、不需要重新討論已經定案的設計。這是單一事實來源（Single Source of Truth）。
>
> **更新規則**：每完成一個任務、或每次結束窗口，都要回來更新這份文件對應的章節。
>
> **v4.6 重大變更提要（★交接窗口必讀）**：
> 1. **D6正式完成**：新增`build_book_text_data.py`轉換腳本，把`bible_data/bible_text/{代碼}.json`（A1既有下載）
>    批次轉成`{代碼}_data.js`（10卷、共8502節），`index.html`新增對應`<script>`標籤+`BOOK_TEXT_SOURCES`10筆資料源，
>    使用者實測11卷經文文字皆正常顯示。至此D6（架構+經文本體）全部完工，這是v4.1以來持續掛著的最後一個
>    「唯一還擋著」項目，現在解除。
> 2. **★提醒（非bug）**：這10卷經文顯示正常，但真人語音喇叭圖示仍是🔊而非🎧——這是預期行為，因為
>    C2（WhisperX對齊）目前只做過詩篇（英文+日文），這10卷還沒對齊，查無資料時自動退回TTS，不影響文字顯示。
>    下一步是C2擴展到箴言(PRO)，逐卷累積真人語音，見七、新窗口使用指南。
>
> **v4.5 重大變更提要（存檔）**：
> 1. **D1日文擴展全部完成**：詩篇日文150章WhisperX對齊已跑完（成功147+沿用3章舊測試檔=150章齊全），
>    人工抽查（119篇最長/117篇最短/23篇基準）確認開頭卡位、結尾乾淨皆正常。
>    `build_chunk_audio.py`重跑後日文語塊**397/397全部配對成功（100%）**，比英文那次（457條中1條殘留問題）還乾淨。
> 2. **★重要修正：v4.4提要對「架構已就緒」的描述不準確，本輪窗口才是真正把日文接上**。
>    v4.4宣稱「`build_chunk_audio.py`、`build_verse_audio.py`、`index.html`三個檔案都已經改成同時支援英文+日文，
>    不需要再修改」，但實際檢查程式碼後發現**三個檔案當時都只支援英文，日文從未被真正實作**，具體是：
>    - `build_chunk_audio.py`：完全沒有日文比對邏輯，本輪窗口新增（日文逐字比對，跟英文逐詞比對是不同演算法，
>      因為日文語塊本身無空白分隔、時間戳也是逐字元顆粒度）
>    - `build_verse_audio.py`：只掃描`timestamps/en/`，本輪窗口改成同時掃`en`+`ja`，
>      **同時修正一個潛在資料覆蓋bug**：key格式從`書卷-章-節`改成`書卷-語言-章-節`，
>      否則中英日key會撞在一起、後處理的語言覆蓋先處理的
>    - `index.html`：`chunkAudioPath()`音頻路徑寫死`audio/en/`資料夾、`getVerseAudioInfo()`key格式跟腳本輸出對不上、
>      兩處喇叭圖示判斷邏輯寫死`=== 'en'`——這4個地方本輪窗口已修正，`chunk_audio.js`/`verse_audio.js`每筆資料
>      現在都帶`lang`欄位供前端動態判斷資料夾/key
>    **教訓**：之後窗口交接時，「架構已就緒不需修改」這類敘述除非有實際測試驗證過（不是只看程式碼「看起來」通用），
>    否則應避免寫成肯定語氣，以免下個窗口誤判不需檢查而漏掉真正的bug。
> 3. **已知殘留小問題（不緊急，見六#7）**：日文整節音頻（`verse_audio.js`）有150章中10個章節、共9節（佔2461節的0.4%）
>    缺少對應時間戳，原因待查（推測是WhisperX對齊該節時遇到音檔或文字比對困難），不影響系統運作
>    （查無資料時前端自動退回TTS朗讀，不會出錯或播放失敗），影響章節清單與缺失節號見六#7。
> 4. **★D1（英文+日文）至此全部完成**，接下來新窗口可以接續D6經文本體串接、或C2擴展到箴言(PRO)，見七、新窗口使用指南。
>
> **v4.4 重大變更提要（存檔）**：
> 1. D1擴展到日文，架構層已全部完成（**此描述經本輪窗口驗證證實不準確，見上方v4.5第2點**），
>    正在等WhisperX日文對齊跑完。新增`batch_align_psa_ja.py`（日文版對齊腳本，逐字比對取代英文的逐詞比對），
>    3章小規模測試已通過（開頭卡位準確，插值未解=0）。
> 2. 新增`run_alignment_queue.py`（夜間排隊自動對齊腳本）：自動掃描哪些「書卷+語言」組合還沒對齊、
>    依序處理、已完成的自動跳過、出錯不中斷整個排隊，未來擴展到其他10卷的英文+日文對齊都可以用這支腳本，
>    不用再手動改路徑常數。
> 3. 本版於D1日文正式完工後由v4.5取代交接內容。
>
> **v4.3 重大變更提要**：
> 1. **D1完成：真人語音正式接入index.html**（不再只是demo頁）。語塊播放（`chunk_audio.js`）跟整節播放（新增`verse_audio.js`+`build_verse_audio.py`）都已串接，喇叭圖示會自動依有沒有真人語音資料切換🎧/🔊，沒有資料時無縫退回原本的TTS，經使用者實測確認可正常播放。
> 2. **整節真人語音比語塊更簡單**：不需要文字比對，WhisperX對齊結果裡每節本來就有現成的startTime/endTime，`build_verse_audio.py`只是單純撈出來重新整理格式，全詩篇150章2461節一次到位。
> 3. **範圍仍僅限英文詩篇**：日文完全沒有做過WhisperX對齊（C2任務從頭到尾只處理英文），日文的朗讀（包含語塊跟整節）目前都還是TTS機器合成，不是真人語音，這點在確認時需要跟未來使用者/新窗口說清楚，避免誤解成日文也做完了。
>
> **v4.2 重大變更提要**：
> 1. **新增`build_chunk_audio.py`（語塊音頻查表腳本）**：把`chunks_data.js`的英文語塊比對WhisperX逐詞時間戳，算出每條語塊的播放起訖時間，輸出`chunk_audio.js`（全域變數`CHUNK_AUDIO`）。這不是新的AI標注，是純文字查表，跑起來幾秒鐘，不需要whisperx_env。
> 2. **詩篇對齊進度127→跑到剩最後9個章節**，目前480條英文語塊裡435條已成功配對時間戳（99.8%去除pending後的成功率），只剩1條（PSA018:2 "take refuge in"，介詞倒裝到動詞前面的特殊語序）需要人工判斷是否要手動特例處理。
> 3. **查表腳本已處理三類文字比對難題**：不連續片語（如"raises up...out of the dust"用`...`標記）、動詞詞形變化（take/takes/taken、call/called）、印刷體彎引號與標點黏字（如"face—even"）。這些技術細節記錄在六#4，供之後處理其他書卷語塊時直接沿用，不用重新踩坑。
>
> **v4.1 重大變更提要**：
> 1. **A3語音下載全部完成**：10卷（PRO/ISA/ECC/GEN/MAT/MRK/LUK/JHN/REV/DAN）英文+日文音頻100%下載完畢，合計1756MB，`download_audio_multi.py`已修好並定案。
> 2. **D6前端三個故障點已修復（架構層）**：書卷選擇器、`chunks_data.js`載入、`highlightChunks()`日文支援全部修好，但**經文本體尚未串接**——除詩篇外，其餘10卷選了會顯示「尚未接入經文資料庫」提示，需要補上傳`bible_text/*.json`才能真正顯示經文（詳見六#1）。
> 3. **D6/A3皆非本版新增，是延續v4.0的未完成項，本版才實際完工/推進**，v4.0提要保留於下方存檔。
>
> **v4.0 重大變更提要**：
> 1. **C任務全面啟動並完成首個完整閉環**：C1/C2/C3全部完成，詩篇23篇逐詞對齊+語塊播放demo驗證成功。C4詩篇150章批次對齊運行中。
> 2. **A3語音下載大幅擴展**：日文10卷(PRO/ISA/ECC/GEN/MAT/MRK/LUK/JHN/REV/DAN)全部下載完畢；英文PRO完成，其餘9卷URL格式待人工核查。
> 3. **C任務技術路線定案**：WhisperX ASR(small模型)+difflib映射策略，解決LORD/Yahweh版本落差，逐詞時間戳格式定案。
> 4. **D6仍是最高優先**，本版沒有變化，仍是阻塞所有成果呈現的核心瓶頸。

---

## 目錄

1. 任務分類體系（A/B/C/D）與現況總表
2. 資料庫Schema定案
3. 檔案目錄總覽
4. 命名規則速查表
5. 依賴關係圖
6. 待解決/待討論事項
7. 新窗口使用指南

---

## 一、任務分類體系與現況總表

專案分四大類任務，命名規則：**A=下載類、B=AI生成類、C=語音處理類、D=功能開發/渲染類**。

| 任務 | 名稱 | 狀態 | 說明 |
|---|---|---|---|
| **A1** | 經文下載（三語逐節） | ✅ **完成，已擴展到全本66卷** | 全本聖經66卷三語文字，見 `bible_text/*.json`。詩篇仍另有舊路徑`psalms_data.js`，待整併（D6時一併處理） |
| **A2** | 詞典建置 | ✅ **完全完成** | 7096詞，英/中/日+假名+拼音齊全，詞根覆蓋率100% |
| **A3** | 語音下載 | ✅ **10卷全部完成** | 詩篇EN+JA✅。PRO/ISA/ECC/GEN/MAT/MRK/LUK/JHN/REV/DAN共10卷，英文+日文共564個檔案、合計1756MB，全部下載完成，0失敗。`download_audio_multi.py`已處理ebible.org三種不同檔名規則（結尾數字/開頭全域編號+拼字數字/底線分隔+拼字數字，詳見六#3存檔記錄） |
| **A4** | 語塊比對庫獲取 | 🔄 **3/6完成** | IS✅250條、JS✅312條、IC✅1506條(81主題)；VS/VC/US待補 |
| **B1** | 英文語塊標注 | 🔄 **11卷完成** | 詩篇(458)、箴言(82)、以賽亞書(23)、傳道書(19)、創世記1-11章(13)、馬太(53)、馬可(6)、路加(16)、約翰(10)、啟示錄(9)、但以理(7)。英文總計696條 |
| **B2** | 日文語塊標注 | 🔄 **11卷完成** | 詩篇(397)、箴言(39)、以賽亞書(1)、傳道書(2)、創世記1-11章(3)、馬太(17)、馬可(2)、路加(3)、約翰(3)、啟示錄(0)、但以理(1)。日文總計468條 |
| **C1** | WhisperX環境可行性測試 | ✅ **完成** | Python 3.12虛擬環境`whisperx_env`，WhisperX 3.8.6+torch 2.8.0+ffmpeg 8.1.1，Windows Boot Camp環境可行 |
| **C2** | 強制對齊（逐詞時間戳） | ✅ **詩篇150章全部完成** | 策略：WhisperX ASR(small模型)轉錄→difflib序列比對映射回正確經文文字，解決LORD/Yahweh版本落差。`batch_align_psa.py`跑完150章，成功150、跳過0、失敗0，耗時7.0小時 |
| **C3** | 對齊結果人工校驗 | ✅ **抽查通過** | 詩篇23篇demo驗證＋後續用`extract_chunk_clips.py`剪片段實際聽過119篇(最長)、23篇(基準)等多條語塊，開頭自然進入、結尾乾淨無截斷，僅1條不連續片語比對(PSA113-01)結尾略蹭到下一句起音，使用者確認可接受 |
| **C4** | 音頻資料整合進index.html | ✅ **完成** | WhisperX詩篇150章對齊全部完成（成功150失敗0）。`build_chunk_audio.py`（語塊查表）+`build_verse_audio.py`（整節查表，新增）都已產出並實測正常，`chunk_audio.js`（457/458條）、`verse_audio.js`（2461節）皆已接入index.html |
| **D1** | 音頻點讀播放 | ✅ **英文+日文皆完成** | 英文（詩篇）語塊+整節播放已正式接入index.html，經使用者實測確認。日文：`batch_align_psa_ja.py`跑完150章對齊、人工抽查通過，`build_chunk_audio.py`（新增日文逐字比對邏輯）+`build_verse_audio.py`（新增lang欄位避免中英日key互撞）+`index.html`（修正4處寫死只認英文的地方：`chunkAudioPath()`路徑、`getVerseAudioInfo()`key格式、2處喇叭圖示判斷）皆已改好並實測。日文語塊397/397配對成功(100%)；日文整節150章2452/2461節有資料（10章共9節缺口，見六#7，不影響運作） |
| **D2** | 密度顏色標記 | ⏸ **資料就緒，前端未串接** | `chapter_density_report.csv`已存在，等D6完全完成後處理 |
| **D3** | 日文語塊高亮渲染 | ✅ **已修復** | `highlightChunks()`改為依`book+lang`篩選語塊比對，日文/中文不再被寫死跳過，已實測驗證（詩篇日文語塊「昼も夜も」可正確高亮） |
| **D4** | 測驗模式擴充 | ⏸ **資料來源已修好，UI待擴充** | `CHUNKS`已改讀真實1164條（原6條demo），測驗模式本身邏輯不變，等經文本體補齊後再驗收 |
| **D5** | UI細節微調 | 隨時可做 | — |
| **D6** | **資料源總體改接** | ✅ **完全完成** | 三個故障點（書卷選擇器/chunks_data.js載入/日文高亮）+經文本體皆已完工。新增`build_book_text_data.py`把`bible_data/bible_text/{代碼}.json`轉成`{代碼}_data.js`，10卷共8502節，`index.html`新增對應script標籤+`BOOK_TEXT_SOURCES`10筆資料源，使用者實測11卷經文文字皆正常顯示 |

---

## 二、資料庫Schema定案

**A1 — 全本聖經（`bible_text/{代碼}.json`，66個檔案）**
```json
{
  "book": "PSA", "book_zh": "詩篇",
  "chapters": { "1": { "verses": { "1": {"en":"...","zh":"...","ja":"..."} } } }
}
```
注意：英文文字使用`engwebp`（LORD版），但英文音頻使用`eng-web`（Yahweh版）。兩者有已知差異（LORD↔Yahweh，冠詞有無），已決定接受此差異，difflib對齊策略可自動處理。

**B1/B2 — `chunks_data.js`（11卷1164條，已存在，但index.html未載入）**
```json
{
  "PSA": { "en": [458條], "ja": [397條] },
  "PRO": { "en": [82條],  "ja": [39條] },
  ...11卷...
}
```

**C — 音頻逐詞時間戳（`bible_data/timestamps/en/PSA/NNN.json`）**
```json
{
  "book": "PSA", "chapter": 23, "audioFile": "023.mp3",
  "verses": [
    {
      "verse": 1, "text": "The LORD is my shepherd...",
      "startTime": 2.139, "endTime": 14.189,
      "words": [
        {"wordIndex": 0, "wordText": "The", "startTime": 2.139, "endTime": 2.5},
        ...
      ]
    }
  ]
}
```

---

## 三、檔案目錄總覽

```
E:\bible-lang-app\
├── index.html                          主程式（D6架構+D1真人語音英文+日文皆已修好；經文本體除詩篇外10卷待補bible_text/*.json）
├── vocab_data.js                       A2產出（已正確串接）
├── psalms_data.js                      A1舊產出（僅詩篇，待淘汰）
├── chunks_data.js                      B產出（11卷1164條，已於D6接上index.html）
├── download_bible_full.py              A1全66卷文字下載
├── download_psalms_audio.py            A3詩篇音頻下載（英文用eng-web/LibriVox，日文用WordProject）
├── download_audio_multi.py             A3擴展10卷音頻下載（已修好定案，處理ebible.org三種檔名規則，10卷564檔0失敗）
├── batch_align_psa.py                  C2詩篇150章批次對齊（已完成，成功150失敗0）
├── build_chunk_audio.py                C4語塊音頻查表腳本（v2：新增日文逐字比對邏輯，跟英文逐詞比對是獨立的兩套演算法；輸出多帶lang欄位）
├── chunk_audio.js                      build_chunk_audio.py產出，全域變數CHUNK_AUDIO，英文457/458條、日文397/397條皆已配對，已接入index.html
├── build_verse_audio.py                C4整節音頻查表腳本（v2：同時掃描en+ja兩個語言資料夾，key格式改為書卷-語言-章-節，避免中英日互相覆蓋）
├── verse_audio.js                      build_verse_audio.py產出，全域變數VERSE_AUDIO，英文150章2461節、日文150章2452節（9節缺口見六#7），已接入index.html
├── check_ja_verse_gap.py               診斷工具（新增）：逐章比對英文/日文時間戳節數差異，找出哪幾章哪幾節對不上，純Python內建模組不需whisperx_env
├── extract_chunk_clips.py              C3人工抽查輔助工具（用ffmpeg把指定語塊剪成小mp3方便雙擊播放核對）
├── batch_align_psa_ja.py               C2日文版對齊腳本（新增，逐字比對，3章測試通過，正在跑全部150章）
├── preview_ja_verses.py                C3日文抽查輔助工具（新增，直接從時間戳json剪整節音頻，不需要先跑verse_audio.js）
├── run_alignment_queue.py              新增：夜間排隊自動對齊腳本，自動掃描哪些書卷+語言尚未對齊、依序處理、已完成自動跳過
├── align_psalm23_v2.py                 C2單章對齊（詩篇23篇demo用）
├── build_demo_psalm23_v3.py            C3 demo網頁組裝（含語塊播放）
├── fix_regex.py / fix2.py              暫時性patch腳本（可刪）
└── bible_data\
    ├── bible_text\{66卷}.json
    ├── timestamps\en\PSA\              C2輸出目錄（生成中）
    ├── PSA_023_en_word_timestamps.json C2詩篇23篇時間戳（demo用）
    ├── audio\en\PSA\001~150.mp3       詩篇英文音頻✅
    ├── audio\en\PRO\001~031.mp3       箴言英文音頻✅
    ├── audio\en\ISA\001~066.mp3       以賽亞書英文✅
    ├── audio\en\ECC\001~012.mp3       傳道書英文✅
    ├── audio\en\GEN\001~050.mp3       創世記英文✅
    ├── audio\en\MAT\001~028.mp3       馬太英文✅
    ├── audio\en\MRK\001~016.mp3       馬可英文✅
    ├── audio\en\LUK\001~024.mp3       路加英文✅
    ├── audio\en\JHN\001~021.mp3       約翰英文✅
    ├── audio\en\REV\001~022.mp3       啟示錄英文✅
    ├── audio\en\DAN\001~012.mp3       但以理英文✅
    ├── audio\ja\PSA\001~150.mp3       詩篇日文音頻✅
    ├── audio\ja\PRO\001~031.mp3       箴言日文音頻✅
    ├── audio\ja\ISA\001~066.mp3       以賽亞書日文✅
    ├── audio\ja\ECC\001~012.mp3       傳道書日文✅
    ├── audio\ja\GEN\001~050.mp3       創世記日文✅
    ├── audio\ja\MAT\001~028.mp3       馬太日文✅
    ├── audio\ja\MRK\001~016.mp3       馬可日文✅
    ├── audio\ja\LUK\001~024.mp3       路加日文✅
    ├── audio\ja\JHN\001~021.mp3       約翰日文✅
    ├── audio\ja\REV\001~022.mp3       啟示錄日文✅
    ├── audio\ja\DAN\001~012.mp3       但以理日文✅
    └── bible_data\audio\en\PSA\demo_psalm23.html  C3 demo網頁
```

---

## 四、命名規則速查表

| 項目 | 格式 | 範例 |
|---|---|---|
| 時間戳輸出 | `timestamps/en/{書卷}/NNN.json` | `timestamps/en/PSA/023.json` |
| 音頻檔案 | `audio/{lang}/{書卷}/NNN.mp3` | `audio/en/PSA/023.mp3` |
| 語塊ID（英） | `CK-EN-{書卷}{章:03d}-{序:02d}` | `CK-EN-PSA001-01` |
| 語塊ID（日） | `CK-JA-{書卷}{章:03d}-{序:02d}` | `CK-JA-GEN003-01` |
| B輸出檔名 | `chunks_{en/ja}_{書卷}_{起:03d}-{末:03d}.json` | `chunks_en_ISA_001-066.json` |
| 書卷代碼 | ebible.org縮寫 | PSA/PRO/ISA/ECC/GEN/MAT/MRK/LUK/JHN/REV/DAN |

---

## 五、依賴關係圖

```
A1(經文，全66卷✅) ──┬──► B1/B2(語塊標注，11卷✅) ──► chunks_data.js(✅已存在，已接上index.html)
                      │                                        │
                      │                                        ▼
                      │                              D6(前端總體改接，架構已修，經文本體待補)
                      │                                        │
                      │                          ┌─────────────┼─────────────┐
                      │                          ▼             ▼             ▼
                      │                      D2(密度)      D3(已修✅)      D4(資料源已修)
                      │
                      └──► A3(10卷英文+日文全部✅，564檔0失敗)
                              │
                              ▼
                      C1✅→C2(英文✅+日文✅詩篇150章)→C3(抽查通過✅英文+日文)→C4(查表腳本✅英文457+日文397語塊，英文2461+日文2452節)→D1(英文+日文皆已接入index.html✅)
```

---

## 六、待解決/待討論事項

### 1.［存檔記錄，已完成】D1日文擴展：對齊、抽查、查表腳本、index.html全部完工

**最終狀態**：詩篇日文150章WhisperX對齊已完成（log顯示成功147+沿用3章更早小規模測試的舊檔案，150章齊全）。
人工抽查119篇（最長）、117篇（最短）、23篇（基準）皆確認開頭卡位準確、結尾乾淨無截斷。

**★重要更正**：v4.4曾宣稱`build_chunk_audio.py`/`build_verse_audio.py`/`index.html`三個檔案「已經改成同時支援中英日，
不需要再修改」，**經本輪窗口實際檢查程式碼後證實這個描述不準確**——三個檔案當時都只有英文邏輯，日文完全沒被實作。
本輪窗口實際完成的修正：

1. **`build_chunk_audio.py`**：新增日文逐字比對邏輯（獨立於英文的逐詞比對，因為日文語塊無空白分隔、
   時間戳也是逐字元顆粒度，不能沿用英文的`.split()`分詞方式），並補上`lang`欄位供前端判斷音頻資料夾。
   重跑結果：日文397/397語塊全部配對成功（100%），英文457條維持不變（含PSA018:2既有殘留問題）。
2. **`build_verse_audio.py`**：新增同時掃描`timestamps/en/`與`timestamps/ja/`，並把輸出key格式從
   `書卷-章-節`改成`書卷-語言-章-節`（原格式會讓中英日資料因key相同而互相覆蓋，是本輪窗口發現並修正的潛在bug）。
   重跑結果：英文2461節、日文2452節（9節缺口見六#7)。
3. **`index.html`**：修正4處寫死只認英文的地方——`chunkAudioPath()`音頻路徑改用`info.lang`動態判斷資料夾、
   `getVerseAudioInfo()`改成4參數對應新key格式、兩處喇叭圖示判斷邏輯（整節播放）拿掉`=== 'en'`限制，
   改成不管哪個語言只要查表查得到就顯示🎧。JS語法已用`node --check`驗證通過。

**驗收**：使用者已重跑兩支查表腳本並確認終端機輸出正確，`index.html`待使用者用瀏覽器實測日文喇叭圖示（🎧）
是否正確顯示、點擊能否正常播放（若尚未回報實測結果，新窗口接手時可請使用者先做這一步確認）。

**教訓（供之後窗口交接參考）**：「架構已就緒、不需修改」這類斷言，除非有實際執行測試驗證過，
否則不應該用肯定語氣寫進藍圖——本次因為只看程式碼片段就寫下這個結論，導致下一輪窗口一開始以為只需要
「等對齊跑完、重跑腳本」，實際上還有三個檔案的核心邏輯需要重寫，多花了好幾輪來回才抓出真正原因。

### 2.［存檔記錄，已完成】D6經文本體串接

架構層三個故障點（書卷選擇器、`chunks_data.js`載入、`highlightChunks()`日文支援）跟經文本體串接**皆已完成並經使用者實測驗證**。

新增`build_book_text_data.py`：把`bible_data/bible_text/{代碼}.json`（A1既有下載，原始結構本身已跟前端需要的格式一致）批次包裝成`{代碼}_data.js`（`const {代碼}_DATA = {...};`），10卷共8502節（PRO 915、ISA 1291、ECC 222、GEN 1533、MAT 1071、MRK 678、LUK 1151、JHN 879、REV 405、DAN 357）。`index.html`同步新增10個`<script src="...">`標籤，並在`BOOK_TEXT_SOURCES`補上10筆資料源（皆用`typeof`保險判斷，缺檔案時安全回傳null、不會報錯）。使用者用本機HTTP伺服器打開實測，11卷經文文字皆正常顯示。

**至此D6全部完工**，D2(密度標記)/D4(測驗模式UI擴充)這兩項收尾工作可以開始進行。

**提醒（非bug）**：這10卷目前只有文字，真人語音仍是TTS（🔊），因為C2對齊還沒做到這10卷，見七、新窗口使用指南裡的C2擴展說明。

### 3.［存檔記錄］A3英文音頻9卷曾失敗，已解決

**根本原因**：ebible.org的`eng-web/audio/`目錄底下，不同書卷混用了三種完全不同的檔名規則，不是資料夾名稱錯誤（資料夾名稱本身9卷裡有8卷一開始就是對的，只有啟示錄`66_Revelation`少了個s）：
- **規則一（箴言）**：章節數字直接在檔名結尾，如`...-01.mp3`
- **規則二（以賽亞書/馬太福音等大部分）**：檔名開頭是全站全域編號（跟章節無關），真正章節資訊藏在拼字英文詞裡，如`0699 Isaiah-Chapter Twenty One.mp3`，且拼字詞之間可能用空格、底線、連字號三種方式分隔，偶爾還帶`(1)`這種備註
- **規則三（創世記）**：`01_21_Genesis_Chapter_Twenty_One.mp3`，底線分隔+拼字詞並存

`download_audio_multi.py`已改寫為同時支援這三種規則（含拼字數字轉換函式），10卷英文+日文共564個檔案、1756MB，已於本輪窗口100%下載完成，0失敗。**若之後要擴展下載其餘55卷音頻，這三種規則的解析邏輯可以直接沿用。**

### 4.［存檔記錄］C2詩篇150章批次對齊，已完成
`batch_align_psa.py`在`whisperx_env`環境下運行，耗時7.0小時，150章成功150、跳過0、失敗0。
輸出在`bible_data/timestamps/en/PSA/001.json`至`150.json`。
下一步（若要擴展）：用同腳本改三個路徑常數，對齊PRO(箴言，音頻已齊)。

### 5. C4語塊音頻查表技術備忘

`build_chunk_audio.py`比對`chunks_data.js`的英文語塊跟WhisperX逐詞時間戳時，遇到並解決了三類文字差異：

- **不連續片語**：語塊文字若含`...`（如`"raises up...out of the dust"`），代表這本來就是被其他字打斷的片語動詞，腳本會拆成好幾段依序各自定位，取第一段起點到最後一段訖點。
- **動詞詞形變化**：語塊記錄的是「詞典引用形」（如"take"、"call"），但經文實際用的可能是"takes"/"taken"/"took"、"called"這種變化形。腳本內建一個小範圍的手動詞形對照表（`_LEMMA_MAP`），只收錄實際遇到的幾個動詞，刻意不做廣泛字尾猜測以避免誤判。
- **標點與引號差異**：經文可能用印刷體彎引號（'）而`chunks_data.js`用直引號(')；經文也可能有標點跟下一個詞黏在一起、中間沒空白（如"face—even"）；也可能有連字號複合詞（如"two-edged"）需要當一個詞、不能拆開。腳本統一處理了這三種情況。

**已知殘留限制**：語序被詩體倒裝的情況（例如"in whom I take refuge"，介詞跑到動詞前面）無法用上述規則解決，需人工判斷是否手動加特例。詩篇範圍內僅1條（PSA018:2）屬此情況，決定暫不處理。

**若之後要對其他書卷（PRO等）做同樣的查表**：`build_chunk_audio.py`不需要改任何路徑常數，會自動掃描`bible_data/timestamps/en/`底下所有已有資料夾的書卷，跟`chunks_data.js`裡對應書卷的英文語塊比對，跑一次就會涵蓋所有已對齊的書卷。

### 6.［存檔記錄］D1真人語音正式接入index.html，已完成（英文部分）

**語塊播放**：語塊卡片（點正文黃色高亮語塊跳出的彈窗）新增「🎧 播放真人語音」按鈕（跟原本的TTS按鈕並存，改標籤為「🔊 TTS朗讀（機器合成）」）。只有`CHUNK_AUDIO_SAFE`裡有資料的語塊才會顯示這顆按鈕，其餘語塊維持原樣。

**整節播放**：每節經文旁邊常駐的喇叭按鈕，改為依`VERSE_AUDIO_SAFE`裡有沒有對應資料，動態決定圖示是🎧（真人語音）還是🔊（TTS），使用者不用點下去試就知道差別。

**共用播放器**：兩者共用同一個`<audio id="chunkAudioPlayer">`元素跟一份通用的`playRealAudioSegment(path, start, end, onDone)`函式，避免語塊播放跟整節播放同時疊播。

**整節查表比語塊簡單很多**：`build_verse_audio.py`不需要任何文字比對，因為WhisperX對齊結果裡每節本來就有自己的`startTime`/`endTime`，直接撈出來重新整理格式即可，全詩篇150章2461節一次到位、零誤判風險。

**部署注意事項**：真人語音靠`<audio src="bible_data/audio/en/{書卷}/{檔案}.mp3">`讀取本機相對路徑檔案，若用瀏覽器直接雙擊`index.html`開啟（`file://`協議），部分瀏覽器可能擋掉本機音頻讀取，需要改用本機HTTP伺服器開啟（如`python -m http.server`）。**已由使用者實測確認可正常播放**，暫時沒遇到這個限制。

**範圍提醒**：目前只有英文詩篇有真人語音（語塊+整節皆是）。日文完全沒有做過WhisperX對齊，日文的朗讀（不管語塊還是整節）目前都還是TTS機器合成，不要誤以為日文也做完了。

### 7. 其他（不緊急）
- A4 VS/VC庫待補
- 創世記12-50章B任務未開始
- psalms_data.js舊格式待整併（D6經文本體補齊時一併處理）
- **日文整節音頻10章共9節缺口（優先度最低，最後再處理即可）**：`verse_audio.js`裡日文比英文少9節，
  已用`check_ja_verse_gap.py`（放在專案根目錄，純Python內建模組、不需whisperx_env）逐章比對確認，
  具體缺失章節/節號如下：
  ```
  第47章：日文多出第10節（不應該發生，需檢查，推測某節被誤切成兩節或音檔有重複片段）
  第49章：缺第9節
  第58章：缺第5節
  第63章：缺第6節
  第65章：缺第3節
  第76章：缺第9節
  第89章：缺第51節
  第105章：缺第6節
  第106章：缺第22節
  第132章：缺第4、5節
  ```
  根因未查（推測是WhisperX對齊該節時遇到音檔或文字比對困難，導致該節被跳過），
  不影響系統運作（`getVerseAudioInfo()`查無資料時前端自動退回TTS朗讀，不會出錯或播放失敗），
  這幾節目前顯示🔊而非🎧。若之後要修，思路是查`batch_align_psa_ja.py`對齊邏輯裡
  是否有「某節比對失敗就整節跳過不寫入」的設計，或直接聽這幾節附近的音檔判斷是否為音檔本身異常。

---

## 七、C任務技術架構備忘（本版新增）

**環境**：`whisperx_env`（Python 3.12，E:\bible-lang-app\whisperx_env\）
**啟動方式**：
```
cd E:\bible-lang-app
whisperx_env\Scripts\activate
python batch_align_psa.py
```

**對齊策略**：
1. WhisperX ASR(small模型)轉錄音頻，取得WhisperX自己識別的逐詞時間戳
2. difflib.SequenceMatcher比對WhisperX識別文字與資料庫正確文字
3. equal區段直接映射時間戳；replace區段取首尾時間戳平均分配給資料庫詞
4. 無時間戳的詞用前後鄰居時間戳插值

**已知限制**：
- LORD/Yahweh版本落差：資料庫用LORD，音頻唸Yahweh，difflib自動處理，不影響其他詞
- 單詞點讀品質有限（連讀/協同發音），字典TTS(有道)優於真人切割，已決定單詞用TTS
- 語塊點讀用真人切割（正確做法，連讀本身就是語塊學習目標）

**套用到其他書卷**：修改`batch_align_psa.py`頂部三個常數：
```python
BIBLE_TEXT_PATH = r"E:\bible-lang-app\bible_data\bible_text\PRO.json"
AUDIO_DIR       = r"E:\bible-lang-app\bible_data\audio\en\PRO"
OUTPUT_DIR      = r"E:\bible-lang-app\bible_data\timestamps\en\PRO"
TOTAL_CHAPTERS  = 31
```

---

## 八、新窗口使用指南

**★D1、D6皆已完成，目前最優先建議接續C2箴言(PRO)對齊，逐步累積第二卷真人語音**：

上傳本文件，描述：「D1(英文+日文)、D6(經文本體)都已完成，現在要把batch_align_psa.py的路徑常數改為PRO：
```
BIBLE_TEXT_PATH = r"E:\bible-lang-app\bible_data\bible_text\PRO.json"
AUDIO_DIR       = r"E:\bible-lang-app\bible_data\audio\en\PRO"
OUTPUT_DIR      = r"E:\bible-lang-app\bible_data\timestamps\en\PRO"
TOTAL_CHAPTERS  = 31
```
然後啟動箴言英文批次對齊；跑完後直接執行build_chunk_audio.py和build_verse_audio.py就會自動涵蓋PRO，
不用改這兩支腳本。英文對齊完成、抽查通過後，再比照batch_align_psa_ja.py的模式做箴言日文對齊」

**若想收尾日文9節缺口（優先度最低，見六#7）**：
上傳本文件 + `batch_align_psa_ja.py`，描述：「六#7列的10章9節日文整節音頻缺口要查根因」

**做B1/B2語塊標注（其他書卷）**：
上傳對應任務包 + extract_chapter_text.py產生的章節文字，不需要本文件

**若要擴展下載其餘55卷英文音頻**：
上傳本文件 + `download_audio_multi.py`，描述：「要擴展到其餘55卷，ebible.org的三種檔名規則已在download_audio_multi.py裡處理過，可以沿用同一套邏輯」

---

*文件版本：v4.6*
*更新日期：2026年7月*
*對應專案：聖經多語言學習App*
*本版核心更新：D6正式完成——新增build_book_text_data.py把bible_data/bible_text/{代碼}.json轉成
{代碼}_data.js，index.html新增10個script標籤+BOOK_TEXT_SOURCES資料源，使用者實測11卷經文文字皆正常顯示；
D1、D6至此皆完工；★下一步建議C2擴展到箴言(PRO)，逐卷累積真人語音，見八、新窗口使用指南*
