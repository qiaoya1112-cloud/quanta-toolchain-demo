# Codex Reconnecting 排查与恢复记录

排查日期：2026-10-10，时间均为 Asia/Shanghai。

结论：已确认故障发生在 Codex 与 OpenAI 的连接层，且有后端域名解析失败的直接证据。已执行 Clash 内核重启并完成短时连接复测，当前恢复。尚未通过备用网络对照或长时间任务验证，不能宣称永久修复或将全部故障归因于代理。

## 直接证据

- 当前排查任务的模型日志记录 13 次连接重试，最后一次为 15:03:10：`Connection failed: error sending request`。
- 桌面端有 WebSocket 异常关闭（1006）、心跳超时与连接打开超时。
- 15:06:16 桌面日志直接记录：`getaddrinfo ENOTFOUND codex-cloud-backend.chatgpt.com`。
- 15:06:24 模型列表刷新仍出现 `request timed out`。
- 系统查询确认 OpenAI 域名解析为 `198.18.0.0/15` 范围的 Fake-IP，并经 `utun4` 隧道转发。
- Clash 连接页面确认 Codex 后端、ChatGPT 与 WebSocket 域名使用同一个 ChatGPT 策略组和同一代理节点。用户确认没有备用线路。
- 本机还运行企业网络客户端；仅凭同时运行不能判断其导致故障。
- 本地作业中心页面 HTTP 200，约 0.033 秒返回。应用页面正常不等于 Codex 连接稳定。

## 已执行恢复

15:25:37–15:25:38，通过 Clash Verge 的“重启内核”操作完成恢复。

应用日志记录 `Service -> NotRunning -> Service`。内核 PID 从 48280 更换为 77827，确认发生实际重启。

没有修改仓库业务代码、Codex 认证信息、企业网络客户端或安全设置；没有新增代理线路。

## 恢复后验证

15:27:07–15:27:57，进行 6 轮采样：

| 检查 | 结果 |
| --- | --- |
| chatgpt.com DNS | 6/6 成功 |
| codex-cloud-backend.chatgpt.com DNS | 6/6 成功 |
| codex-cloud-environments.chatgpt.com DNS | 6/6 成功 |
| ws.chatgpt.com DNS | 6/6 成功 |
| ChatGPT HTTPS/TLS | 6/6 成功建立连接 |
| Codex 后端 HTTPS/TLS | 6/6 成功建立连接 |
| 采样期间新增模型重试或模型列表错误 | 0 |

HTTPS 使用无凭据请求，返回 HTTP 403。它说明测试时 DNS/TCP/TLS 可达，不代表认证请求通过，也不能证明完整模型流或 WebSocket 长连接稳定。

详细采样结果见同目录 `codex-reconnecting-verification.json`。

## 尚未确定的部分

域名解析失败的上游原因仍不确定；可能涉及本地 DNS/隧道状态、代理线路或其他网络环节。重启是恢复措施，短时成功不能证明因果关系，也不能保证不再复发。

若实际任务再次出现 Reconnecting，应对照新的错误时间检查同一后端域名的解析与代理日志。出现 ENOTFOUND 时优先排查 DNS/隧道；解析正常而连接仍重置时，再排查线路、代理内核与上游服务。需要可用备用线路或网络维护方协助才能进一步隔离原因。

官方日志位置与恢复说明参考：[OpenAI 官方故障排查文档](https://learn.chatgpt.com/docs/reference/troubleshooting)。原始日志留在本机，本记录未包含凭据或对话正文。
