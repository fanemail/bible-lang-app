# B1/B2 語塊標注 — 開新窗口交接文字 v2.0

> 這份取代舊版 `handoff_B1_new_window.md`。差異：現在英日一起做、
> 用 PROGRESS.md 自動接續進度，不用自己記章節號。

---

## 第一步：本機跑進度更新（如果上一批做完、剛存完json，先跑這個）

```
C:\Users\freeman\AppData\Local\Programs\Python\Python314\python.exe update_progress.py
```

輸出會告訴你目前英/日各做到哪、下一批建議範圍是幾到幾章。
同時會更新 `E:\bible-lang-app\bible_data\PROGRESS.md`。

---

## 第二步：依照PROGRESS.md建議的範圍，擷取英日合併文字

```
C:\Users\freeman\AppData\Local\Programs\Python\Python314\python.exe extract_chapter_text.py PSA {起始章} {結束章} both
```

（把 `{起始章}` `{結束章}` 換成PROGRESS.md裡建議的數字）

會產生 `chunk_task_input_PSA_both_{起始:03d}-{結束:03d}.txt`，
裡面英日文對照，一個檔案搞定，不用分兩次上傳。

---

## 第三步：開新對話窗口，貼上以下文字

```
請按照這兩份語塊標注任務包（英文B1 + 日文B2），標注附上的這段詩篇經文
（英日對照），分別找出英文語塊和日文語塊，依照各自任務包裡的判定流程、
邊界規則、輸出格式規則來標注。PROGRESS.md是目前的進度記錄，讓你知道
這是接續第幾批。

英文語塊輸出成 chunks_en_psalms_{起始:03d}-{結束:03d}.json
日文語塊輸出成 chunks_ja_psalms_{起始:03d}-{結束:03d}.json
（章節範圍請依實際處理範圍調整檔名）

不確定某個語塊算不算數時，寧可保守不標，不要為了湊數硬標。
```

**然後上傳四個檔案：**
1. `chunk_annotation_task_kit.md`（英文B1任務包 v2.0）
2. `chunk_annotation_task_kit_ja.md`（日文B2任務包 v1.0）
3. `PROGRESS.md`（目前進度，很小的檔案）
4. 剛才產生的 `chunk_task_input_PSA_both_{起始}-{結束}.txt`

**不需要上傳**：MASTER_BLUEPRINT.md、bible_lang_app_project.md、index.html
或任何其他專案文件——任務包本身是自包含的。

---

## 第四步：標注完成後

把新窗口輸出的兩個json檔存到 `E:\bible-lang-app\bible_data\` 資料夾，
回到第一步，重新跑 `update_progress.py` 更新進度，準備下一批。

---

## 累積到覺得夠的量之後

回到熟悉專案的窗口，跑：
```
C:\Users\freeman\AppData\Local\Programs\Python\Python314\python.exe merge_chunks.py
```
自動合併所有批次、算密度統計，產生 `chunks_data.js`。
（這支腳本沿用舊版邏輯，會分別處理 `chunks_en_psalms_*.json` 和
`chunks_ja_psalms_*.json`，兩條語言各自合併。）
