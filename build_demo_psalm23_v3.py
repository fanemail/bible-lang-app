# -*- coding: utf-8 -*-
import json
import re

DATA_PATH = r"E:\bible-lang-app\bible_data\PSA_023_en_word_timestamps.json"
OUTPUT_PATH = r"E:\bible-lang-app\bible_data\audio\en\PSA\demo_psalm23.html"

CHUNKS_DEMO = [
    {"verse": 2, "phrase": "green pastures", "gloss": "青翠的草地／舒適安穩的環境"},
    {"verse": 2, "phrase": "still waters", "gloss": "平靜的水面／內心的平安"},
    {"verse": 4, "phrase": "the valley of the shadow of death", "gloss": "死蔭的幽谷／極度黑暗艱難的處境"},
    {"verse": 6, "phrase": "goodness and loving kindness", "gloss": "恩惠與慈愛"},
]

def normalize(word):
    return re.sub(r"[^a-zA-Z']", "", word).lower()

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

verses_by_num = {v["verse"]: v for v in data["verses"]}

print("=== 語塊比對結果 ===")
for chunk in CHUNKS_DEMO:
    v = verses_by_num.get(chunk["verse"])
    if not v:
        chunk["matched"] = False
        continue
    words = v["words"]
    norm_words = [normalize(w["wordText"]) for w in words]
    phrase_words = [normalize(w) for w in chunk["phrase"].split()]
    n = len(phrase_words)
    match_idx = None
    for i in range(len(norm_words) - n + 1):
        if norm_words[i:i+n] == phrase_words:
            match_idx = i
            break
    if match_idx is None:
        print(f"  !! 第{chunk['verse']}節找不到「{chunk['phrase']}」")
        chunk["matched"] = False
        continue
    chunk["startIdx"] = match_idx
    chunk["endIdx"] = match_idx + n - 1
    chunk["startTime"] = words[match_idx]["startTime"]
    chunk["endTime"] = words[match_idx + n - 1]["endTime"]
    chunk["matched"] = True
    print(f"  第{chunk['verse']}節「{chunk['phrase']}」→ [{chunk['startTime']}-{chunk['endTime']}] OK")

data["chunksDemo"] = [c for c in CHUNKS_DEMO if c.get("matched")]
data_json = json.dumps(data, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>詩篇23篇 語音點讀 Demo</title>
<style>
body{font-family:-apple-system,"Microsoft JhengHei",sans-serif;max-width:700px;margin:40px auto;padding:0 20px;line-height:2.4;font-size:20px;background:#fafaf5;color:#222}
h1{font-size:26px}.verse{margin-bottom:22px}
.vnum{font-weight:bold;color:#888;margin-right:6px}
.word{cursor:pointer;padding:2px 1px;border-radius:4px}
.word:hover{background:#eee}.word.playing{background:#ffe08a}
.chunk-wrap{background:#d9f2d0;border-radius:6px;padding:2px 3px}
.chunk-tag{cursor:pointer;font-size:13px;background:#4c9a4c;color:#fff;border-radius:10px;padding:1px 8px;margin-left:3px;vertical-align:middle}
.chunk-tag:hover{background:#3a7a3a}
.verse-btn{font-size:14px;margin-left:10px;padding:3px 10px;border-radius:12px;border:1px solid #999;background:#fff;cursor:pointer}
.verse-btn:hover{background:#f0f0f0}
#hint{color:#666;font-size:15px;margin-bottom:30px}
</style>
</head>
<body>
<h1>詩篇23篇 · 逐詞語音點讀 Demo</h1>
<p id="hint">點單字播放該字發音；<span style="background:#d9f2d0;padding:1px 6px;border-radius:4px">綠色底色</span>為語塊，點旁邊「▶ 語塊」播放整個語塊；點「播放整節」播放整節。</p>
<div id="verses"></div>
<audio id="player" src="023.mp3" preload="auto"></audio>
<script>
const DATA=__DATA__;
const audio=document.getElementById('player');
const container=document.getElementById('verses');
let stopAt=null;
audio.addEventListener('timeupdate',()=>{
  if(stopAt!==null&&audio.currentTime>=stopAt){
    audio.pause();stopAt=null;
    document.querySelectorAll('.word.playing').forEach(e=>e.classList.remove('playing'));
  }
});
function play(start,end,els){
  document.querySelectorAll('.word.playing').forEach(e=>e.classList.remove('playing'));
  if(els)els.forEach(e=>e.classList.add('playing'));
  audio.currentTime=start;stopAt=end;audio.play();
}
DATA.verses.forEach(v=>{
  const div=document.createElement('div');div.className='verse';
  const vn=document.createElement('span');vn.className='vnum';vn.textContent=v.verse+'. ';div.appendChild(vn);
  const chunks=DATA.chunksDemo.filter(c=>c.verse===v.verse);
  let i=0;const allSpans=[];
  while(i<v.words.length){
    const ck=chunks.find(c=>c.startIdx===i);
    if(ck){
      const wrap=document.createElement('span');wrap.className='chunk-wrap';
      const ckEls=[];
      for(let k=ck.startIdx;k<=ck.endIdx;k++){
        const w=v.words[k];const sp=document.createElement('span');
        sp.className='word';sp.textContent=w.wordText+' ';
        sp.onclick=()=>play(w.startTime,w.endTime,[sp]);
        wrap.appendChild(sp);allSpans.push(sp);ckEls.push(sp);
      }
      const tag=document.createElement('span');tag.className='chunk-tag';
      tag.textContent='▶ 語塊';tag.title=ck.gloss;
      tag.onclick=()=>play(ck.startTime,ck.endTime,ckEls);
      wrap.appendChild(tag);div.appendChild(wrap);i=ck.endIdx+1;
    }else{
      const w=v.words[i];const sp=document.createElement('span');
      sp.className='word';sp.textContent=w.wordText+' ';
      sp.onclick=()=>play(w.startTime,w.endTime,[sp]);
      div.appendChild(sp);allSpans.push(sp);i++;
    }
  }
  const btn=document.createElement('button');btn.className='verse-btn';
  btn.textContent='播放整節';btn.onclick=()=>play(v.startTime,v.endTime,allSpans);
  div.appendChild(btn);container.appendChild(div);
});
</script>
</body>
</html>"""

html = html.replace("__DATA__", data_json)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)
print("Demo已更新：" + OUTPUT_PATH)
