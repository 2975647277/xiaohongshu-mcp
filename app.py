#!/usr/bin/env python3
"""小红书 AI 发布助手 - Web UI"""

import os, sys, json, time, base64, io, threading, subprocess, webbrowser
import requests as req_lib
from datetime import date
from flask import Flask, request, jsonify, render_template
from PIL import Image

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
IMAGE_PATH  = os.path.join(BASE_DIR, "static", "preview.png")
MCP_URL     = "http://localhost:18060/mcp"
MCP_BIN     = os.path.join(BASE_DIR,
    "xiaohongshu-mcp-windows-amd64.exe" if sys.platform=="win32"
    else "xiaohongshu-mcp-darwin-arm64")

app = Flask(__name__)

# ── 配置 ──────────────────────────────────────────────────────
def load_cfg():
    d = {"api_key":"","base_url":"https://api.anthropic.com",
         "model":"claude-sonnet-4-6","coordinate":"花桥"}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE,"r",encoding="utf-8") as f: d.update(json.load(f))
        except: pass
    return d

def save_cfg(c):
    with open(CONFIG_FILE,"w",encoding="utf-8") as f:
        json.dump(c,f,ensure_ascii=False,indent=2)

# ── AI ────────────────────────────────────────────────────────
OPTIMIZER_SYS = """你是一个刷小红书的普通人。用户给你一个想法，你帮他想：
- 这个事情最扎心/最真实的那一个点是什么？只抓一个点
- 用什么情绪说出来最让人想评论？（吐槽、求助、自嘲、迷茫）
- 怎么说才像发微信一样随意，不像在写文章？
输出一句话的核心切入点就够了。"""

GENERATOR_SYS = """你在发一条小红书，就像发朋友圈或者微信群里随口说一句。

参考真实爆款笔记的风格：
- "昆山花桥有人吗？" ← 就这一句话，59条评论
- "有没有精神小妹让我谈一下" ← 随口一句，23条评论
- "97年，160/50，现居昆山花桥，工作是互联网产品岗" ← 直接报条件

规则：
- 正文50-150字，越短越好，像在打字不像在写作
- 不要分段排版，不要工整的段落结构，就是一口气说完
- 不要铺垫不要过渡不要升华，想到什么说什么
- 语气随意，像跟朋友发消息，可以有错别字感/口语感
- 结尾可以留个钩子但别刻意，"有人吗""dd我""蹲一个"这种就行
- 标题可以就是正文第一句，也可以空着不写
- 禁止用：宝子们/姐妹们/家人们/绝绝子/YYDS/强烈推荐

严格按JSON返回，不要其他内容：
{"title":"...","content":"...","tags":["..."],"image_lines":["一句话钩子（6字以内）"],"bg_color":"#暖色十六进制","text_color":"#深色十六进制"}"""

def make_openai_client(api_key, base_url):
    from openai import OpenAI
    return OpenAI(
        api_key=api_key,
        base_url=(base_url or "https://api.openai.com/v1").rstrip("/"),
        timeout=120.0)

def ai_generate(api_key, base_url, model, topic, desc, coord):
    client = make_openai_client(api_key, base_url)

    # 第一步：优化提示词
    opt = client.chat.completions.create(
        model=model, max_tokens=500,
        messages=[
            {"role":"system","content":OPTIMIZER_SYS},
            {"role":"user","content":f"主题：{topic}\n描述：{desc}\n坐标：{coord}"}])
    optimized = opt.choices[0].message.content

    # 第二步：生成内容
    gen = client.chat.completions.create(
        model=model, max_tokens=1500,
        messages=[
            {"role":"system","content":GENERATOR_SYS},
            {"role":"user","content":f"{optimized}\n\n地点：{coord}"}])

    raw = gen.choices[0].message.content.strip()
    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:   raw = raw.split("```")[1].split("```")[0].strip()
    return json.loads(raw)

# ── 配图（HTML → Playwright 截图，像真人做的）─────────────────

