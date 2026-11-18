# 04 · 排版与发布

## 一、行内样式铁律

公众号后台会剥离 `<style>`、`class`、嵌套容器，只保留行内 `style=""`。

**四条死规则：**

1. **禁用 `<h1>`–`<h6>`** —— 后台强制覆盖样式。标题一律用 `<p>`。
2. **禁止依赖继承** —— 每个元素自己写全所有样式，尤其 `text-align`。
3. **结构必须扁平** —— 每个可见元素都是独立顶层 `<p>`，不嵌套 `<div>`。
4. **每个 `<p>` 是孤儿** —— 自己带齐全部样式。

可用属性：`color / font-size / font-weight / background / border / border-radius / box-shadow / padding / margin / line-height / text-align / max-width`

禁用：`class`、`<style>`、外链 CSS、`var()`、`display:flex`、`position`、`@media`、伪类、JS。

## 二、建草稿的两个脚本

```bash
# 封面图
python3 <skill-dir>/scripts/make_cover.py \
  --main "AI 前线" --sub "第 47 期" --foot "11.16 — 11.18" \
  --out /workspace/<slug>/assets/thumb.png --check

# 上传 + 建草稿 + 回读校验（+ 可选发布）
python3 <skill-dir>/scripts/wechat_draft.py \
  --appid <APPID> --secret <SECRET> \
  --title "标题" --digest "摘要" --author "作者" \
  --body /workspace/<slug>/body.html \
  --cover /workspace/<slug>/assets/thumb.png \
  [--publish]
```

需要真机风格预览稿时，用 wechat-mp-article 的：

```bash
bash <mp-skill>/scripts/new-article.sh <slug> /workspace
bash <mp-skill>/scripts/inject-content.sh /workspace/<slug> --title "标题" --body-file body.html
```

## 三、三个必踩的坑

### 坑 1 · 中文乱码

`json.dumps()` 默认 `ensure_ascii=True`，中文变 `\u524d\u7ebf` 字面量，
微信后台**不解码**，草稿里直接显示一堆 `\uXXXX`。

必须：

```python
json.dumps(payload, ensure_ascii=False).encode("utf-8")
```

请求头：`Content-Type: application/json; charset=utf-8`

`wechat_draft.py` 已内置，且回读时会报告「乱码检查」。

### 坑 2 · 标题与摘要长度

- 标题 ≤ 30 个汉字
- 摘要 ≤ 60 个汉字

在 `ensure_ascii=True` 时一个中文膨胀成 6 字节，极易触发 `45003 / 45004`。

### 坑 3 · 出口 IP 白名单

报 `40164 invalid ip xxx` 时，**用 errmsg 里返回的那个 IP**，
不要用本机 `curl ifconfig.me` 的结果——两者经常不一致。

沙箱环境出口 IP 会漂移，可能需要多次追加。

## 四、错误码速查

| 码 | 含义 | 处理 |
|---|---|---|
| 40164 | IP 不在白名单 | 把 errmsg 里的 IP 加白 |
| 40125 | AppSecret 无效 | 后台重置后换新 Secret |
| 45003 | 标题超长 | 压到 30 汉字内 |
| 45004 | 摘要超长 | 压到 60 汉字内 |
| 48001 | 无发布接口权限 | 未认证订阅号常见，手动群发 |

## 五、发布权限

| 账号类型 | 草稿 API | 发布 API |
|---|---|---|
| 认证服务号 | ✅ | ✅ |
| 认证订阅号 | ✅ | ✅ |
| 未认证订阅号 | ✅ | ❌ 48001 |

`48001` 不要反复重试。直接告诉用户：

> 打开 mp.weixin.qq.com → 内容与互动 → 图文消息 → **草稿箱** → 打开 → 群发

## 六、发布前 checklist

- [ ] 标题 30 字内，含搜索词
- [ ] 摘要 60 字内，能勾人
- [ ] 封面图已生成并**亲眼看过**（文字无遮挡）
- [ ] 正文无 `<h1>`–`<h6>`、无 `class`、无嵌套 `<div>`
- [ ] 图片全部已上传或使用 mmbiz 地址（本地路径在发布后会裂图）
- [ ] 中间多处强调
- [ ] 文末钩子完整
- [ ] 草稿回读确认无 `\u` 转义

## 七、发布后的 24 小时

1. 群发后立刻转发到自己朋友圈 / 相关群
2. 小红书同步发图文版
3. 记录首日阅读数，作为后续选题的基准
4. 关键词回复的领取情况，验证钩子是否有效
