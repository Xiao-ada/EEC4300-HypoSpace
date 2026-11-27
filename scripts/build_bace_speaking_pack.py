"""Build the full English script and UTF-8 Chinese correspondence document."""
from __future__ import annotations
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'presentations/bace_final'
c = json.loads((OUT / 'content.json').read_text())
metrics = json.loads((ROOT / 'results/canonical_preference_v5/test/summary.json').read_text())['metrics']
slides = c['slides']
spoken = [' '.join(v[0] for v in slide['sentences']) for slide in slides]
counts = []
for text in spoken:
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)
    counts.append(len(words) + 2 * words.count('LLM'))
assert sum(counts) == 167
(OUT / 'English_script.txt').write_text('\n\n'.join(spoken) + '\n')
timing = {'spoken_word_count': sum(counts), 'by_slide': counts,
          'convention': 'Hyphen components count separately. LLM is three spoken letters. BACE, LoRA and COVE are pronounced as words.',
          'pause_allowance_seconds': 8,
          'estimated_seconds_including_pause_allowance': {str(rate): round(sum(counts)*60/rate+8,2) for rate in [80,85,90,100]},
          'delivery_condition': 'At least 80 spoken words/minute, at most 8 additional seconds of pauses; read only the script paragraphs.'}
(OUT / 'timing.json').write_text(json.dumps(timing, indent=2)+'\n')

slide1_pairs = [
    (slides[0]['title'], '用于假设覆盖的BACE'),
    (slides[0]['subtitle'], '将预算感知的规范类排除与覆盖目标训练的LoRA模型结合'),
    ('Problem\n' + slides[0]['left'][0][1], '问题\n重复结构会浪费固定的生成预算。'),
    ('Learned proposal\n' + slides[0]['left'][1][1], '学习得到的提议分布\nQwen2.5-1.5B与覆盖LoRA\n损失为SFT损失减去覆盖代理。'),
    ('Generation target\n' + slides[0]['left'][2][1], '生成目标\n十六次尝试中得到十三个不同结构类别'),
    ('Generation process', '生成过程'),
    (slides[0]['steps'][0], '正常采样，并记录规范结构类别。'),
    (slides[0]['steps'][1], '计算余量：剩余尝试次数减去仍需增加的新类别数。'),
    (slides[0]['steps'][2], '余量为零时，屏蔽已经见过的类别。'),
    (slides[0]['steps'][3], '由LLM生成，并计入每一次尝试。'),
    (slides[0]['scope'], '干预期间使用有限语法；不根据观测合法性筛选候选，也没有免费重试。')]
slide2_pairs = [
    (slides[1]['title'], 'BACE结果与解码模块的贡献'),
    (slides[1]['subtitle'], '使用同一训练检查点，在二十六道布尔任务上采用三个推理种子，每题十六次尝试。'),
    (slides[1]['gain'], '恢复率增加九点三二个百分点。'),
    (slides[1]['interval'], '按题bootstrap的95%区间为五点九零到十二点八二个百分点。'),
    (slides[1]['cost'], '在匹配对照中，合法率下降三点五三个百分点。'),
    (slides[1]['learning'], 'LLM与BACE组合的恢复率比均匀采样与BACE组合高十点三一个百分点。'),
    (slides[1]['scope'], '只有一次训练运行；这是对之前使用过的布尔题的探索性跟进。覆盖训练损失相对SFT的额外收益仍未得到证实。')]
slide3_pairs = [(slides[2]['title'], '作为另一种系统思路的COVE'), *zip(slides[2]['body'], slides[2]['translations'])]


md = ['# BACE English script and Chinese correspondence', '',
      '## Timing and delivery', '',
      'The script contains 167 spoken words. At 90 words/minute plus 8 seconds of pauses, it takes about 1:59. At 80 plus 8 seconds, it takes about 2:13. Keep at least 80 words/minute and pauses within 8 seconds to stay under 2:15. Human delivery varies, so rehearse once.', '',
      '讲稿共167个实际口播词，数字已展开。按90词/分加8秒停顿约1分59秒；按80词/分加8秒停顿约2分13秒。只读讲稿正文，不额外朗读标题、表格各项或参考来源。建议计时试读一次。', '',
      'Pronounce BACE like “base”, COVE like “cove”, and LoRA like “low rah”. Spell LLM as “ell ell em”. The word count assumes these pronunciations. The spoken interval “about six to thirteen” rounds the exact slide interval [5.90, 12.82].', '',
      'BACE和COVE按单词读，不逐字拼读；LoRA读作low rah，LLM按三个字母读。口播的“约六到十三”对应幻灯片上精确区间[5.90,12.82]。', '',
      '## Complete English speaking script', '']
for i, text in enumerate(spoken,1):
    md.extend([f'### Slide {i}', '', text, ''])
md.extend(['## Sentence aligned script translation', ''])
for i, slide in enumerate(slides,1):
    md.extend([f'### Slide {i}', ''])
    for j,(en,zh) in enumerate(slide['sentences'],1):
        md.extend([f'**{i}.{j} English**', '', en, '', '**中文**', '', zh, ''])
for i,pairs in enumerate([slide1_pairs,slide2_pairs,slide3_pairs],1):
    md.extend([f'## Slide {i} text translations', '', '| English | 中文逐项对应 |', '|---|---|'])
    for en,zh in pairs:
        md.append('| '+en.replace('\n','<br>')+' | '+zh.replace('\n','<br>')+' |')
    md.append('')
    if i == 2:
        md.extend(['### Result table translation', '', '| Method 方法 | Validity 合法率 | Uniqueness 不重复率 | Recovery 恢复率 |', '|---|---:|---:|---:|'])
        for (label,key),cn in zip(slides[1]['method_rows'],['同一LLM正常采样','同一LLM加BACE','无LLM的均匀采样加BACE']):
            values=[f'{100*metrics[key][m]:.2f}%' for m in ['VR','NR','RR']]
            md.append('| '+label+'<br>'+cn+' | '+' | '.join(values)+' |')
        md.append('')
md.extend(['## Understanding the claims', '',
'BACE限制重复结构，但不提前筛出满足观测的测试答案。余量是剩余尝试次数减去仍需增加的新类别数。唯一率保证来自约束，恢复率和合法率仍需要实测。', '',
'结果页对比同一检查点的两种解码方式，因此支持解码模块的贡献。它没有证明覆盖训练损失优于普通SFT。三个种子是推理重复，测试观测题已在旧实验中出现。', '',
'第三页仅口播两句话。COVE使用学习执行器和固定目录改善最终系统输出，但仅执行器对照也同分，不能据此宣称LLM生成能力提高。其接近99%的数字不与BACE表混用。', '',
'## Sources', '',
'- `docs/BACE_METHOD.md`',
'- `results/canonical_preference_v5/test/summary.json`',
'- `results/all80/test/summary.json`',
'- https://github.com/Xiao-ada/EEC4300-HypoSpace',
'- https://proceedings.mlr.press/v306/chen26bz.html', ''])
(OUT / 'Script_and_translation.md').write_text('\n'.join(md).rstrip()+'\n')
print(json.dumps({'spoken_words':sum(counts),'by_slide':counts,'translation':str(OUT/'Script_and_translation.md')},indent=2))
