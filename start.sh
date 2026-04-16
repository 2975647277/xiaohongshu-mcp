#!/bin/bash
# 小红书 MCP 工具箱 - 统一启动脚本
# 用法:
#   ./start.sh mcp      启动 MCP 服务 (端口 18060)
#   ./start.sh web      启动 Web UI  (端口 7788)
#   ./start.sh daily    执行每日自动发布
#   ./start.sh all      启动 MCP + Web UI

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查 Python 环境
check_python() {
    if [ -d "$DIR/.venv312/bin" ]; then
        PYTHON="$DIR/.venv312/bin/python"
    elif [ -d "$DIR/.venv/bin" ]; then
        PYTHON="$DIR/.venv/bin/python"
    elif command -v python3 &>/dev/null; then
        PYTHON="python3"
    else
        echo -e "${RED}错误: 未找到 Python，请先安装 Python 3.10+${NC}"
        exit 1
    fi
    echo -e "${GREEN}Python: $PYTHON${NC}"
}

# 安装依赖
install_deps() {
    check_python
    echo -e "${YELLOW}安装 Python 依赖...${NC}"
    $PYTHON -m pip install flask openai pillow requests playwright -q
    $PYTHON -m playwright install chromium 2>/dev/null || true
    echo -e "${GREEN}依赖安装完成${NC}"
}

# 启动 MCP 服务
start_mcp() {
    local BIN="$DIR/xiaohongshu-mcp-darwin-arm64"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        BIN="$DIR/xiaohongshu-mcp-windows-amd64.exe"
    fi
    if [ ! -f "$BIN" ]; then
        echo -e "${RED}错误: 未找到 MCP 二进制文件: $BIN${NC}"
        echo "请从 Release 页面下载对应平台的二进制文件"
        exit 1
    fi
    echo -e "${GREEN}启动 MCP 服务 (端口 18060)...${NC}"
    chmod +x "$BIN"
    "$BIN" -headless
}

# 启动 Web UI
start_web() {
    check_python
    echo -e "${GREEN}启动 Web UI (端口 7788)...${NC}"
    echo -e "访问 ${YELLOW}http://localhost:7788${NC}"
    $PYTHON app.py
}

# 每日自动发布
run_daily() {
    check_python
    echo -e "${GREEN}执行每日自动发布...${NC}"
    $PYTHON daily_post.py
}

# 启动全部 (MCP 后台 + Web UI 前台)
start_all() {
    local BIN="$DIR/xiaohongshu-mcp-darwin-arm64"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        BIN="$DIR/xiaohongshu-mcp-windows-amd64.exe"
    fi
    if [ -f "$BIN" ]; then
        echo -e "${GREEN}后台启动 MCP 服务...${NC}"
        chmod +x "$BIN"
        "$BIN" -headless &
        MCP_PID=$!
        sleep 2
        echo -e "${GREEN}MCP 服务已启动 (PID: $MCP_PID)${NC}"
    fi
    start_web
}

# 主入口
case "${1:-help}" in
    mcp)
        start_mcp
        ;;
    web)
        start_web
        ;;
    daily)
        run_daily
        ;;
    all)
        start_all
        ;;
    install)
        install_deps
        ;;
    *)
        echo "小红书 MCP 工具箱"
        echo ""
        echo "用法: ./start.sh <命令>"
        echo ""
        echo "命令:"
        echo "  mcp       启动 MCP 服务 (端口 18060)"
        echo "  web       启动 Web UI  (端口 7788)"
        echo "  daily     执行每日自动发布"
        echo "  all       启动 MCP 服务 + Web UI"
        echo "  install   安装 Python 依赖"
        echo ""
        echo "示例:"
        echo "  ./start.sh all       # 一键启动所有服务"
        echo "  ./start.sh web       # 仅启动 Web 界面"
        echo "  ./start.sh daily     # 手动触发一次发布"
        ;;
esac
