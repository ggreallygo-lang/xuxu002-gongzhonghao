# -*- coding: utf-8 -*-
"""推送前自检：凭据、图片、封面尺寸、版式硬指标。"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ok = True


def fail(msg):
    global ok
    ok = False
    print("[X]", msg)


def note(msg):
    print("[OK]", msg)


def load_env():
    p = os.path.join(ROOT, ".env")
    if not os.path.exists(p):
        fail("缺少 .env（复制 .env.example 并填入 AppID / AppSecret）")
        return {}
    env = {}
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def main():
    env = load_env()
    if not env.get("WECHAT_APP_ID") or not env.get("WECHAT_APP_SECRET"):
        fail("凭据没填全：WECHAT_APP_ID / WECHAT_APP_SECRET")
    else:
        note("凭据已配置")

    article = os.path.join(ROOT, "article.html")
    if not os.path.exists(article):
        fail("缺少 article.html，先跑 python scripts/build.py")
        return report()
    html = open(article, encoding="utf-8").read()

    srcs = re.findall(r'<img[^>]+src="([^"]+)"', html)
    missing = []
    for s in srcs:
        if s.startswith(("http://", "https://")):
            continue
        p = s.replace("file:///", "")
        from urllib.parse import unquote
        p = unquote(p)
        if not os.path.isabs(p):
            p = os.path.join(ROOT, p)
        if not os.path.exists(p):
            missing.append(s)
    if missing:
        fail(f"{len(missing)} 张图找不到：{missing[:3]}")
    else:
        note(f"正文 {len(srcs)} 张图，本地文件齐全")

    checks = {
        "表格 <table>": html.count("<table"),
        "分割线 <hr>": html.count("<hr"),
        "高亮段": html.count("background:#FDEFC8"),
    }
    if checks["表格 <table>"]:
        fail("正文里有 <table>，微信里会变形，请转成图片")
    if checks["分割线 <hr>"]:
        fail("正文里有 <hr>，改用留白")
    if checks["高亮段"] > 6:
        fail(f"高亮 {checks['高亮段']} 处，超过 6 处")
    else:
        note(f"高亮 {checks['高亮段']} 处，无表格、无分割线")

    cfg_path = os.path.join(ROOT, "config.json")
    if not os.path.exists(cfg_path):
        fail("缺少 config.json（复制 config.example.json）")
        return report()
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    try:
        from PIL import Image
    except ImportError:
        note("没装 Pillow，跳过封面尺寸检查（pip install pillow）")
        return report()
    want = {"cover_wide": (900, 383), "cover_square": (400, 400)}
    for key, size in want.items():
        rel = cfg.get(key, "")
        p = os.path.join(ROOT, rel)
        if not rel or not os.path.exists(p):
            fail(f"{key} 文件不存在：{rel}")
            continue
        w, h = Image.open(p).size
        if (w, h) == size:
            note(f"{key} 尺寸正确 {w}×{h}")
        else:
            fail(f"{key} 尺寸是 {w}×{h}，应为 {size[0]}×{size[1]}（按比例直出，不要裁）")
    return report()


def report():
    print()
    print("自检通过，可以推草稿。" if ok else "自检未通过，先按上面的提示改。")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
