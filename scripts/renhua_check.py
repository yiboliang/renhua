#!/usr/bin/env python3
"""renhua_check.py - 中文去 AI 味量化检查（renhua / 人话）

用法: python3 renhua_check.py draft.md [--neg-max 2] [--title-max 20]
      [--bold-min N] [--bold-max N] [--bold-gap N] [--no-first-person] [--allow 词1,词2]
输出: ✗ 必须修改项，⚠ 需人工判断项。有 ✗ 时退出码为 1，可直接用于 CI。
仅依赖 Python 3 标准库。License: MIT
"""
import re, sys, argparse, statistics
ap = argparse.ArgumentParser()
ap.add_argument('file')
ap.add_argument('--neg-max', type=int, default=2)       # 否定对照上限
ap.add_argument('--bold-min', type=int, default=0)
ap.add_argument('--bold-max', type=int, default=99)
ap.add_argument('--bold-gap', type=int, default=0)      # 加粗最大间距，0=不查
ap.add_argument('--title-max', type=float, default=0)   # 标题宽度上限，0=不查
ap.add_argument('--no-first-person', action='store_true')
ap.add_argument('--allow', default='')
ap.add_argument('--profile', nargs='+', default=None, help='作者亲手写的样文，用于声音指纹对比')
a = ap.parse_args()
allow = set(x for x in a.allow.split(',') if x)

raw = open(a.file, encoding='utf-8').read()
raw = re.sub(r'```.*?```', '', raw, flags=re.S)          # 跳过代码块
lines = raw.splitlines()
title = lines[0].lstrip('# ').strip() if lines and lines[0].startswith('# ') else ''
body = '\n'.join(lines[1:]) if title else raw
plain = re.sub(r'\*\*|〔[^〕]*〕|^#+\s*|^>\s*', '', body, flags=re.M)

# 强信号：单次出现就改
STRONG = {
 '聊天残留': [r'好问题', r'希望(这|以上)(能|对你)有?(所)?帮助', r'作为一?个?AI', r'如果你(还)?有(其他|任何)问题', r'截至(目前|我的知识)'],
 '舞台腔开场': [r'让我们(一起)?', r'说实话[，,？?]', r'接下来(我们)?(来)?看', r'答案(其实)?很简单', r'你可能会问'],
 '假深刻': [r'归根结底', r'说到底', r'本质上', r'核心在于', r'真正(重要|关键)的是'],
 '意义膨胀': [r'标志着', r'里程碑', r'深远(的)?影响', r'重大意义', r'新(的)?时代', r'开启.{0,6}新篇章', r'从更宏观(的)?(层面|角度)'],
 '空洞结尾': [r'未来可期', r'值得期待', r'拭目以待', r'未来已来', r'星辰大海', r'才刚刚开始'],
 '套话连接': [r'值得注意的是', r'不难发现', r'换句话说', r'总而言之', r'综上所述', r'由此可见', r'众所周知', r'毋庸置疑', r'不可否认', r'首先', r'其次', r'再次', r'一方面', r'另一方面'],
 '虚假权威': [r'(专家|业内)(普遍)?认为', r'有(研究|数据)(表明|显示)', r'业界公认'],
 '机械编号': [r'短期看', r'中期看', r'长期看', r'一是', r'二是', r'三是', r'第一层', r'第二层'],
 '新套话': [r'说白了', r'说穿了', r'一句话[:：]', r'这背后', r'折射出', r'的缩影', r'的注脚', r'按下.{0,4}快进键', r'牌桌', r'入场券', r'(上|下)半场', r'终局', r'进入深水区', r'静悄悄', r'范式转移', r'新基建', r'答案是[:：]', r'问题来了', r'耐人寻味', r'值得玩味', r'某种意义上', r'回到最初的问题', r'慢就是快', r'做减法', r'胜负手', r'释放了?.{0,4}信号', r'值得一提的是', r'唯一不变的是', r'看懂了.{0,10}就看懂了', r'不再是配角', r'开放共赢', r'成人礼', r'大考', r'青春期'],
 'English': [r'\bdelve\b', r'\btestament\b', r'\blandscape\b', r'\bnot just\b', r'\blet that sink in\b', r"\bhere's the thing\b"],
}
# 弱信号：单独出现不算，密集才改
WEAK = {
 'AI高频词': [r'这意味着', r'换言之', r'更重要的是', r'被(严重)?低估', r'悄然', r'洗牌', r'护城河', r'赛道', r'底色', r'叙事', r'破局', r'赋能', r'闭环', r'抓手', r'底层逻辑', r'颗粒度', r'范式', r'矩阵', r'沉淀', r'势能', r'全方位', r'一站式', r'极致', r'深度解析', r'全面解读', r'生态'],
 '伪深度动词': [r'(提升|促进|推动|助力|加速)[^。，]{0,8}(能力|发展|进程|升级|转型)'],
 '含糊限定': [r'在一定程度上', r'或许', r'可能会', r'某种程度上'],
 '递进套句': [r'不仅[^。]{0,20}(更|而且|还)', r'既是[^。]{0,15}也是'],
}
NEG = r'不是[^。！？\n]{1,30}?而是|不是[^。！？\n]{1,20}?[，,]这是|在[^，。！？\n]{1,15}[，,]不在|以为[^。！？\n]{1,20}?[，,]其实|不在[^。！？\n]{1,30}?而在于?|而不是|与其说[^。]{0,20}不如说'

