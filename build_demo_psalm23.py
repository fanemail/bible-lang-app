# -*- coding: utf-8 -*-
import json

DATA_PATH = r"E:\bible-lang-app\bible_data\PSA_023_en_word_timestamps.json"
OUTPUT_PATH = r"E:\bible-lang-app\bible_data\audio\en\PSA\demo_psalm23.html"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

data_json_str = json.dumps(data, ensure_ascii=False)

html_template = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>詩篇23篇 語音點讀 Demo</title>
<style>
  body { font-family: -apple-system, "Microsoft JhengHei", sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; line-height: 2.2; font-size: 20px; background:#fafaf5; color:#222; }
  h1 { font-size: 26px; }
  .verse { margin-bottom: 22px; }
  .vnum { font-weight: bold; color:#888; margin-right: 6px; }
  .word { cursor: pointer; padding: 2px 1px; border-radius: 4px; }
  .word:hover { background: #eee; }
  .word.playing { background: #ffe08a; }
  .verse-btn { font-size: 14px; margin-left: 10px; padding: 3px 10px; border-radius: 12px; border: 1px solid #999; background: #fff; cursor: pointer; }
  .verse-btn:hover { background: #f0f0f0; }
  #hint { color:#666; font-size:15px; margin-bottom: 30px;}
</style>
</head>
<body>
<h1>詩篇23篇 · 逐詞語音點讀 Demo</h1>
<p id="hint">點擊任一個英文單字，會播放這個字在真人朗讀音頻裡的原始發音片段。點「播放整節」可以播放整節。</p>
<div id="verses"></div>
<audio id="player" src="023.mp3" preload="auto"></audio>

<script>
const DATA = __PSALM_DATA__;
const audio = document.getElementById('player');
const container = document.getElementById('verses');
let stopAt = null;

function stopIfNeeded(){
  if(stopAt !== null && audio.currentTime >= stopAt){
    audio.pause();
    stopAt = null;
    document.querySelectorAll('.word.playing').forEach(el => el.classList.remove('playing'));
  }
}
audio.addEventListener('timeupdate', stopIfNeeded);

function playRange(start, end, el){
  document.querySelectorAll('.word.playing').forEach(x => x.classList.remove('playing'));
  if(el) el.classList.add('playing');
  audio.currentTime = start;
  stopAt = end;
  audio.play();
}

DATA.verses.forEach(v => {
  const verseDiv = document.createElement('div');
  verseDiv.className = 'verse';

  const vnum = document.createElement('span');
  vnum.className = 'vnum';
  vnum.textContent = v.verse + '.';
  verseDiv.appendChild(vnum);

  v.words.forEach(w => {
    const span = document.createElement('span');
    span.className = 'word';
    span.textContent = w.wordText + ' ';
    span.onclick = () => playRange(w.startTime, w.endTime, span);
    verseDiv.appendChild(span);
  });

  const btn = document.createElement('button');
  btn.className = 'verse-btn';
  btn.textContent = '播放整節';
  btn.onclick = () => playRange(v.startTime, v.endTime, null);
  verseDiv.appendChild(btn);

  container.appendChild(verseDiv);
});
</script>
</body>
</html>
"""

html_out = html_template.replace("__PSALM_DATA__", data_json_str)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_out)

print("Demo已產生：" + OUTPUT_PATH)
print("用瀏覽器打開這個檔案即可測試（雙擊，或把檔案拖進Chrome/Edge視窗）。")
