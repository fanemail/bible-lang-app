# B1 / B2 語塊標注進度追蹤

（此檔案由 update_progress.py 自動產生，每次做完新一批後重新跑一次即可更新）

總範圍：詩篇 1~150 章

## 英文語塊（B1）
- 已完成章節：1-10
- 已標注語塊總數：38
- **下一批建議範圍：11 ~ 30 章**

## 日文語塊（B2）
- 已完成章節：1-10
- 已標注語塊總數：35
- **下一批建議範圍：11 ~ 30 章**

## 下一步該做的事
英日進度一致，下一批一起做 11~30 章：

```
python extract_chapter_text.py PSA 11 30 both
```

會產生 `chunk_task_input_PSA_both_011-030.txt`，
開新窗口時，上傳：這份 PROGRESS.md + chunk_annotation_task_kit.md +
chunk_annotation_task_kit_ja.md + 剛產生的這個文字檔（共4個檔案，1次搞定）。
