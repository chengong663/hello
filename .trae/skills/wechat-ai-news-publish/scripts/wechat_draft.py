#!/usr/bin/env python3
"""微信公众号：上传封面 + 创建草稿（+ 可选发布）。

关键点（都是踩过的坑）:
  1. json.dumps(..., ensure_ascii=False) —— 否则中文变 \\uXXXX 字面量，后台显示乱码
  2. Content-Type 必须带 charset=utf-8
  3. 标题 ≤ 30 汉字、摘要 ≤ 60 汉字
  4. IP 不在白名单会返回 40164，错误里带真实出口 IP

用法:
    python3 wechat_draft.py --appid wx... --secret ... \
        --title "标题" --digest "摘要" --author "TraeWork" \
        --body body.html --cover assets/thumb.png
        [--publish] [--json]
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

BASE = "https://api.weixin.qq.com"
HEADERS = {"Content-Type": "application/json; charset=utf-8"}


def _get(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(url, payload, raw=False):
    data = payload if raw else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def get_token(appid, secret):
    d = _get(f"{BASE}/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}")
    if "access_token" not in d:
        die(d, "获取 access_token 失败")
    return d["access_token"]


def upload_thumb(token, cover):
    if not os.path.exists(cover):
        die({"errcode": -1, "errmsg": f"封面文件不存在: {cover}"}, "上传封面失败")
    out = subprocess.run(
        ["curl", "-s", "-F", f"media=@{cover};type=image/png",
         f"{BASE}/cgi-bin/material/add_material?access_token={token}&type=thumb"],
        capture_output=True, text=True).stdout
    try:
        d = json.loads(out)
    except json.JSONDecodeError:
        die({"errcode": -1, "errmsg": out[:200]}, "上传封面失败")
    if "media_id" not in d:
        die(d, "上传封面失败")
    return d["media_id"]


def add_draft(token, title, digest, author, content, thumb, source_url=""):
    payload = {"articles": [{
        "title": title,
        "author": author,
        "digest": digest,
        "content": content,
        "thumb_media_id": thumb,
        "show_cover_pic": 1,
        "content_source_url": source_url,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }]}
    d = _post(f"{BASE}/cgi-bin/draft/add?access_token={token}", payload)
    if "media_id" not in d:
        die(d, "创建草稿失败")
    return d["media_id"]


def verify(token, media_id):
    d = _post(f"{BASE}/cgi-bin/draft/get?access_token={token}", {"media_id": media_id})
    item = d.get("news_item", [{}])[0]
    title, content = item.get("title", ""), item.get("content", "")
    escaped = "\\u" in title or "\\u" in content
    return {
        "title": title,
        "digest": item.get("digest", ""),
        "thumb_media_id": item.get("thumb_media_id", ""),
        "content_len": len(content),
        "garble_check": "⚠ 仍存在字面 \\u 转义（乱码！）" if escaped else "正常（无字面转义）",
    }


def publish(token, media_id):
    return _post(f"{BASE}/cgi-bin/freepublish/submit?access_token={token}",
                 {"media_id": media_id})


def die(d, prefix):
    code = d.get("errcode")
    msg = d.get("errmsg", "")
    print(f"✗ {prefix}: errcode={code} errmsg={msg}", file=sys.stderr)
    if code == 40164:
        print("  → IP 不在白名单。请把 errmsg 里的 IP 加入公众号后台 IP 白名单后重试。",
              file=sys.stderr)
    elif code == 40125:
        print("  → AppSecret 无效，请到后台重置后使用新 Secret。", file=sys.stderr)
    elif code == 45003:
        print("  → 标题超长，控制在 30 个汉字以内。", file=sys.stderr)
    elif code == 45004:
        print("  → 摘要超长，控制在 60 个汉字以内。", file=sys.stderr)
    elif code == 48001:
        print("  → 该公众号无此接口权限（未认证订阅号常见），请手动在草稿箱群发。",
              file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--appid", required=True)
    ap.add_argument("--secret", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--digest", default="")
    ap.add_argument("--author", default="TraeWork")
    ap.add_argument("--body", required=True)
    ap.add_argument("--cover", required=True)
    ap.add_argument("--source-url", default="")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    a = ap.parse_args()

    if not os.path.exists(a.body):
        die({"errcode": -1, "errmsg": f"正文文件不存在: {a.body}"}, "读取正文失败")
    with open(a.body, encoding="utf-8") as f:
        content = f.read()

    if a.title and len(a.title) > 30:
        print(f"⚠ 标题 {len(a.title)} 字，超过 30 字建议值，可能触发 45003", file=sys.stderr)
    if a.digest and len(a.digest) > 60:
        print(f"⚠ 摘要 {len(a.digest)} 字，超过 60 字建议值，可能触发 45004", file=sys.stderr)

    token = get_token(a.appid, a.secret)
    thumb = upload_thumb(token, a.cover)
    media_id = add_draft(token, a.title, a.digest, a.author, content, thumb, a.source_url)
    check = verify(token, media_id)

    result = {"media_id": media_id, "thumb_media_id": thumb, **check}

    if a.publish:
        result["publish"] = publish(token, media_id)
        if result["publish"].get("errcode") == 48001:
            result["hint"] = "无发布接口权限，请手动在公众号后台草稿箱群发"

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("✓ 草稿已创建")
        for k, v in result.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    sys.exit(main())
