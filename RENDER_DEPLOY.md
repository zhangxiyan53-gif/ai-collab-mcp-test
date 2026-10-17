# Render 免费部署操作步骤（MCP SDK v3：无认证纯只读）

> ⚠️ 等 ChatGPT 检查通过后再执行。用户需注册 Render 账号（免费）。

## 部署文件

| 文件 | 用途 |
|---|---|
| `mcp_sdk_server.py` | MCP 服务器（官方 SDK，无认证，只读） |
| `requirements-mcp.txt` | 依赖（`mcp==2.3.0` 锁定） |
| `render.yaml` | Render 服务配置 |

## 前置要求

- Render 账号（https://dashboard.render.com/register，免费）
- 本项目的 Git 仓库（只推送上面 3 个文件）

## 部署步骤

### 1. 推送代码到 Git

```bash
git init -b main
git add mcp_sdk_server.py requirements-mcp.txt render.yaml
git commit -m "MCP SDK v3 readonly"
git remote add origin <你的仓库地址>
git push -u origin main
```

> 只推送这 3 个文件。不要推送测试脚本、venv、用户个人文件。

### 2. 在 Render 创建 Web Service

1. 登录 https://dashboard.render.com
2. 点 **New +** → **Web Service**
3. 选择 **Build and deploy from a Git repository** → 连接你的仓库
4. 配置：
   | 字段 | 值 |
   |---|---|
   | Name | `ai-collab-mcp-test` |
   | Region | Oregon（离加州最近） |
   | Branch | `main` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements-mcp.txt` |
   | Start Command | `python mcp_sdk_server.py` |
   | Plan | **Free** |
5. 环境变量：无需设置（PORT 由 Render 自动注入）
6. 点 **Create Web Service**，等待部署完成（约2-3分钟）
7. 记下分配的公网地址，例如 `https://ai-collab-mcp-test.onrender.com`

### 3. 验证部署

用官方 SDK 客户端验证（推荐，符合 MCP 2026-07-28 协议）：

```bash
pip install "mcp==2.3.0"
python - <<'EOF'
import asyncio, json
async def main():
    from mcp.client.streamable_http import streamable_http_client as shc
    from mcp import ClientSession
    import httpx2
    url = "https://ai-collab-mcp-test.onrender.com/mcp"  # 换成你的地址
    async with httpx2.AsyncClient(timeout=30, trust_env=False) as hc:
        async with shc(url, http_client=hc) as (read, write):
            async with ClientSession(read, write) as s:
                await s.initialize()
                r = await s.call_tool("get_status", {})
                print(r.content[0].text)
asyncio.run(main())
EOF
```

期望输出包含 `"server": "ai-collab-center-mcp-test"`。

### 4. 在 ChatGPT 中添加 MCP 服务器

1. 浏览器打开 chatgpt.com → 头像 → Settings
2. Apps（或 Apps & Connectors）→ 确认 Developer Mode 已打开
3. 点 Create（或 +）→ Add custom MCP server
4. 填写：
   | 字段 | 值 |
   |---|---|
   | Name | `AI协作中心测试` |
   | MCP Server URL | `https://ai-collab-mcp-test.onrender.com/mcp` |
   | Authentication | None（本轮无认证，只读无敏感信息） |
5. ChatGPT 发现工具列表（应只有 `get_status`）
6. 新对话输入 @ 选择该工具，试调用 `get_status`

### 5. 成功标准（本轮唯一目标）

- [ ] ChatGPT 能列出 `get_status` 工具
- [ ] 在 ChatGPT 中调用 `get_status` 返回状态 JSON
- [ ] 以上两步在 ChatGPT 界面内完成，无人工复制粘贴

## Render Free 限制（已知）

| 限制 | 影响 | 对策 |
|---|---|---|
| 15分钟无请求自动休眠 | 首次调用延迟 ~30秒（冷启动） | 测试前先发一次 initialize 唤醒 |
| 每月750小时 | 足够测试用 | 超出会停机 |
| 文件系统临时 | 重启后数据丢失 | 本轮无状态，不存数据 |
| 无 SLA | 可能随时中断 | 仅用于测试 |

## 费用

| 项目 | 费用 |
|---|---|
| Render Free Web Service | $0 |
| ChatGPT Plus（已有） | $0 |
| **总计** | **$0** |

## 安全说明（本轮）

- 无认证：get_status 只返回固定无敏感信息（服务器名、版本号）
- 无写工具：`create_test_task` 已彻底移除，tools/list 不暴露
- 不连接真实任务队列
- 云端不存用户个人文件、密码、真实业务资料
