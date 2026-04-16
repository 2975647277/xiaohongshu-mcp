<div align="center">

# <img src="https://www.xiaohongshu.com/favicon.ico" width="28"> 小红书 MCP Server

**AI 驱动的小红书自动化工具 | 生成 · 发布 · 管理 一站式搞定**

[![Release](https://img.shields.io/github/v/release/2975647277/xiaohongshu-mcp?style=flat-square&color=ff2442)](https://github.com/2975647277/xiaohongshu-mcp/releases)
[![License](https://img.shields.io/github/license/2975647277/xiaohongshu-mcp?style=flat-square&color=blue)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Protocol-blueviolet?style=flat-square)](https://modelcontextprotocol.io)
[![Stars](https://img.shields.io/github/stars/2975647277/xiaohongshu-mcp?style=flat-square&color=yellow)](https://github.com/2975647277/xiaohongshu-mcp/stargazers)

<br>

<img src="docs/webui-preview.png" width="750">

<sub>Web UI 界面 — 输入主题 → AI 生成拟人化文案 + 封面 → 实时预览 → 一键发布</sub>

</div>

---

## 亮点

<table>
<tr>
<td width="50%">

**🤖 AI 拟人化内容生成**

不是模板填空，而是真正像人写的。研究了上千条爆款笔记的语气和节奏，生成的文案像发朋友圈一样自然。

</td>
<td width="50%">

**🎨 极简封面自动生成**

一句话钩子 + 莫兰迪配色，告别花里胡哨。Playwright 渲染 HTML，像素级精确。

<img src="docs/cover-example.png" width="160">

</td>
</tr>
<tr>
<td width="50%">

**🔌 MCP 协议接入**

标准 MCP Server，接入 Claude Desktop / Cursor / 任何 MCP 客户端，用自然语言操控小红书。

</td>
<td width="50%">

**📱 多端支持**

Web UI + 移动端 App + 命令行 + 定时任务，一套代码覆盖所有场景。

</td>
</tr>
</table>

## 功能一览

| 能力 | 说明 |
|------|------|
| 扫码登录 | 小红书二维码登录，Cookie 自动管理 |
| AI 生成文案 | 支持任意 LLM（OpenAI / Claude / 自定义），拟人化口语风格 |
| AI 生成封面 | HTML → 截图，极简钩子风格，自动配色 |
| 发布图文笔记 | 标题 + 正文 + 图片 + 标签，一键发布 |
| 发布视频笔记 | 支持视频上传发布 |
| 每日自动发布 | 3 套模板按天轮换，Cookie 过期 Mac 通知 |
| 搜索 / 详情 | 搜索笔记、查看笔记详情、查看用户主页 |
| 互动操作 | 点赞、收藏、评论、回复评论 |

## 使用方式

### 方式一：Web UI（推荐）

```bash
./start.sh all    # 一键启动 MCP 服务 + Web UI
```

打开 `http://localhost:7788`，填入 API Key → 输入主题 → 生成 → 发布

### 方式二：MCP 客户端

启动 MCP 服务后，在 AI 客户端中配置：

<details>
<summary><b>Claude Desktop / Claude Code</b></summary>

编辑 `~/.claude.json`：

```json
{
  "mcpServers": {
    "xiaohongshu": {
      "type": "http",
      "url": "http://localhost:18060/mcp"
    }
  }
}
```

</details>

<details>
<summary><b>Cursor</b></summary>

编辑 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "xiaohongshu": {
      "url": "http://localhost:18060/mcp"
    }
  }
}
```

</details>

### 方式三：每日自动发布

```bash
./start.sh daily   # 手动执行一次

# 设置 Cron 定时任务（每天 12:00）
0 12 * * * cd /path/to/xiaohongshu-mcp && ./start.sh daily >> /tmp/xhs_daily.log 2>&1
```

### 方式四：移动端

`android-app/` 为 Capacitor 项目，可打包为 Android / iOS App，前端直接调用 AI API，无需后端。

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/2975647277/xiaohongshu-mcp.git
cd xiaohongshu-mcp

# 2. 安装依赖（需要 Python 3.10+）
./start.sh install

# 3. 下载 MCP 二进制文件（从 Release 页面）
# macOS ARM:  xiaohongshu-mcp-darwin-arm64
# Windows:    xiaohongshu-mcp-windows-amd64.exe

# 4. 一键启动
./start.sh all
```

> 首次使用需要用小红书 App 扫码登录，登录后 Cookie 自动保存。

## 启动命令

| 命令 | 说明 |
|------|------|
| `./start.sh all` | 启动 MCP 服务 + Web UI |
| `./start.sh mcp` | 仅启动 MCP 服务（端口 18060） |
| `./start.sh web` | 仅启动 Web UI（端口 7788） |
| `./start.sh daily` | 执行一次每日自动发布 |
| `./start.sh install` | 安装 Python 依赖 |

## 配置

首次启动后在 Web UI 顶部展开「API 配置」：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| API Key | LLM API 密钥 | `sk-xxx` |
| Base URL | API 地址 | `https://api.openai.com/v1` |
| Model | 模型名称 | `gpt-4o` / `claude-sonnet-4-6` |
| 坐标 | 地理位置关键词 | `花桥` |

> 配置保存在本地 `config.json`，不会上传。

## MCP 工具列表

<details>
<summary>展开查看全部 13 个工具</summary>

| 工具 | 说明 |
|------|------|
| `check_login_status` | 检查登录状态 |
| `get_login_qrcode` | 获取登录二维码 |
| `delete_cookies` | 清除登录 Cookie |
| `publish_content` | 发布图文笔记 |
| `publish_with_video` | 发布视频笔记 |
| `search_feeds` | 搜索笔记 |
| `list_feeds` | 获取笔记列表 |
| `get_feed_detail` | 获取笔记详情 |
| `like_feed` | 点赞笔记 |
| `favorite_feed` | 收藏笔记 |
| `post_comment_to_feed` | 评论笔记 |
| `reply_comment_in_feed` | 回复评论 |
| `user_profile` | 查看用户主页 |

</details>

## 项目结构

```
xiaohongshu-mcp/
├── start.sh                       # 统一启动脚本
├── app.py                         # Flask Web UI + AI 生成
├── daily_post.py                  # 每日自动发布
├── xiaohongshu-mcp-darwin-arm64   # MCP 服务二进制
├── xiaohongshu-login-darwin-arm64 # 登录服务二进制
├── templates/index.html           # Web UI 页面
├── static/                        # 封面模板 + 静态资源
├── android-app/                   # 移动端 Capacitor 项目
│   └── www/index.html
└── deploy/                        # 构建部署脚本
```

## 系统要求

| 项目 | 要求 |
|------|------|
| Python | 3.10+ |
| 系统 | macOS / Windows |
| 浏览器引擎 | Playwright + Chromium（封面截图） |
| 小红书 App | 扫码登录用 |

## Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=2975647277/xiaohongshu-mcp&type=Date)](https://star-history.com/#2975647277/xiaohongshu-mcp&Date)

</div>

## 免责声明

- 本项目仅供学习和研究使用
- 使用本工具产生的一切后果由使用者自行承担
- 请遵守小红书平台的使用规则和服务条款
- 不得用于任何违法违规用途

## 联系方式

<div align="center">

| 打赏支持 | 交流群 | 个人微信 |
|:---:|:---:|:---:|
| <img src="docs/reward.jpg" width="200"> | <img src="docs/group.jpg" width="200"> | <img src="docs/wechat.jpg" width="200"> |
| 觉得好用可以支持一下 | 问题反馈 / 功能建议 | 备注「小红书MCP」 |

</div>

## License

MIT