fails, warns = [], []
OPEN = r'^(在这个.{0,12}的?时代|随着.{0,20}的(发展|到来|普及)|近年来|当今|在当下|如今，)'
first = next((p for p in body.splitlines() if p.strip() and not p.startswith('#')), '')
if re.search(OPEN, re.sub(r'\*\*', '', first.strip())): fails.append(f'[铺垫式开头] {first.strip()[:25]}')
for p in [r'深度解析', r'全面解读', r'一文(读懂|看懂)', r'[！!]', r'震惊', r'重磅']:
    if title and re.search(p, title): fails.append(f'[标题套话] {title}')
def ctx(m):
    s = max(0, m.start() - 10); return plain[s:m.end() + 10].replace('\n', ' ')
for cat, pats in STRONG.items():
    for p in pats:
        for m in re.finditer(p, plain, flags=re.I):
            if m.group() in allow: continue
            fails.append(f'[{cat}]「{m.group()}」…{ctx(m)}…')
for cat, pats in WEAK.items():
    hits = [m for p in pats for m in re.finditer(p, plain) if m.group() not in allow]
    per_k = len(hits) / max(1, len(plain) / 1000)
    if per_k >= 2: fails.append(f'[{cat}] 每千字 {per_k:.1f} 处：' + '、'.join(sorted({h.group() for h in hits}))[:80])
    elif hits: warns.append(f'[{cat}] ' + '、'.join(sorted({h.group() for h in hits})))
neg = re.findall(NEG, plain)
if len(neg) > a.neg_max: fails.append(f'[否定对照] {len(neg)} 处（上限 {a.neg_max}）：' + ' | '.join(n[:18] for n in neg))

paras = [l.strip() for l in body.splitlines() if l.strip()]
skip = ('#', '\U0001F4CC', '〔', '>', '- ', '* ', '|') 
prose = []
for p in paras:
    if p.startswith(skip) or re.match(r'^\d+[.、]', p): continue
    t = re.sub(r'\*\*', '', p); prose.append(t)
    if len(re.findall(r'[。！？!?]', t)) <= 2 and len(t) < 60:
        fails.append(f'[碎段落] {t[:30]}')
    if t.count('；') >= 2: warns.append(f'[分号排比] {t[:30]}')
