# renhua 人话 · 中文去 AI 味

> A Chinese-first AI-writing linter + rewriter skill for Claude Code, Codex and other agents that support `SKILL.md`.

中文去 AI 味 skill，带一个可运行的量化检查脚本。它先用脚本扫出套话、否定对照、同构排比、碎段落、空洞结尾等 32 类 AI 写作痕迹，再按作者语感改写。原则是保事实、不编造。

## 和同类 skill 有什么不同

- **有脚本，不靠感觉**：`scripts/renhua_check.py` 只用 Python 标准库，输出 ✗（必须改）和 ⚠（人工判断）。有 ✗ 时退出码为 1，可以直接接进 CI 或写作流水线。
- **强弱分级**：「首先/其次」「值得注意的是」这类强信号出现一次就报；「赋能」「生态」这类弱信号按每千字密度判断，减少技术文里的误报。
- **能调参数**：否定对照上限、标题宽度、加粗句数和间距、是否禁止第一人称、术语白名单都可以设。
- **为中文写的**：清单里有意义膨胀、伪深度动词、同义词轮换、铺垫式开头、概念堆砌式标题这些中文特有的模式，英文常见痕迹也顺带检查。

## 实测

| 样稿 | 结果 |
|---|---|
| `examples/ai-sample.md`（典型 AI 腔，85 字） | FAIL，12 处 ✗ |
| `examples/human-sample.md`（人写的行业短评，243 字） | PASS，0 处 |

```text
$ python3 scripts/renhua_check.py examples/ai-sample.md --title-max 20
字数≈85  否定对照=1  加粗=1  句数=6
FAIL 12
  ✗ [铺垫式开头] 在这个快速变化的时代，光模块行业正迎来新的机遇。值
  ✗ [标题套话] 深度解析：AI时代光模块的未来
  ✗ [假深刻]「归根结底」…
  ✗ [空洞结尾]「未来已来」…
  ✗ [套话连接]「首先」「其次」「再次」…
  ...
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

**Claude.ai / Claude Desktop**：下载 ZIP，在设置里上传为 skill。

## 使用

```text
去AI味：
[粘贴文本]
```

```text
帮我查一下这篇有没有AI味，先别改：
[粘贴文本]
```

想让改写更像你本人，可以先给 2-3 段自己写的样文：

```text
这是我平时写的东西，照这个语感来：
[样文]

现在把下面这篇去AI味：
[文本]
```

单独跑脚本：

```bash
python3 scripts/renhua_check.py draft.md --neg-max 2 --title-max 20 --allow 生态,闭环
```

## 局限

- 脚本只抓词和句式，抓不到「这段有没有新信息」，内容层的判断要靠 SKILL.md 里的逐段自问。
- 「在 A，不在 B」这类否定对照的变体还没收进检测，因为误报率偏高。
- 模型会换新的口头禅，词库需要定期更新，欢迎提 PR。
- 不以骗过 AI 检测器为目标。

## 致谢

思路和模式清单参考了以下项目，规则与脚本为本项目重写：

- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)（WikiProject AI Cleanup）
- [blader/humanizer](https://github.com/blader/humanizer)：强弱分级、先初改再自我挑刺的流程、用样文匹配语感
- [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)：五维评分
- zh-humanizer：中文模式库

## License

MIT
