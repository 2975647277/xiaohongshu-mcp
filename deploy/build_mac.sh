#!/bin/bash
# 打包成 Mac .app，双击直接运行，不需要安装 Python
set -e

echo "📦 开始打包 Mac 应用..."
INSTALL_DIR="$HOME/xiaohongshu-mcp"
cd "$INSTALL_DIR"

/usr/bin/python3 -m pip install pyinstaller -q

/Users/heyongzhe/Library/Python/3.9/bin/pyinstaller \
  --name "小红书AI发布助手" \
  --onefile \
  --windowed \
  --add-data "templates:templates" \
  --add-data "static:static" \
  --hidden-import flask \
  --hidden-import anthropic \
  --hidden-import PIL \
  --hidden-import requests \
  app.py

echo ""
echo "✅ 打包完成！"
echo "   应用位置: $INSTALL_DIR/dist/小红书AI发布助手"
echo "   双击即可运行，无需安装 Python"
open "$INSTALL_DIR/dist/"
