---
name: "wechat-account-ops"
description: "公众号全链路运营：冷启动诊断、选题规划、推文写作、排版与草稿发布。Invoke when user asks to 运营公众号、做选题规划、写推文、或发布到公众号（0粉新号亦可）。"
---

# 微信公众号全链路运营

一条从「账号怎么活下去」到「稿子怎么发出去」的完整流水线。

## 决策次序

```
先诊断（账号处在什么阶段）
  → 再选题（这个阶段该写什么）
    → 再写作（怎么写得不像AI）
      → 最后发布（怎么排、怎么建草稿）
```

**不要跳过诊断直接写稿。** 0 粉账号和 1 万粉账号该写的东西完全不同，写错阶段等于白干。

## 路由

| 用户意图 | 读哪篇 |
|---|---|
| 账号没流量 / 涨不动 / 刚注册 / 要做规划 | `references/01-ops-coldstart.md` |
| 下个月发什么 / 没选题 / 选题没效果 | `references/02-topic-selection.md` |
| 写一篇推文 / 稿子太像 AI / 结构怎么搭 | `references/03-writing.md` |
| 要现成模板 / 不知道实测稿长什么样 | `references/05-sample-teardown.md` + `samples/excel-measure/body.html` |
| 排版 / 建草稿 / 发布 / 接口报错 | `references/04-publish.md` |

一个请求只读最相关的一篇。全链路任务按顺序读。

有范文时优先抄结构：`samples/excel-measure/body.html` 是跑通过的实测稿正文，
改数字、改细节、换提示词即可，样式参数不要动。

## 四个阶段的核心答案

| 阶段 | 核心问题 | 答案方向 |
|---|---|---|
| 运营 | 流量从哪来 | 0 粉靠搜一搜 + 小红书导流，不靠公众号内部 |
| 选题 | 写什么才有人看 | 写「具体问题」不写「行业新闻」 |
| 写作 | 怎么不像 AI 写的 | 一到两句一段，事实密度优先，杀掉缝合语 |
| 发布 | 怎么发不出错 | 行内样式 + `ensure_ascii=False` + 白名单 IP |

## 脚本

```bash
# 1. 封面图（900x383）
python3 <skill-dir>/scripts/make_cover.py \
  --main "AI 前线" --sub "第 47 期" --foot "11.16 — 11.18" \
  --out /workspace/<slug>/assets/thumb.png --check

# 2. 上传封面 + 建草稿 + 回读校验（+ 可选发布）
python3 <skill-dir>/scripts/wechat_draft.py \
  --appid <APPID> --secret <SECRET> \
  --title "标题" --digest "摘要" --author "作者" \
  --body /workspace/<slug>/body.html \
  --cover /workspace/<slug>/assets/thumb.png \
  [--publish] [--json]
```

## 三条不可退让的底线

1. **实测必须是真跑的**。数字、截图、踩的坑都要是自己的。编造的实测被发现一次，账号就废了。
2. **每篇至少一张承载论据的图**。数据图、流程图、真实截图。没有的话宁可不写，不要放氛围图充数。
3. **正文必须有强调**。通篇平铺等于没写，金句要能从段落里跳出来。

## 与其他能力的关系

- 排版与方法论细节可加载 `trae-remote-official:wechat-mp-article:wechat-mp-article`
- 需要真机预览稿时，用它的 `new-article.sh` + `inject-content.sh`
- 本 skill 负责「策略与判断」，那个 skill 负责「模板与排版执行」
