const guideSections = [
  {
    title: "Supported files",
    body: "当前公开入口优先支持 .docx 文件，建议上传论文主文档。复杂表格、脚注、图片与浮动对象仍需要人工复核。",
  },
  {
    title: "Format requirements",
    body: "直接粘贴学校、学院或课程发布的格式要求即可。后续 Agent 接入后，会从文本中提取标题层级、摘要、关键词、字体字号、页边距、行距与参考文献规则。",
  },
  {
    title: "Preview",
    body: "预检会先识别论文结构，再把问题按结构、摘要、标题、页面设置与参考文献归类展示。当前公开 API 已支持 .docx 结构预检。",
  },
  {
    title: "Fix and export",
    body: "自动修复按钮目前是前端流程预留；真实修复 Agent 接入后，应返回可审计的修改清单。Word 导出沿用现有导出任务接口。",
  },
  {
    title: "Privacy",
    body: "真实论文建议使用私有部署或本地环境。公开预览不应承载敏感论文、Provider key 或长期项目数据。",
  },
];

export function GuidePage() {
  return (
    <main className="formatter-page guide-page">
      <nav className="portal-nav" aria-label="主导航">
        <a className="portal-brand" href="/" aria-label="Forma 首页">
          Forma
        </a>
        <div className="portal-nav-links" aria-label="功能入口">
          <a href="/#requirements">Upload</a>
          <a href="/#preview">Preview</a>
          <a href="/#export">Export</a>
        </div>
      </nav>

      <section className="guide-shell" aria-labelledby="guide-title">
        <div className="guide-hero">
          <p className="formatter-eyebrow">Guide</p>
          <h1 id="guide-title">Use Forma with a clear boundary.</h1>
          <p>了解它现在能做什么、哪些能力仍待接入 Agent，以及上传论文前需要注意的隐私边界。</p>
        </div>

        <div className="guide-list">
          {guideSections.map((section) => (
            <article key={section.title} className="guide-item">
              <h2>{section.title}</h2>
              <p>{section.body}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