# 8套小红书真实风格模板
XHS_TEMPLATES = [
    # 0: 奶油莫兰迪
    {"bg":"linear-gradient(135deg,#F5EFE6 0%,#E8D5C0 100%)","card":"rgba(255,252,248,0.92)",
     "title":"#3D2B1F","sub":"#7A5C44","accent":"#C17F5A","tag":"#C17F5A","style":"morandi"},
    # 1: 梦幻紫粉
    {"bg":"linear-gradient(135deg,#FDE8F5 0%,#E8C5F0 100%)","card":"rgba(255,240,252,0.92)",
     "title":"#4A1060","sub":"#8B3A9E","accent":"#C855A8","tag":"#C855A8","style":"pink"},
    # 2: 清新薄荷绿
    {"bg":"linear-gradient(135deg,#E0F5EE 0%,#B8EDD8 100%)","card":"rgba(240,255,250,0.92)",
     "title":"#1A4A38","sub":"#2E7A5A","accent":"#2EBD82","tag":"#2EBD82","style":"mint"},
    # 3: 深夜香槟（暗色）
    {"bg":"linear-gradient(135deg,#1A1020 0%,#2D1B3D 100%)","card":"rgba(40,25,60,0.85)",
     "title":"#F5E6D0","sub":"#C8A87E","accent":"#D4A847","tag":"#D4A847","style":"dark"},
    # 4: 日落橘
    {"bg":"linear-gradient(135deg,#FFF0E0 0%,#FFD4A8 100%)","card":"rgba(255,248,235,0.92)",
     "title":"#6B2D00","sub":"#A0531A","accent":"#E87C30","tag":"#E87C30","style":"sunset"},
    # 5: 轻奢玫瑰
    {"bg":"linear-gradient(135deg,#FFF0F3 0%,#FFD6DE 100%)","card":"rgba(255,245,248,0.92)",
     "title":"#5C0A1A","sub":"#9E2340","accent":"#E83058","tag":"#E83058","style":"rose"},
    # 6: 高级灰蓝
    {"bg":"linear-gradient(135deg,#EEF2F8 0%,#D4E0F0 100%)","card":"rgba(245,248,255,0.92)",
     "title":"#1A2A4A","sub":"#3A5A8A","accent":"#3A6ECC","tag":"#3A6ECC","style":"blue"},
    # 7: 抹茶奶酪
    {"bg":"linear-gradient(135deg,#F0F7E6 0%,#D4EAB8 100%)","card":"rgba(245,252,238,0.92)",
     "title":"#2A4A1A","sub":"#4A7A2A","accent":"#7AB648","tag":"#7AB648","style":"matcha"},
]

def _build_html(lines, tpl):
    hook = lines[0] if lines else ""
    sub  = lines[1] if len(lines) > 1 else ""
    is_dark  = tpl["style"] == "dark"
    noise_op = "0.03" if is_dark else "0.025"
    # 主钩子字号：字少则大，最大120px
    hook_sz = max(64, 120 - max(0, len(hook) - 4) * 10)
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    width:1080px; height:1080px; overflow:hidden;
    background:{tpl["bg"]};
    font-family: "PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
    position:relative;
    display:flex; align-items:center; justify-content:center;
  }}

  body::before {{
    content:""; position:absolute; inset:0; z-index:0;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='{noise_op}'/%3E%3C/svg%3E");
    background-size: 300px 300px; pointer-events:none;
  }}

  body::after {{
    content:""; position:absolute; z-index:0;
    width:500px; height:500px; border-radius:50%;
    top:-150px; right:-150px;
    background: radial-gradient(circle, {tpl["accent"]}18 0%, transparent 70%);
    pointer-events:none;
  }}

  .center {{
    position:relative; z-index:1;
    text-align:center;
    padding: 0 80px;
  }}

  .hook {{
    font-size:{hook_sz}px;
    font-weight:900; line-height:1.2;
    color:{tpl["title"]};
    letter-spacing:-1px;
    margin-bottom:32px;
  }}

  .sub {{
    font-size:40px; font-weight:500;
    color:{tpl["sub"]}; line-height:1.5;
    letter-spacing:0.5px;
  }}

  .deco {{
    position:absolute; z-index:0;
    width:360px; height:360px; border-radius:50%;
    bottom:-100px; left:-100px;
    background: radial-gradient(circle, {tpl["accent"]}12 0%, transparent 60%);
    pointer-events:none;
  }}
</style>
</head>
<body>
  <div class="deco"></div>
  <div class="center">
    <div class="hook">{hook}</div>
    {sub_html}
  </div>
