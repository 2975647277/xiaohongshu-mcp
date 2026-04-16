#!/usr/bin/env python3
"""
小红书每日自动发布脚本
- 每天轮换3套内容模板
- Cookie过期时发送Mac通知
- 自动启动MCP服务
"""

import json
import subprocess
import time
import os
import sys
import requests
from datetime import date
from PIL import Image, ImageDraw, ImageFont

MCP_URL = "http://localhost:18060/mcp"
MCP_BIN = os.path.join(os.path.dirname(__file__), "xiaohongshu-mcp-darwin-arm64")
IMAGE_PATH = "/tmp/xhs_daily_post.png"

# 3套内容模板，按天轮换
TEMPLATES = [
    {
        "title": "花桥有人吗",
        "content": (
            "来花桥大半年了 认识的人还是只有同事和房东\n"
            "周末翻遍微信不知道找谁 有没有花桥的dd我"
        ),
        "image_text": [
            ("花桥有人吗", 120, "#C0392B", 460),
        ],
        "bg_color": "#FFF5E6",
    },
    {
        "title": "花桥晚上有没有出来走走的",
        "content": (
            "每天下班就是回家躺着 周末一个人出去逛连耳机都懒得摘\n"
            "花桥有没有晚上出来走走的 不用聊什么 就走走就行\n"
            "建了个群 想来的dd我"
        ),
        "image_text": [
            ("有人吗", 120, "#2C3E50", 460),
        ],
        "bg_color": "#EBF5FB",
    },
    {
        "title": "花桥的朋友们在哪里",
        "content": (
            "之前随手发了一条 没想到真有人私信我\n"
            "建了个小群 聊着聊着发现好多人跟我一样\n"
            "都是一个人在花桥 想认识点人又不知道去哪认识\n"
            "群还有位置 私信我就好"
        ),
        "image_text": [
            ("dd我", 120, "#6C3483", 460),
        ],
        "bg_color": "#F5EEF8",
    },
]

TAGS = ["花桥", "交朋友", "找朋友", "同频的人", "花桥交友", "微信群", "花桥本地"]


def notify(title, message):
    """发送Mac桌面通知"""
    script = f'display notification "{message}" with title "{title}" sound name "Glass"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def start_mcp_server():
    """启动MCP服务（如果未运行）"""
    try:
        r = requests.post(MCP_URL, json={"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                          "params": {"protocolVersion": "2024-11-05",
                                                     "capabilities": {},
                                                     "clientInfo": {"name": "test", "version": "1"}}}, timeout=3)
        if r.status_code == 200:
            return True
    except Exception:
        pass

    print("启动MCP服务...")
    subprocess.Popen(
        [MCP_BIN, "-headless"],
        cwd=os.path.dirname(MCP_BIN),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(4)
    return True


def get_session():
    """获取MCP会话ID"""
    r = requests.post(MCP_URL, json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "daily-poster", "version": "1.0"}}
    })
    return r.headers.get("Mcp-Session-Id")


def call_tool(session_id, tool_name, arguments={}):
    """调用MCP工具"""
    r = requests.post(MCP_URL, headers={"Mcp-Session-Id": session_id}, json={
        "jsonrpc": "2.0", "id": 10, "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments}
    })
    return r.json()


def check_login(session_id):
    """检查登录状态"""
    result = call_tool(session_id, "check_login_status")
    text = result["result"]["content"][0]["text"]
    return "已登录" in text


def get_qrcode_and_notify(session_id):
    """获取二维码并保存，发送通知"""
    import base64
    result = call_tool(session_id, "get_login_qrcode")
    for item in result["result"]["content"]:
        if item["type"] == "image":
            img_data = base64.b64decode(item["data"])
            qr_path = "/tmp/xhs_login_qrcode.png"
            with open(qr_path, "wb") as f:
                f.write(img_data)
            subprocess.run(["open", qr_path])
            notify("小红书需要重新登录", "二维码已弹出，请用小红书App扫码")
            return True
    return False


def generate_image(template):
    """生成配图"""
    img = Image.new("RGB", (1080, 1080), color=template["bg_color"])
    draw = ImageDraw.Draw(img)

    # 渐变背景
    from PIL import ImageColor
    base = ImageColor.getrgb(template["bg_color"])
    for i in range(1080):
        alpha = i / 1080
        r = max(0, int(base[0] - alpha * 20))
        g = max(0, int(base[1] - alpha * 15))
        b = max(0, int(base[2] - alpha * 25))
        draw.line([(0, i), (1080, i)], fill=(r, g, b))

    # 装饰圆
    draw.ellipse([820, 40, 1060, 280], fill=(*base[:2], max(0, base[2] - 30)))
    draw.ellipse([20, 780, 200, 960], fill=(*base[:2], max(0, base[2] - 20)))

    # 写文字
    for text, size, color, y in template["image_text"]:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", size)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        x = (1080 - w) // 2
        draw.text((x, y), text, fill=color, font=font)

    img.save(IMAGE_PATH)
    print(f"配图已生成: {IMAGE_PATH}")


def publish(session_id, template):
    """发布笔记"""
    result = call_tool(session_id, "publish_content", {
        "title": template["title"],
        "content": template["content"],
        "images": [IMAGE_PATH],
        "tags": TAGS,
    })
    text = result["result"]["content"][0]["text"]
    return "发布完成" in text or "成功" in text


def main():
    print(f"=== 小红书每日自动发布 {date.today()} ===")

    # 按天选择模板（循环）
    day_index = date.today().toordinal() % len(TEMPLATES)
    template = TEMPLATES[day_index]
    print(f"今日模板: {template['title']}")

    # 启动MCP
    start_mcp_server()
    session_id = get_session()

    # 检查登录
    if not check_login(session_id):
        print("未登录，获取二维码...")
        get_qrcode_and_notify(session_id)
        notify("小红书自动发布暂停", "请扫码后重新运行脚本")
        sys.exit(1)

    print("登录状态正常")

    # 生成配图
    generate_image(template)

    # 发布
    print("正在发布...")
    session_id = get_session()  # 重新获取session
    success = publish(session_id, template)

    if success:
        print("发布成功！")
        notify("小红书发布成功 🎉", f"「{template['title']}」已发布")
    else:
        print("发布失败")
        notify("小红书发布失败", "请检查日志")


if __name__ == "__main__":
    main()
