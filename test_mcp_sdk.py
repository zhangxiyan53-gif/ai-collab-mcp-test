"""MCP SDK 严格测试（v3：无认证纯只读）
- 所有请求带正确 MCP 头
- 验证真实 JSON-RPC 错误码，不只看 HTTP 状态
- 任何未预期的异常 = FAIL，不判 PASS
"""
import asyncio
import json
import sys
import urllib.request
import urllib.error

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18791
URL = f"http://127.0.0.1:{PORT}/mcp"

MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "MCP-Protocol-Version": "2026-07-28",
}

results = []


def check(name, ok, detail=""):
    results.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def post_raw(body: bytes) -> tuple[int, dict | None]:
    """原始 POST，返回 (http_status, 解析后的 JSON 或 None)。"""
    req = urllib.request.Request(URL, data=body, headers=MCP_HEADERS)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None


async def main():
    from mcp.client.streamable_http import streamable_http_client as shc
    from mcp import ClientSession
    import httpx2 as httpx

    # --- 1. SDK 客户端标准流程 ---
    async with httpx.AsyncClient(timeout=15, trust_env=False) as hc:
        async with shc(URL, http_client=hc) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                check("initialize 协议协商",
                      init.server_info.name == "ai-collab-center-mcp-test",
                      init.server_info.name)
                tools = await session.list_tools()
                names = [t.name for t in tools.tools]
                check("tools/list 仅 get_status",
                      names == ["get_status"], str(names))
                r = await session.call_tool("get_status", {})
                d = json.loads(r.content[0].text)
                check("get_status 返回固定无敏感信息",
                      d.get("mode") == "test-only-readonly"
                      and "server" in d, str(d))

    # --- 2. 异常输入：验证真实 JSON-RPC 错误码 ---
    cases = [
        (b"[1,2,3]", -32600, "顶层数组→Invalid Request"),
        (b"not json at all", -32700, "非JSON→Parse Error"),
        (b'{"jsonrpc":"2.0"}', -32600, "缺method→Invalid Request"),
        # SDK 2.x 要求 params._meta 带协议信封，缺失判 -32602（符合严格校验）
        (b'{"jsonrpc":"2.0","id":1,"method":"nope"}', -32602,
         "缺_meta信封→Invalid Params"),
    ]
    for body, want_code, label in cases:
        status, resp = post_raw(body)
        got_code = (resp or {}).get("error", {}).get("code")
        is_jsonrpc = (resp or {}).get("jsonrpc") == "2.0"
        ok = (got_code == want_code and is_jsonrpc
              and 400 <= status < 500)
        check(f"异常输入 {label}",
              ok, f"HTTP {status}, code={got_code}")

    # --- 3. 异常后服务器存活 ---
    async with httpx.AsyncClient(timeout=15, trust_env=False) as hc:
        async with shc(URL, http_client=hc) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                r = await session.call_tool("get_status", {})
                check("异常输入后服务器仍存活",
                      "ai-collab-center-mcp-test" in r.content[0].text)

    n_ok = sum(1 for ok in results if ok[1])
    print(f"\n{n_ok}/{len(results)} 通过")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    # 不吞异常：任何未预期错误直接抛栈，= FAIL
    sys.exit(asyncio.run(main()))