dash = plain.count('——') + plain.count('—')
if dash / max(1, len(plain) / 1000) > 3: warns.append(f'[破折号] 每千字 {dash/max(1,len(plain)/1000):.1f} 个')
emo = re.findall(r'[\U0001F300-\U0001FAFF☀-➿]', plain.replace('\U0001F4CC', ''))
if emo: warns.append(f'[emoji] {len(emo)} 个')

sents = [s.strip() for s in re.split(r'[。！？!?\n]', plain) if len(s.strip()) > 4]
run = 1
for i in range(1, len(sents)):
    run = run + 1 if sents[i][:2] == sents[i-1][:2] else 1
    if run == 3: fails.append(f'[同开头×3] {sents[i-2][:12]} / {sents[i-1][:12]} / {sents[i][:12]}')
if len(sents) >= 8:
    L = [len(s) for s in sents]; cv = statistics.pstdev(L) / statistics.mean(L)
    if cv < 0.35: warns.append(f'[节奏平] 句长变异系数 {cv:.2f}（<0.35 偏机械）')
if len(prose) >= 5:
    P = [len(p) for p in prose]; cvp = statistics.pstdev(P) / statistics.mean(P)
    if cvp < 0.25: warns.append(f'[段落等长] 段长变异系数 {cvp:.2f}')
tri = re.findall(r'[^，。、]{2,6}、[^，。、]{2,6}(、|和|与)[^，。、]{2,6}[，。]', plain)
if len(tri) >= 3: warns.append(f'[三项并列] {len(tri)} 处，检查是否凑数')

if paras:
    last = paras[-1]
    for w in ['浪潮', '终将', '时代的', '历史的', '未来属于', '每一个人', '值得每一个', '让我们']:
        if w in last: warns.append(f'[结尾升华]「{w}」')

# ---- G 类：结构性 AI 腔 ----
G = [
 ('公式句', r'[\u4e00-\u9fffA-Za-z0-9]{1,12}\s*=\s*[^=\n]{2,}'),
 ('转向句', r'从[^，。！？\n]{1,14}(转向|走向|迈向|升级为|进化为|跃迁到)'),
 ('从A到B×2', r'从[^，。！？\n]{1,8}到[^，。！？\n]{1,8}[，,]\s*从[^，。！？\n]{1,8}到'),
 ('少多口号', r'少(一点)?[^，。；\n]{1,10}[，,；]\s*多(一点)?'),
 ('一边一边', r'一边是[^。\n]{1,20}[，,；]\s*一边是'),
 ('谁…谁就', r'谁[^，。\n]{1,15}[，,]\s*谁就'),
 ('对X我们要', r'对[^，。；\n]{1,6}[，,]\s*我们要[^；。\n]{1,8}[；;]'),
 ('让让让', r'让[^，。\n]{1,10}[，,]\s*让[^，。\n]{1,10}[，,]\s*让'),
 ('升降对照', r'的价值在(下降|降低)[^。\n]{0,20}的价值在(上升|提升)'),
 ('X会变Y会变', r'([^，。\n]{1,6})会变[，,]\s*([^，。\n]{1,6})会变'),
 ('如果说那么', r'如果说[^，。\n]{1,20}[，,]\s*那么'),
 ('第一第二第三', r'第一[，,、：:][^\n]{1,40}?第二[，,、：:][^\n]{1,40}?第三[，,、：:]'),
 ('自问自答', r'[？?]\s*(答案是|未必|当然不|不一定|恰恰相反)'),
 ('很多人以为×2', r'(很多人|有人|大家)以为[^。]{1,30}。[^。]{0,5}(很多人|有人|大家)以为'),
 ('当所有人都', r'当(所有人|大家|别人)都在'),
]
for name, pat in G:
    for m in re.finditer(pat, plain):
        fails.append(f'[结构·{name}]「{m.group()[:24]}」')
