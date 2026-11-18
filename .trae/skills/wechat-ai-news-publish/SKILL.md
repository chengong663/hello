---
name: "wechat-ai-news-publish"
description: "搜集最新 AI 新闻并生成公众号推文，自动生成封面图、上传素材、创建微信草稿。Invoke when user asks to 发一篇AI新闻推文 or 公众号发AI资讯 with AppID/AppSecret provided."
---

# 微信公众号 · AI 新闻推文发布

把「搜新闻 → 写推文 → 做封面 → 建草稿」串成一条可复用流水线。

## 前置条件

用户需提供 **AppID** 与 **AppSecret**，并已把当前出口 IP 加入公众号后台
`设置与开发 → 基本配置 → IP 白名单`。

沙箱出口 IP 会变化，若报 `40164 invalid ip`，直接读取错误里返回的那个 IP，
提示用户追加白名单后重试。

## 执行流程

### Step 1 · 搜集新闻

用 `WebSearch` + `WebFetch` 抓取过去 2—3 天的 AI 行业新闻，覆盖多个赛道：

- 模型发布（OpenAI / Anthropic / Google DeepMind / 国产大模型）
- 财报与融资（上市公司公告、一级市场融资）
- 芯片与硬件（算力、端侧、可穿戴）
- 政策与伦理（联合国、监管、研究报告）

每条新闻必须记录：**发生了什么 + 关键数字 + 来源 + 日期**。
不要编造数字；拿不到就写"官方未披露"。

### Step 2 · 写正文

加载 `trae-remote-official:wechat-mp-article:wechat-mp-article` skill，
按其中的**科技数码（01-tech）**或**资讯（02-news-and-gov）**方法论写作。

硬性要求：

- 每个可见元素都是独立顶层 `<p>`，全套样式写在行内 `style=""`
- 禁用 `<h1>`–`<h6>`、`class`、`<style>`、flex、`var()`
- 一到两句一段，长短句交错，杀掉"值得注意的是""与此同时"这类缝合语
- 至少 3—5 处正文内强调（加粗 / 变色 / 单句成段），不要通篇平铺
- 每条新闻末尾标注来源

正文写到 `<slug>/body.html`。

### Step 3 · 调用 wechat-mp-article 建目录（可选）

若需要真机预览稿：

```bash
bash <wechat-mp-article-skill-dir>/scripts/new-article.sh <slug> /workspace
bash <wechat-mp-article-skill-dir>/scripts/inject-content.sh /workspace/<slug> \
  --title "标题" --body-file /workspace/<slug>/body.html
```

### Step 4 · 生成封面图

```bash
python3 <skill-dir>/scripts/make_cover.py \
  --main "AI 前线" --sub "第 47 期" --foot "11.16 — 11.18" \
  --out /workspace/<slug>/assets/thumb.png
```

尺寸固定 900×383（微信推荐 2.35:1）。**生成后必须用 Read 看一眼**，
确认文字没被色块遮挡、没有裁切。

### Step 5 · 上传素材并建草稿

```bash
python3 <skill-dir>/scripts/wechat_draft.py \
  --appid  <APPID> \
  --secret <APPSECRET> \
  --title   "推文标题" \
  --digest  "80 字以内摘要" \
  --author  "TraeWork" \
  --body    /workspace/<slug>/body.html \
  --cover   /workspace/<slug>/assets/thumb.png
```

脚本会依次完成：取 token → 上传永久缩略图 → `draft/add` → `draft/get` 回读校验，
并打印 `MEDIA_ID` 与「乱码检查」结果。

### Step 6 · 尝试发布

脚本加 `--publish` 会调用 `freepublish/submit`。

- 成功：返回 `publish_id`，进入审核队列
- 返回 `48001 api unauthorized`：该公众号无发布接口权限（未认证个人订阅号常见）

遇到 48001 不要反复重试，直接告知用户手动发布：

> 打开 mp.weixin.qq.com → 内容与互动 → 图文消息 → **草稿箱** → 打开本篇 → 群发

## ⚠️ 必踩过的三个坑

### 坑 1 · 中文乱码（最严重）

`json.dumps(payload)` 默认 `ensure_ascii=True`，中文会被转成 `\u524d\u7ebf`
字面量，微信后台**不解码**，草稿里就直接显示成一堆 `\uXXXX`。

必须写成：

```python
json.dumps(payload, ensure_ascii=False).encode("utf-8")
```

并且请求头用 `Content-Type: application/json; charset=utf-8`。

`wechat_draft.py` 已内置正确写法，且会在回读校验时报告是否仍存在字面转义。

### 坑 2 · 标题/摘要长度按字节算

`title size out of limit`（45003）与 `description size out of limit`（45004）
在 `ensure_ascii=True` 时极易触发——一个中文字会膨胀成 6 个字节。

控制：**标题 ≤ 30 个汉字，摘要 ≤ 60 个汉字**，并用 `ensure_ascii=False`。

### 坑 3 · 出口 IP 漂移

沙箱出口 IP 每次请求可能不同。`40164` 报错里会带真实 IP，照着加白名单即可，
不要把本机 `curl ifconfig.me` 的结果当作微信看到的 IP——两者常不一致。

## 交付

- 预览稿：`/workspace/<slug>/index.html`
- 正文源：`/workspace/<slug>/body.html`
- 封面：`/workspace/<slug>/assets/thumb.png`
- 草稿：已建在公众号草稿箱，附 `MEDIA_ID`

给用户的收尾话术要包含：草稿已就绪 / 手动发布入口 / 若需 API 直发需先完成微信认证。
