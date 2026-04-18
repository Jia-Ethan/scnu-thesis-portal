# Architecture

当前架构保留 Python 文档处理优势，同时把 Workbench 作为可演进的项目空间。

## 边界

```text
web/
  public landing
  quick export flow
  workbench UI

backend/app/
  parse registry
  precheck
  export registry
  workbench API
  provider metadata

backend/story2paper/
  experimental multi-agent research code
```

`backend/story2paper/` 不进入默认公开主线。vNext Agent Runtime 会在 `backend/app/agents/` 与 `backend/app/providers/` 下逐步实现。

## 当前主链路

```text
Upload Materials
→ Parse Sources
→ Build NormalizedThesis
→ Run Precheck
→ Export DOCX
```

Workbench 链路：

```text
Project
→ File Library
→ Parse Job
→ Baseline Version
→ Issue Ledger / Proposal Queue
→ User Approval
→ New Version
→ Export History
```

## vNext 目标链路

```text
Director
→ Agent
→ Action
→ Draft / Proposal
→ Approval
→ Version
→ Export / Package
```

事件类型目标：

```text
run_started
director_decision
agent_start
text_delta
action
source_found
proposal_created
draft_created
approval_required
agent_end
run_completed
run_failed
```

Agent run 状态目标：

```text
queued
running
waiting_for_user
completed
failed
cancelled
stale
```

## 数据原则

- 当前版本是用户确认后的版本
- Proposal 不直接修改版本
- Provider key 不返回前端
- 规则来源和 source ledger 必须可追溯
- 项目包不包含 secrets
