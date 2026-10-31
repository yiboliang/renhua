# renhua 人话 · 中文去 AI 味

> A Chinese-first AI-writing linter + rewriter skill for Claude Code, Codex and other agents that support `SKILL.md`.

中文去 AI 味 skill，带一个可运行的量化检查脚本。它先用脚本扫出套话、宏大比喻、对仗口号、公式句、转向句等 41 类 AI 写作痕迹，再按作者的声音改写。原则是保事实、不编造。

## 和同类 skill 有什么不同

- **有脚本，不靠感觉**：`scripts/renhua_check.py` 只用 Python 标准库，输出 ✗（必须改）和 ⚠（人工判断）。有 ✗ 时退出码为 1，可以直接接进 CI 或写作流水线。
- **抓结构，不只抓词**：公式句（X = A + B）、转向句（从 A 转向 B）、对仗口号（少讲故事，多交付样品）、谁…谁就…、一边是…一边是…、自问自答、比喻对仗，都有专门的检测规则。
- **对照作者，而不是对照「人类平均」**：`--profile` 读入作者亲手写的样文，比较草稿和作者在句长、句长波动、标点、人称、段长上的差距。偏离 3 项以上，提示整篇不像作者。
- **AI 味重的稿子不逐句修**：逐句替换会保留原稿的节奏和骨架。流程里有分流规则，超过阈值就拆成事实清单再重写。
- **先问细节，再动笔**：AI 腔多半是缺细节造成的。改写前先向作者追问最多 3 个具体问题，答不上就标【待补】，不编。
- **改完盲审**：终稿交给没看过改写过程的审稿者（子代理）逐句标注，最多两轮。
- **有回归测试**：`tests/` 里放 AI 腔样本和人写样本，改规则后跑一遍，保证不漏检、不误报。

## 实测

```text
$ bash tests/run.sh
检出 16/16，误报 0/7
```

| 样本 | 旧版脚本（v1） | 当前版本 |
|---|---|---|
| 16 段 2026 年常见中文 AI 腔（公式句、宏大比喻、对仗口号等） | 检出 5/16（只靠「碎段落」规则误打误撞） | 检出 16/16 |
| 7 段人写的行业短评 | 误报 0/7 | 误报 0/7 |

说明：测试样本由维护者编写，其中盲测组在部分规则确定后才补进来，检出率有偏高的可能。欢迎用真实文本补充 `tests/`。

```text
$ python3 scripts/renhua_check.py tests/ai/a04.md
FAIL 3
  ✗ [结构·对X我们要]「对客户，我们要更快；」
  ✗ [结构·对X我们要]「对伙伴，我们要更稳；」
  ✗ [结构·升降对照]「的价值在下降，共封装方案的价值在上升」
```

## 改前改后

**改前**

> 在这个快速变化的时代，光模块行业正迎来新的机遇。值得注意的是，这不是一次简单的升级，而是一场范式革命。首先，算力需求爆发。其次，功耗压力加大。再次，成本持续下降。归根结底，未来已来，让我们拭目以待。

**改后**（原文没有具体事实，改写不会替作者编数据，只标出缺口）

> 光模块这一轮需求，是被算力拉起来的，功耗和成本两头同时在挤。【待补：哪一代速率、哪类客户、价格降了多少】

原文 90 多个字，信息量只够写一句。去 AI 味经常会让人看清原稿其实是空的，这正是它该起的作用。

## 安装

**Claude Code**

```bash
git clone https://github.com/yiboliang/renhua.git ~/.claude/skills/renhua
```

**Codex / 其他支持 skills 的 agent**：把整个目录复制到对应的 skills 文件夹。

**Claude.ai / ChatGPT**：下载 ZIP，在设置的 Skills 页面上传。

**Gemini**：不支持 ZIP 上传。在「技能 → 创建 → 手动创建」里，把 SKILL.md 正文贴进指令栏。这种装法不带脚本，Gemini 会按清单人工扫描。

## 使用

```text
去AI味：
[粘贴文本]
```

```text
帮我查一下这篇有没有AI味，先别改：
[粘贴文本]
```

想让改写更像你本人：复制 `voice/_template.md`，改名为你的名字，用 `--profile` 跑出你的量化指纹填进去。之后每次改写都会对照这份档案。

单独跑脚本：

```bash
python3 scripts/renhua_check.py draft.md --neg-max 2 --title-max 20 --allow 生态,闭环
python3 scripts/renhua_check.py draft.md --profile 我写的1.md 我写的2.md
```

## 局限

- 脚本只抓词和句式，抓不到「这段有没有新信息」和「换个人也能照抄」的空话，这些要靠 SKILL.md 里的逐段自问和盲审。
- 没有标志词的对仗口号（如「提前看到风险，主动制造机会」）脚本抓不到。
- 声音指纹在 800 字以上的稿子上才可靠，短文本只作参考。
- 模型会换新的口头禅，词库需要定期更新，欢迎提 PR，新规则请同时补测试样本。
- 不以骗过 AI 检测器为目标。

## 致谢

思路和模式清单参考了以下项目，规则与脚本为本项目重写：

- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)（WikiProject AI Cleanup）
- [blader/humanizer](https://github.com/blader/humanizer)：强弱分级、先初改再自我挑刺的流程、用样文匹配语感
- [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)：五维评分
- zh-humanizer：中文模式库

## License

MIT
