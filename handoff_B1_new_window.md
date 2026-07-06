# 開新窗口做B1語塊標注 — 交接文字

## 第一步：在這裡（本機CMD）先產生這次要標注的章節文字

```
C:\Users\freeman\AppData\Local\Programs\Python\Python314\python.exe extract_chapter_text.py 1 10
```
（範例是詩篇1~10章，第一次先抓小範圍測試流程，之後可以逐批擴大範圍）

跑完會產生 `E:\bible-lang-app\bible_data\chunk_task_input_001-010.txt`

---

## 第二步：開新對話窗口，貼上以下文字

```
請按照這份語塊標注任務包，標注附上的這段詩篇經文，找出裡面符合定義的英文語塊
（idiom / phrasal verb / 固定動賓搭配），依照任務包裡的三層判定流程、三條邊界規則、
輸出格式規則來標注，最後輸出成任務包要求的JSON陣列格式，存成
chunks_en_psalms_001-010.json（章節範圍請依你實際處理的範圍調整檔名）。

不確定某個語塊算不算數時，寧可保守不標，不要為了湊數硬標。
```

**然後上傳兩個檔案：**
1. `chunk_annotation_task_kit.md`（v2.0，已包含完整定義、邊界規則、六庫關係）
2. 剛才產生的 `chunk_task_input_001-010.txt`

**不需要上傳**：`MASTER_BLUEPRINT.md`、`bible_lang_app_project.md`、`index.html`、或任何其他專案文件——任務包本身是自包含的，新窗口不需要知道專案背景。

---

## 第三步：標注完成後

把新窗口輸出的 `chunks_en_psalms_001-010.json` 存到 `E:\bible-lang-app\bible_data\` 資料夾。

之後想繼續標注下一批（例如11~20章），重複第一、二步即可，換一次章節範圍。
每一批都是獨立的新窗口、獨立的檔案，不會互相衝突（id編號規則已經設計成不會撞號）。

累積到你覺得夠的量之後，回到熟悉專案的窗口（比如這裡），跑：
```
C:\Users\freeman\AppData\Local\Programs\Python\Python314\python.exe merge_chunks.py
```
會自動合併所有批次、順便算出密度統計，產生 `chunks_data.js`。
