const demoFiles = [
  { name: "毕业论文初稿.docx", meta: "docx · 186 KB · 已解析" },
  { name: "指导老师批注.docx", meta: "commented docx · 92 KB · 待闭环" },
  { name: "参考文献清单.bib", meta: "reference · 14 KB · 仅整理不补造" },
];

const demoProposals = [
  {
    status: "pending",
    title: "中文摘要缺少研究方法描述",
    body: "建议补充研究对象、方法和主要结论。候选内容不会直接写入版本。",
    risk: "需用户确认是否与真实研究材料一致。",
  },
  {
    status: "stashed",
    title: "图表题注需要人工复核",
    body: "检测到浮动图片和表格，导出后保留人工复核记录。",
    risk: "复杂对象可能无法完全高保真恢复。",
  },
  {
    status: "accepted",
    title: "参考文献格式统一",
    body: "已生成 v1.1 版本，未补造作者、刊名或卷期。",
    risk: "缺失元数据仍需用户回到原始来源确认。",
  },
];

const demoEvents = [
  "run_started · Intake Parser",
  "agent_start · Compliance Auditor",
  "proposal_created · abstract-cn",
  "approval_required · 3 items",
  "run_completed · baseline v1",
];

const demoExports = [
  "SCNU-thesis-baseline.docx · completed",
  "integrity-report.json · completed",
  "review-notes.md · completed",
];

export function WorkbenchDemo() {
  return (
    <main className="workbench-shell demo-workbench-shell">
      <header className="workbench-topbar demo-workbench-topbar">
        <div>
          <a className="workbench-back" href="#/">
            返回公开首页
          </a>
          <h1>SCNU Thesis Agent Workbench Demo</h1>
          <p>安全示例项目，不包含真实论文正文，不调用远程 Provider。</p>
        </div>
        <div className="workbench-status">
          <span>当前版本 baseline v1</span>
          <span className="model-status model-status-local">本地优先模式</span>
        </div>
      </header>

      <section className="workbench-grid demo-workbench-grid">
        <aside className="workbench-panel">
          <div className="workbench-panel-head">
            <h2>项目与文件</h2>
            <span className="proposal-status">demo project</span>
          </div>
          <article className="demo-project-card">
            <h3>基于学习投入的本科论文示例</h3>
            <p>school=scnu · undergraduate · scnu-undergraduate</p>
            <p>privacy_mode=local_only · remote_provider_allowed=false</p>
          </article>
          <h3>文件库</h3>
          <div className="workbench-list compact">
            {demoFiles.map((file) => (
              <div key={file.name} className="workbench-row">
                <strong>{file.name}</strong>
                <span>{file.meta}</span>
              </div>
            ))}
          </div>
        </aside>

        <section className="workbench-document">
          <div className="privacy-banner">
            <strong>公开预览边界</strong>
            <p>这里只展示 Workbench 信息结构。真实论文、Provider key 和远程模型授权应在私有部署中处理。</p>
          </div>
          <div className="workbench-panel-head">
            <h2>文档预览与版本</h2>
            <div className="workbench-actions">
              <button type="button">DOCX</button>
              <button type="button">Markdown</button>
              <button type="button">自检报告</button>
            </div>
          </div>
          <article className="workbench-preview demo-paper-preview">
            <p className="public-kicker">baseline v1</p>
            <h3>基于学习投入的本科论文示例</h3>
            <p>
              中文摘要已识别，研究方法描述不足。正文结构包含绪论、相关研究、研究设计、结果分析和结论。图表与脚注已进入人工复核范围。
            </p>
            <div className="workbench-blocks">
              <section>
                <h4>Issue Map</h4>
                <p>摘要方法缺失、参考文献格式不统一、图表题注需复核、目录字段待 Word 更新。</p>
              </section>
              <section>
                <h4>Version Rule</h4>
                <p>Proposal 未确认不会影响当前版本；接受建议后生成新版本并写入 Audit Log。</p>
              </section>
            </div>
          </article>
          <h3>版本历史</h3>
          <div className="workbench-timeline">
            <div>
              <strong>baseline v1</strong>
              <span>Intake Parser · 结构识别后生成</span>
            </div>
            <div>
              <strong>accepted:reference-format</strong>
              <span>用户接受参考文献格式建议后生成</span>
            </div>
          </div>
        </section>

        <aside className="workbench-panel">
          <h2>Agent 面板</h2>
          <div className="workbench-events">
            {demoEvents.map((event) => (
              <div key={event}>
                <strong>{event.split(" · ")[0]}</strong>
                <span>{event.split(" · ")[1]}</span>
              </div>
            ))}
          </div>
          <h3>建议队列</h3>
          <div className="workbench-proposals">
            {demoProposals.map((proposal) => (
              <article key={proposal.title}>
                <span className="proposal-status">{proposal.status}</span>
                <h4>{proposal.title}</h4>
                <p>{proposal.body}</p>
                <small>{proposal.risk}</small>
              </article>
            ))}
          </div>
          <h3>导出历史</h3>
          <div className="workbench-list compact">
            {demoExports.map((item) => (
              <div key={item} className="workbench-row">
                <strong>{item.split(" · ")[0]}</strong>
                <span>{item.split(" · ")[1]}</span>
              </div>
            ))}
          </div>
        </aside>
      </section>
    </main>
  );
}
