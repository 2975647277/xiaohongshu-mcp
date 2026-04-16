#!/bin/bash
# ============================================
# 小红书每日自动发布 - Mac 一键安装脚本
# 支持 M1/M2/M3 (ARM) 和 Intel 芯片
# ============================================

set -e

echo ""
echo "======================================"
echo "  小红书自动发布 - Mac 一键安装"
echo "======================================"
echo ""

INSTALL_DIR="$HOME/xiaohongshu-mcp"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 检测芯片类型
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    BINARY="xiaohongshu-mcp-darwin-arm64"
    TARBALL="xiaohongshu-mcp-darwin-arm64.tar.gz"
    echo "✅ 检测到 Apple Silicon (M系列)"
else
    BINARY="xiaohongshu-mcp-darwin-amd64"
    TARBALL="xiaohongshu-mcp-darwin-amd64.tar.gz"
    echo "✅ 检测到 Intel 芯片"
fi

RELEASE_URL="https://github.com/xpzouying/xiaohongshu-mcp/releases/download/v2026.04.09.1645-7732044"

# 下载MCP程序
if [ ! -f "$BINARY" ]; then
    echo ""
    echo "📥 正在下载 MCP 服务..."
    curl -L "$RELEASE_URL/$TARBALL" -o "$TARBALL" --progress-bar
    tar -xzf "$TARBALL"
    rm -f "$TARBALL"
    chmod +x "$BINARY"
    echo "✅ 下载完成"
else
    echo "✅ MCP 程序已存在，跳过下载"
fi

# 安装 Python 依赖
echo ""
echo "📦 安装 Python 依赖..."
pip3 install Pillow requests --break-system-packages -q
echo "✅ 依赖安装完成"

# 复制发布脚本
echo ""
echo "📝 写入发布脚本..."
cat > "$INSTALL_DIR/daily_post.py" << 'PYTHON_SCRIPT'
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
MCP_BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xiaohongshu-mcp-darwin-arm64")
IMAGE_PATH = "/tmp/xhs_daily_post.png"

TEMPLATES = [
    {
        "title": "在花桥，找同频的人",
        "content": (
            "说真的，我已经很久没有朋友主动找我聊天了\n\n"
            "不是说我有多惨，就是突然发现——\n"
            "长大之后交朋友真的好难\n"
            "大家都很忙，都很有礼貌，但就是不亲近\n\n"
            "我最近在花桥组一个小圈子\n"
            "没有什么主题，就是想找一群\n"
            "愿意好好说话的人\n\n"
            "不卖东西、不搞事情\n"
            "就是闲聊、互相分享、偶尔吐槽\n\n"
            "感兴趣的可以私信我「进群」\n"
            "名额不多，感觉合适才拉你进来🌿"
        ),
        "image_text": [
            ("在花桥", 110, "#C0392B", 160),
            ("找到同频的人", 75, "#8B4513", 300),
            ("不卖东西  不搞事情", 42, "#795548", 440),
            ("就是想找一群", 42, "#795548", 510),
            ("愿意好好说话的人", 42, "#795548", 580),
            ("感兴趣的 私信我「进群」🌿", 38, "#A0522D", 680),
        ],
        "bg_color": "#FFF5E6",
    },
    {
        "title": "花桥｜我偷偷建了一个群",
        "content": (
            "我偷偷建了一个群\n\n"
            "里面的人都有点意思\n"
            "有人凌晨三点发美食，有人分享从没人听过的歌\n"
            "有人失恋了发一句「还好有你们」大家就都陪着聊\n\n"
            "没有人在里面卖东西\n"
            "没有人每天发早安图\n"
            "就是一群花桥普通人，互相陪着\n\n"
            "想进来看看的，私信我\n"
            "就说「我想看看」就好🌙"
        ),
        "image_text": [
            ("我偷偷", 90, "#2C3E50", 140),
            ("建了一个群", 90, "#2C3E50", 250),
            ("里面的人都有点意思", 44, "#566573", 400),
            ("花桥 · 普通人的小圈子", 38, "#7F8C8D", 520),
            ("私信我「我想看看」🌙", 40, "#1A5276", 640),
        ],
        "bg_color": "#EBF5FB",
    },
    {
        "title": "花桥的你，有没有这种感觉",
        "content": (
            "你有没有过这种感觉\n\n"
            "朋友圈发了东西没人评论\n"
            "有话想说但不知道发给谁\n"
            "不是没有朋友，就是没有那种\n"
            "「随时可以找」的朋友\n\n"
            "我在花桥找这样的人，一起建一个群\n"
            "大家都是普通人，没有人设，不用表演\n"
            "累了可以说，开心了可以分享\n\n"
            "私信我「进群」就好\n"
            "进来觉得不合适随时可以退，不尬的🤍"
        ),
        "image_text": [
            ("有没有这种感觉", 72, "#6C3483", 150),
            ("发了东西没人评论", 44, "#7D3C98", 300),
            ("有话想说不知道发给谁", 40, "#7D3C98", 365),
            ("花桥 · 找个随时可以找的人", 38, "#9B59B6", 470),
            ("私信「进群」不尬的🤍", 42, "#5B2C6F", 600),
        ],
        "bg_color": "#F5EEF8",
    },
]

