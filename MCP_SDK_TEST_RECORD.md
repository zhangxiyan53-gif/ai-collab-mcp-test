# 本地复现步骤（MCP SDK v3）

## 启动

```bash
cd <解压后的项目文件夹>
# 首次：创建虚拟环境并安装锁定版本
python3 -m venv mcp_venv
./mcp_venv/bin/pip install -r requirements-mcp.txt
# 启动（测试用端口 18791，避免冲突）
PORT=18791 ./mcp_venv/bin/python mcp_sdk_server.py
```

期望输出：
```
MCP SDK server on 0.0.0.0:18791
INFO:     Uvicorn running on http://0.0.0.0:18791
```

## 测试

```bash
# 新终端
cd <解压后的项目文件夹>
./mcp_venv/bin/python test_mcp_sdk.py 18791
```

期望输出：8/8 通过
```
[PASS] initialize 协议协商
[PASS] tools/list 仅 get_status
[PASS] get_status 返回固定无敏感信息
[PASS] 异常输入 顶层数组→Invalid Request
[PASS] 异常输入 非JSON→Parse Error
[PASS] 异常输入 缺method→Invalid Request
[PASS] 异常输入 缺_meta信封→Invalid Params
[PASS] 异常输入后服务器仍存活
8/8 通过
```

## 停止

```bash
# 找到进程并终止
在启动服务器的终端按 Ctrl+C
# 若在后台运行，则找到实际进程 PID 后 kill PID
```

## 实测记录（2026-10-17 第三轮修复后）

### TransportSecuritySettings（新增）

| 测试 | 结果 |
|---|---|
| 合法 Host（127.0.0.1） | ✅ 通过（HTTP 400 是 ping 方法缺 _meta，属正常） |
| 非法 Host（evil.com） | ✅ 拒绝（HTTP 421 "Invalid Host header"） |
| 合法 Origin（https://chatgpt.com） | ✅ 通过 |
| 非法 Origin（https://evil.com） | ✅ 拒绝（HTTP 403 "Invalid Origin header"） |
| 无 Origin（非浏览器客户端） | ✅ 通过（符合规范） |

配置：`allowed_hosts` 含 `127.0.0.1:*`、`localhost:*` + Render 的
`RENDER_EXTERNAL_HOSTNAME`；`allowed_origins` 含 chatgpt.com /
chat.openai.com。

### 原有 8 项测试

8/8 通过（见上）。

依赖锁定：`mcp==2.3.0`（实测版本）

### 本轮 4 项修改

1. TransportSecuritySettings：Host 白名单 + Origin 规则（见上表）
2. RENDER_DEPLOY.md：curl 示例改为官方 SDK 客户端验证
3. `git init -b main`（避免默认分支不一致）
4. render.yaml：删除未使用的 MCP_BEARER_TOKEN
