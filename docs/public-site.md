# Public Site

公开站的定位是：

```text
Landing + 可用 Demo + 自托管引导 + 隐私边界说明
```

它不是完整 SaaS，也不是远程 AI 论文生成入口。

## 信息架构

首页按以下顺序组织：

1. Hero: 说明产品名称、对象、价值与公开边界
2. Quick Export: 上传 `.docx` 或粘贴正文，预检后导出规范化 Word
3. Demo Flow: 上传、结构预检、合规导出、进入 Workbench
4. Workbench Preview: 项目空间、文件库、Proposal Queue、版本历史、Provider 设置
5. Privacy Boundary: 非官方、非代写、不承诺查重率、远程 AI 默认关闭
6. Self-host: Docker Compose、Access Code、Local-first、Ollama ready
7. Roadmap: Public Site、Agent Runtime、Comment Resolver、Project Package、OCR / PDF Provider

## 公开 Demo 边界

允许：

- 上传 `.docx`
- 粘贴文本
- 快速预检
- 导出规范化 `.docx`
- 查看 Workbench demo preview

禁止：

- 匿名远程 LLM Provider
- 真实论文内容发送到 AI
- 无限长任务
- 匿名用户管理 Provider 设置

## 验收

- 访问首页后 30 秒内能理解产品价值
- 快速导出入口仍然可直接使用
- 首页明确说明公开站不启用远程 AI
- Workbench 有无需真实论文的安全预览
- 自托管路径清楚