for m in re.finditer(r'(三件事|三点|三个(关键|方面|问题|变化)|三条主线)', plain):
    warns.append(f'[凑三宣告]「{m.group()}」检查是否真有三项')
# 收尾金句：最后一段最后一句 ≤8 字，且前面有内容
_ls = [x for x in re.split(r'(?<=[。！？!?])', paras[-1] if paras else '') if x.strip()]
if len(_ls) >= 2 and len(re.sub(r'[。！？!?\s*]', '', _ls[-1])) <= 8:
    warns.append(f'[收尾金句]「{_ls[-1].strip()}」')

bolds = [m.start() for m in re.finditer(r'\*\*(.+?)\*\*', body)]
if len(bolds) < a.bold_min or len(bolds) > a.bold_max:
    fails.append(f'[加粗] {len(bolds)} 句（要求 {a.bold_min}-{a.bold_max}）')
if a.bold_gap and len(bolds) > 1:
    g = max(bolds[i] - bolds[i-1] for i in range(1, len(bolds)))
    if g > a.bold_gap * 1.1: warns.append(f'[加粗间距] 最大约 {g} 字（≤{a.bold_gap}）')
if a.no_first_person:
    for m in re.finditer(r'我(认为|觉得|判断|相信)', plain): fails.append(f'[第一人称判断]「{m.group()}」')
if title and a.title_max:
    w = sum(0.5 if ord(c) < 128 else 1 for c in title)
    if w > a.title_max: fails.append(f'[标题] 宽 {w}（≤{a.title_max}）')

n = len(re.findall(r'[一-鿿]', plain)) + len(re.findall(r'[A-Za-z0-9]+', plain))
def fingerprint(text):
    t = re.sub(r'\*\*|^#+.*$|^>\s*', '', text, flags=re.M)
    ss = [x for x in re.split(r'[。！？!?\n]', t) if len(x.strip()) > 2]
    ps = [x.strip() for x in t.split('\n') if len(x.strip()) > 10]
    k = max(1, len(re.sub(r'\s', '', t)) / 1000)
    L = [len(x.strip()) for x in ss] or [1]
    return {
        '平均句长': statistics.mean(L),
        '句长波动': statistics.pstdev(L) / statistics.mean(L),
        '每句逗号': t.count('，') / max(1, len(ss)),
        '破折号/千字': (t.count('——') + t.count('—')) / k,
        '问号/千字': (t.count('？') + t.count('?')) / k,
        '「我」/千字': len(re.findall(r'我(?!们)', t)) / k,
        '「我们」/千字': t.count('我们') / k,
        '平均段长': statistics.mean([len(p) for p in ps]) if ps else 0,
    }
fp_lines = []
if a.profile:
    ref = [fingerprint(open(p, encoding='utf-8').read()) for p in a.profile]
    base = {key: statistics.mean(r[key] for r in ref) for key in ref[0]}
    cur = fingerprint(body)
    off = 0
    for key in base:
        b, c = base[key], cur[key]
        tol = max(abs(b) * 0.35, {'破折号/千字': 1.5, '问号/千字': 2, '「我」/千字': 3, '「我们」/千字': 3}.get(key, 0.15))
        flag = abs(c - b) > tol
        off += flag
        fp_lines.append(f'  {"⚠" if flag else "·"} {key}: 草稿 {c:.2f} / 作者 {b:.2f}')
    fp_lines.append(f'  偏离 {off}/{len(base)} 项' + ('：整体不像作者，建议按事实骨架重写，不要逐句修' if off >= 3 else ''))
print(f'字数≈{n}  否定对照={len(neg)}  加粗={len(bolds)}  句数={len(sents)}')
print(('FAIL ' if fails else 'PASS ') + str(len(fails)))
for f in fails: print('  ✗', f)
for w in warns: print('  ⚠', w)
if fp_lines:
    print('声音指纹（草稿 vs 作者样文）')
    for x in fp_lines: print(x)
sys.exit(1 if fails else 0)