</body>
</html>"""

def make_image(lines, bg_hint, fg_hint):
    import hashlib, time
    from playwright.sync_api import sync_playwright

    # 内容 + 当前秒级时间戳混合，保证同内容多次生成也能轮换主题
    mix = "".join(lines) + str(int(time.time()) // 5)
    seed = int(hashlib.md5(mix.encode()).hexdigest(), 16)
    tpl  = XHS_TEMPLATES[seed % len(XHS_TEMPLATES)]
    html = _build_html(lines, tpl)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page(viewport={"width":1080,"height":1080})
        page.set_content(html, wait_until="domcontentloaded")
        page.wait_for_timeout(300)
        page.screenshot(path=IMAGE_PATH, clip={"x":0,"y":0,"width":1080,"height":1080})
        browser.close()

    thumb = Image.open(IMAGE_PATH).resize((420,420), Image.LANCZOS)
    buf   = io.BytesIO(); thumb.save(buf,"PNG"); buf.seek(0)
    return base64.b64encode(buf.read()).decode()

# ── MCP ───────────────────────────────────────────────────────
def start_mcp():
    try:
        r=req_lib.post(MCP_URL,json={"jsonrpc":"2.0","id":0,"method":"initialize",
            "params":{"protocolVersion":"2024-11-05","capabilities":{},
                      "clientInfo":{"name":"app","version":"1"}}},timeout=3)
        if r.status_code==200: return True
    except: pass
    subprocess.Popen([MCP_BIN,"-headless"],cwd=BASE_DIR,
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(4); return True

def mcp_session():
    r=req_lib.post(MCP_URL,json={"jsonrpc":"2.0","id":1,"method":"initialize",
        "params":{"protocolVersion":"2024-11-05","capabilities":{},
                  "clientInfo":{"name":"xhs-app","version":"1"}}})
    return r.headers.get("Mcp-Session-Id")

def mcp_tool(sid,name,args={}):
    r=req_lib.post(MCP_URL,headers={"Mcp-Session-Id":sid},json={
        "jsonrpc":"2.0","id":10,"method":"tools/call",
        "params":{"name":name,"arguments":args}})
    return r.json()

# ── API 路由 ──────────────────────────────────────────────────
@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/config", methods=["GET","POST"])
def config_route():
    if request.method=="GET": return jsonify(load_cfg())
    data=request.json; save_cfg(data); return jsonify({"ok":True})

@app.route("/api/generate", methods=["POST"])
def generate():
    d=request.json
    # 基本参数校验
    if not d.get("api_key","").strip():
        return jsonify({"ok":False,"error":"API Key 未填写，请在配置区填写并保存"})
    if not d.get("model","").strip():
        return jsonify({"ok":False,"error":"模型名称未填写"})
    if not d.get("topic","").strip():
        return jsonify({"ok":False,"error":"主题未填写"})
    try:
        result=ai_generate(d["api_key"],d.get("base_url",""),d["model"],
                           d["topic"],d.get("desc",""),d.get("coord","花桥"))
        img_b64=make_image(result.get("image_lines",[result["title"]]),
                           result.get("bg_color","#FFF5E6"),
                           result.get("text_color","#8B4513"))
        result["image_preview"]=img_b64
        return jsonify({"ok":True,"data":result})
    except json.JSONDecodeError:
        return jsonify({"ok":False,"error":"AI 返回格式异常，请重试"})
    except Exception as e:
        msg = str(e)
        # 给常见错误友好提示
        if "timed out" in msg or "timeout" in msg.lower():
            msg = "请求超时，请检查网络连接或稍后重试"
        elif "401" in msg or "authentication" in msg.lower():
            msg = "API Key 无效或已过期，请检查配置"
        elif "404" in msg:
            msg = "模型名称不存在，请检查模型配置"
        elif "Connection" in msg or "connect" in msg.lower():
            msg = f"无法连接到 API，请检查 Base URL 是否正确（当前：{d.get('base_url','未填写')}）"
        return jsonify({"ok":False,"error":msg})

@app.route("/api/test", methods=["POST"])
def test_conn():
    d=request.json
    try:
        client = make_openai_client(d.get("api_key",""), d.get("base_url",""))
        client.chat.completions.create(
            model=d.get("model","gpt-4o-mini"),
            max_tokens=5,
            messages=[{"role":"user","content":"hi"}])
        return jsonify({"ok":True})
    except Exception as e:
        msg=str(e)
        if "401" in msg or "auth" in msg.lower(): msg="API Key 无效"
        elif "404" in msg: msg="模型名称不存在，请检查"
        elif "timeout" in msg.lower(): msg="连接超时，请检查 Base URL 和网络"
        elif "connect" in msg.lower(): msg="无法连接，请检查 Base URL 是否正确"
        return jsonify({"ok":False,"error":msg})

@app.route("/api/mcp/status")
def mcp_status():
    try:
        start_mcp(); sid=mcp_session()
        logged=mcp_tool(sid,"check_login_status")
        text=logged["result"]["content"][0]["text"]
        return jsonify({"ok":True,"logged_in":"已登录" in text})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)})

@app.route("/api/mcp/qrcode")
def mcp_qrcode():
    try:
        start_mcp(); sid=mcp_session()
        res=mcp_tool(sid,"get_login_qrcode")
        for item in res["result"]["content"]:
            if item["type"]=="image":
                return jsonify({"ok":True,"image":item["data"]})
        return jsonify({"ok":False,"error":"无法获取二维码"})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)})

@app.route("/api/publish", methods=["POST"])
def publish():
    d=request.json
    try:
        start_mcp(); sid=mcp_session()
        if not ("已登录" in mcp_tool(sid,"check_login_status")["result"]["content"][0]["text"]):
            return jsonify({"ok":False,"need_login":True})
        sid=mcp_session()
        tags=[t.lstrip("#").strip() for t in d.get("tags","").split() if t.strip()]
        res=mcp_tool(sid,"publish_content",{
            "title":d["title"],"content":d["content"],
            "images":[IMAGE_PATH],"tags":tags})
        text=res["result"]["content"][0]["text"]
        ok="发布完成" in text or "成功" in text
        return jsonify({"ok":ok})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)})

if __name__=="__main__":
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:7788")).start()
    print("🌸 小红书 AI 发布助手已启动 → http://127.0.0.1:7788")
    app.run(port=7788, debug=False)
