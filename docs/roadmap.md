# Roadmap

vNext 的顺序遵循一个原则：先补公开可信度，再补运行时复杂度。

## v0.3.0-public-site

目标：让项目看起来、试起来、读起来都像成熟开源产品。

交付：

- Landing page
- README 改版
- 产品截图与 demo flow
- Privacy module
- Workbench demo project
- 文档重组

验收：

- 公开站可访问
- 快速导出可用
- 公开站不启用远程 AI
- README 第一屏包含 Demo、Quick Start、Privacy、Roadmap

## v0.4.0-agent-runtime

目标：从同步 parse job 升级为可观察任务系统。

交付：

- `thesis_jobs`
- `job_events`
- SSE 实时事件
- cancel / retry
- stale job detection
- progress UI

验收：

- 前端实时看到 parse / audit / export 状态
- job 可取消
- 失败可重试
- 服务重启后 stale job 可标记失败

## v0.5.0-comment-resolver

目标：支持老师批注文档解析和修订建议。

交付：

- CommentDocxParser
- CommentPanel
- CommentResolverAgent
- RevisionDiffView
- located / unlocated comments queue

验收：

- 上传批注 `.docx` 后显示批注列表
- 可定位到 block 的批注生成修订 Proposal
- 未定位批注进入待处理队列
- 接受 Proposal 后生成新版本

## v0.6.0-project-package

目标：实现 `.scnu-thesis.zip`，支持跨环境迁移。

项目包包含：

- `manifest.json`
- `project.json`
- `source-ledger.json`
- `versions/*.json`
- `proposals.json`
- `approvals.json`
- `issues.json`
- `exports/manifest.json`
- `audit-logs.json`
- `rule-sources.json`

项目包不包含：

- API key
- Provider secrets
- 本地缓存
- 未授权远程日志

## v0.7.0-provider-runtime

目标：接入真实本地 / 远程模型，但保持项目级授权和 Proposal-only 输出。

支持顺序：

1. Ollama 本地
2. OpenAI
3. Gemini
4. DeepSeek
5. MiniMax
6. MinerU / local OCR

验收：

- 本地 Ollama 可生成 Proposal
- 远程 Provider 需项目级授权
- Agent 输出只进入 Draft / Proposal
- 不直接修改当前版本
