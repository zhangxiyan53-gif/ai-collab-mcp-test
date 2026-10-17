"""AI协作中心 MCP 测试服务器 v3（官方 MCP Python SDK）
Round 1：无认证、纯只读，仅 get_status。

设计说明（经 ChatGPT 审查）：
- get_status 只返回固定无敏感信息，无需认证
- 不连接任何真实任务队列
- 不使用虚假 OAuth 发行方/资源地址
- 写工具彻底移除（非禁用，是不存在）

运行：
    pip install -r requirements-mcp.txt
    python mcp_sdk_server.py
环境变量：
    PORT - 监听端口（Render 自动设置，默认 8000）
    HOST - 监听地址（默认 0.0.0.0，符合 Render 要求）
"""
import os

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

mcp = MCPServer(
    name="ai-collab-center-mcp-test",
    version="0.3",
)


def build_transport_security() -> TransportSecuritySettings:
    """Host 白名单 + Origin 规则。

    - Render 部署时用 RENDER_EXTERNAL_HOSTNAME（如 xxx.onrender.com）
    - 本地测试时允许 127.0.0.1 / localhost
    - Origin 允许 ChatGPT 网页版
    """
    hosts = ["127.0.0.1", "127.0.0.1:*", "localhost", "localhost:*"]
    render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if render_host:
        base = render_host.split(":")[0]
        hosts.append(base)
        hosts.append(f"{base}:*")
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=[
            "https://chatgpt.com",
            "https://chat.openai.com",
        ],
    )


@mcp.tool()
def get_status() -> dict:
    """获取 AI协作中心测试服务器状态（只读，无副作用）。"""
    return {
        "server": "ai-collab-center-mcp-test",
        "version": "0.3",
        "mode": "test-only-readonly",
        "note": "测试服务器，未连接真实任务队列",
    }


if __name__ == "__main__":
    print(f"MCP SDK server on {HOST}:{PORT}")
    ts = build_transport_security()
    print(f"allowed_hosts={ts.allowed_hosts}")
    mcp.run(transport="streamable-http", host=HOST, port=PORT,
            transport_security=ts)
