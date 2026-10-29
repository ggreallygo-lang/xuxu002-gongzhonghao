# -*- coding: utf-8 -*-
"""content.json -> article.html（公众号可用的内联样式）。"""
import json, os, sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "content.json")
OUT = os.path.join(ROOT, "article.html")

P = "font-size:16px;line-height:1.7;letter-spacing:0;color:#3a3a3a;margin:0 0 14px;"
H2 = "font-size:20px;font-weight:700;color:#3a3a3a;line-height:1.5;margin:44px 0 20px;"
IMG = "max-width:100%;height:auto;display:block;margin:30px auto 10px;border-radius:0;"
CAP = "font-size:12.5px;line-height:1.8;color:#A8A29A;text-align:center;margin:0 0 30px;"
MARK = "background:#FDEFC8;font-weight:600;color:#1B2838;"
BG = "#FDFCF9"


def url_of(src):
    if src.startswith(("http://", "https://", "file://")):
        return src
    path = os.path.abspath(os.path.join(ROOT, src)).replace("\\", "/")
    return quote(path, safe="/:")


def render(block):
    t = block.get("t")
    if t == "p":
        return f'<p style="{P}">{block["text"]}</p>'
    if t == "bold":
        return f'<p style="{P}"><span style="{MARK}">{block["text"]}</span></p>'
    if t == "h2":
        return f'<h2 style="{H2}"><span style="color:#D2691E;">{block["n"]}</span> · {block["text"]}</h2>'
    if t == "img":
        return (f'<p style="{P}"><img src="{url_of(block["src"])}" alt="" style="{IMG}"></p>'
                f'<p style="{CAP}">{block.get("cap", "")}</p>')
    if t == "code":
        return ('<section style="background:#F7F4EC;padding:16px 18px;margin:24px 0 26px;'
                'border-left:3px solid #F4B400;">'
                '<pre style="margin:0;font-family:Menlo,Consolas,monospace;font-size:12.5px;'
                'line-height:1.7;color:#3A3A3A;white-space:pre-wrap;word-break:break-word;">'
                f'{block["text"]}</pre></section>')
    raise SystemExit(f"未知的块类型：{t}")


def meta_card(items):
    rows = "".join(
        f'<span style="margin-right:26px;white-space:nowrap;">'
        f'<b style="font-size:22px;color:#1B2838;">{v}</b>'
        f'<span style="font-size:12px;color:#A8A29A;margin-left:6px;">{k}</span></span>'
        for k, v in items)
    return f'<section style="background:#F7F4EC;padding:22px 24px;margin:30px 0 34px;line-height:1.6;">{rows}</section>'


def main():
    if not os.path.exists(SRC):
        raise SystemExit("找不到 content.json，先复制 content.example.json")
    data = json.load(open(SRC, encoding="utf-8"))
    body = []
    for block in data["blocks"]:
        body.append(render(block))
        if block.get("meta"):
            body.append(meta_card(block["meta"]))
    if data.get("meta"):
        body.insert(1, meta_card(data["meta"]))

    html = (
        '<section id="wenyan" style="font-family:-apple-system,BlinkMacSystemFont,&quot;PingFang SC&quot;,'
        '&quot;Microsoft YaHei&quot;,sans-serif;font-size:16px;line-height:1.7;letter-spacing:0;color:#000;'
        f'background-color:{BG};padding:0 6px;">' + "".join(body) + "</section>"
    )
    open(OUT, "w", encoding="utf-8").write(html)
    print(f"已生成 article.html：{html.count('<img')} 张图，{len(data['blocks'])} 个块")


if __name__ == "__main__":
    main()