TAGS = ["花桥", "交朋友", "找朋友", "同频的人", "花桥交友", "微信群", "花桥本地"]


def notify(title, message):
    script = f'display notification "{message}" with title "{title}" sound name "Glass"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def start_mcp_server():
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
    subprocess.Popen([MCP_BIN, "-headless"], cwd=os.path.dirname(MCP_BIN),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    return True


def get_session():
    r = requests.post(MCP_URL, json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "daily-poster", "version": "1.0"}}
    })
    return r.headers.get("Mcp-Session-Id")


def call_tool(session_id, tool_name, arguments={}):
    r = requests.post(MCP_URL, headers={"Mcp-Session-Id": session_id}, json={
        "jsonrpc": "2.0", "id": 10, "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments}
    })
    return r.json()


def check_login(session_id):
    result = call_tool(session_id, "check_login_status")
    return "已登录" in result["result"]["content"][0]["text"]


def get_qrcode_and_notify(session_id):
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
    img = Image.new("RGB", (1080, 1080), color=template["bg_color"])
    draw = ImageDraw.Draw(img)
    from PIL import ImageColor
    base = ImageColor.getrgb(template["bg_color"])
    for i in range(1080):
        alpha = i / 1080
        r = max(0, int(base[0] - alpha * 20))
        g = max(0, int(base[1] - alpha * 15))
        b = max(0, int(base[2] - alpha * 25))
        draw.line([(0, i), (1080, i)], fill=(r, g, b))
    draw.ellipse([820, 40, 1060, 280], fill=(*base[:2], max(0, base[2] - 30)))
    draw.ellipse([20, 780, 200, 960], fill=(*base[:2], max(0, base[2] - 20)))
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


def publish(session_id, template):
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
    day_index = date.today().toordinal() % len(TEMPLATES)
    template = TEMPLATES[day_index]
    print(f"今日模板: {template['title']}")
    start_mcp_server()
    session_id = get_session()
    if not check_login(session_id):
        print("未登录，获取二维码...")
        get_qrcode_and_notify(session_id)
        notify("小红书自动发布暂停", "请扫码后重新运行脚本")
        sys.exit(1)
    print("登录状态正常")
    generate_image(template)
    print("正在发布...")
    session_id = get_session()
    success = publish(session_id, template)
    if success:
        print("发布成功！")
        notify("小红书发布成功 🎉", f"「{template['title']}」已发布")
    else:
        print("发布失败")
        notify("小红书发布失败", "请检查日志")


if __name__ == "__main__":
    main()
PYTHON_SCRIPT

echo "✅ 发布脚本已写入"

# 设置定时任务（每天21:30）
echo ""
echo "⏰ 设置每天 21:30 定时发布..."
(crontab -l 2>/dev/null | grep -v "daily_post.py"; echo "30 21 * * * /usr/bin/python3 $INSTALL_DIR/daily_post.py >> /tmp/xhs_daily.log 2>&1") | crontab -
echo "✅ 定时任务设置完成"

# 首次登录
echo ""
echo "======================================"
echo "  最后一步：扫码登录小红书"
echo "======================================"
echo ""
echo "正在启动服务并获取登录二维码..."
"$INSTALL_DIR/$BINARY" -headless &
sleep 4
python3 "$INSTALL_DIR/app.py"

echo ""
echo "======================================"
echo "  安装完成！"
echo "  每天 21:30 将自动发布笔记"
echo "  日志查看: cat /tmp/xhs_daily.log"
echo "======================================"
