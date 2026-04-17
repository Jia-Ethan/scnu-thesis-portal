import { useEffect, useMemo, useState } from "react";
import {
  ApiError,
  createParseJob,
  createProject,
  createProjectExport,
  decideProposal,
  exportDownloadUrl,
  getJobEvents,
  getProviders,
  listProjectExports,
  listProjectFiles,
  listProjects,
  listProposals,
  listVersions,
  uploadProjectFile,
  type ExportRecord,
  type ProjectFileRecord,
  type ProposalRecord,
  type ThesisProject,
  type ThesisVersionRecord,
} from "../app/api";

type EventRecord = { id: string; type: string; payload: Record<string, unknown>; created_at: string };

export function WorkbenchApp() {
  const [projects, setProjects] = useState<ThesisProject[]>([]);
  const [activeProject, setActiveProject] = useState<ThesisProject | null>(null);
  const [files, setFiles] = useState<ProjectFileRecord[]>([]);
  const [versions, setVersions] = useState<ThesisVersionRecord[]>([]);
  const [proposals, setProposals] = useState<ProposalRecord[]>([]);
  const [exportsList, setExportsList] = useState<ExportRecord[]>([]);
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [providers, setProviders] = useState<Array<{ id: string; name: string; remote: boolean }>>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const currentVersion = useMemo(() => versions[0] ?? null, [versions]);

  useEffect(() => {
    void boot();
  }, []);

  async function boot() {
    try {
      const [projectRows, providerRows] = await Promise.all([listProjects(), getProviders()]);
      setProjects(projectRows);
      setProviders(providerRows.providers);
      if (projectRows[0]) {
        setActiveProject(projectRows[0]);
        await refreshProject(projectRows[0].id);
      }
    } catch (error) {
      setMessage(readError(error));
    }
  }

  async function refreshProject(projectId: string) {
    const [fileRows, versionRows, proposalRows, exportRows] = await Promise.all([
      listProjectFiles(projectId),
      listVersions(projectId),
      listProposals(projectId),
      listProjectExports(projectId),
    ]);
    setFiles(fileRows);
    setVersions(versionRows);
    setProposals(proposalRows);
    setExportsList(exportRows);
  }

  async function handleCreateProject() {
    setBusy(true);
    setMessage(null);
    try {
      const project = await createProject("SCNU Thesis Workbench 项目");
      setProjects((items) => [project, ...items]);
      setActiveProject(project);
      await refreshProject(project.id);
    } catch (error) {
      setMessage(readError(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleUpload(file: File | null) {
    if (!file || !activeProject) return;
    setBusy(true);
    setMessage(null);
    try {
      const type = inferFileType(file.name);
      const row = await uploadProjectFile(activeProject.id, file, type);
      const job = await createParseJob(activeProject.id, row.id);
      const eventRows = await getJobEvents(job.id);
      setEvents(eventRows);
      await refreshProject(activeProject.id);
      setMessage("解析完成，已生成 baseline 版本和建议队列。");
    } catch (error) {
      setMessage(readError(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleDecision(proposal: ProposalRecord, decision: "accept" | "reject" | "stash") {
    if (!activeProject) return;
    setBusy(true);
    setMessage(null);
    try {
      await decideProposal(proposal.id, decision);
      await refreshProject(activeProject.id);
    } catch (error) {
      setMessage(readError(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleExport(format: "docx" | "pdf" | "markdown" | "integrity_report") {
    if (!activeProject) return;
    setBusy(true);
    setMessage(null);
    try {
      await createProjectExport(activeProject.id, format);
      await refreshProject(activeProject.id);
      setMessage("导出记录已归档。");
    } catch (error) {
      setMessage(readError(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="workbench-shell">
      <header className="workbench-topbar">
        <div>
          <a className="workbench-back" href="#/">
            返回快速导出
          </a>
          <h1>SCNU Thesis Agent Workbench</h1>
        </div>
        <div className="workbench-status">
          <span>{currentVersion ? `当前版本 ${currentVersion.label}` : "暂无版本"}</span>
          <span>{providers.some((item) => item.id === "ollama") ? "本地模型可配置" : "模型待配置"}</span>
        </div>
      </header>

      <section className="workbench-grid">
        <aside className="workbench-panel">
          <div className="workbench-panel-head">
            <h2>项目与文件</h2>
            <button type="button" onClick={handleCreateProject} disabled={busy}>
              新建项目
            </button>
          </div>
          <div className="workbench-list">
            {projects.map((project) => (
              <button
                type="button"
                key={project.id}
                className={project.id === activeProject?.id ? "is-active" : ""}
                onClick={() => {
                  setActiveProject(project);
                  void refreshProject(project.id);
                }}
              >
                {project.title}
              </button>
            ))}
          </div>

          <label className="workbench-upload">
            <span>上传论文材料</span>
            <input
              type="file"
              disabled={!activeProject || busy}
              accept=".docx,.pdf,.txt,.bib,.ris,.png,.jpg,.jpeg,.webp"
              onChange={(event) => {
                const file = event.currentTarget.files?.[0] ?? null;
                event.currentTarget.value = "";
                void handleUpload(file);
              }}
            />
          </label>

          <h3>文件库</h3>
          <div className="workbench-list compact">
            {files.map((file) => (
              <div key={file.id} className="workbench-row">
                <strong>{file.filename}</strong>
                <span>{file.type} · {Math.round(file.size / 1024)} KB</span>
              </div>
            ))}
          </div>
        </aside>

        <section className="workbench-document">
          <div className="workbench-panel-head">
            <h2>文档预览与版本</h2>
            <div className="workbench-actions">
              <button type="button" disabled={!currentVersion || busy} onClick={() => void handleExport("docx")}>DOCX</button>
              <button type="button" disabled={!currentVersion || busy} onClick={() => void handleExport("markdown")}>Markdown</button>
              <button type="button" disabled={!currentVersion || busy} onClick={() => void handleExport("integrity_report")}>自检报告</button>
              <button type="button" disabled={!currentVersion || busy} onClick={() => void handleExport("pdf")}>PDF</button>
            </div>
          </div>
          {message && <p className="workbench-message">{message}</p>}
          {currentVersion ? (
            <article className="workbench-preview">
              <h3>{currentVersion.thesis.cover.title || "未命名论文"}</h3>
              <p>{currentVersion.thesis.abstract_cn.content || "中文摘要待补充。"}</p>
              <div className="workbench-blocks">
                {currentVersion.thesis.body_sections.map((section) => (
                  <section key={section.id}>
                    <h4>{section.title}</h4>
                    <p>{section.content || "该正文块暂无用户确认内容。"}</p>
                  </section>
                ))}
              </div>
            </article>
          ) : (
            <p className="workbench-empty">新建项目并上传 `.docx`、PDF、图片、参考文献或任务书后，这里会显示结构树和当前版本。</p>
          )}
          <h3>版本历史</h3>
          <div className="workbench-timeline">
            {versions.map((version) => (
              <div key={version.id}>
                <strong>{version.label}</strong>
                <span>{new Date(version.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </section>

        <aside className="workbench-panel">
          <h2>Agent 面板</h2>
          <div className="workbench-events">
            {events.map((event) => (
              <div key={event.id}>
                <strong>{eventLabel(event.type)}</strong>
                <span>{JSON.stringify(event.payload)}</span>
              </div>
            ))}
          </div>
          <h3>建议队列</h3>
          <div className="workbench-proposals">
            {proposals.map((proposal) => (
              <article key={proposal.id}>
                <span className="proposal-status">{proposal.status}</span>
                <h4>{proposal.reason}</h4>
                <p>{proposal.after}</p>
                <small>{proposal.risk}</small>
                {proposal.status === "pending" && (
                  <div>
                    <button type="button" onClick={() => void handleDecision(proposal, "accept")} disabled={busy}>接受</button>
                    <button type="button" onClick={() => void handleDecision(proposal, "reject")} disabled={busy}>拒绝</button>
                    <button type="button" onClick={() => void handleDecision(proposal, "stash")} disabled={busy}>暂存</button>
                  </div>
                )}
              </article>
            ))}
          </div>
          <h3>导出历史</h3>
          <div className="workbench-list compact">
            {exportsList.map((item) => (
              <a key={item.id} href={exportDownloadUrl(item.id)}>
                {item.filename} · {item.format}
              </a>
            ))}
          </div>
        </aside>
      </section>
    </main>
  );
}

function inferFileType(filename: string) {
  const lower = filename.toLowerCase();
  if (lower.endsWith(".pdf")) return "pdf";
  if (lower.endsWith(".bib") || lower.endsWith(".ris")) return "reference";
  if (/\.(png|jpg|jpeg|webp|tif|tiff)$/.test(lower)) return "image";
  if (lower.endsWith(".docx")) return "docx";
  return "text";
}

function eventLabel(type: string) {
  const labels: Record<string, string> = {
    run_started: "解析中",
    agent_start: "审查中",
    proposal_created: "生成建议中",
    approval_required: "等待确认",
    run_completed: "完成",
    run_failed: "失败",
  };
  return labels[type] ?? type;
}

function readError(error: unknown) {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "操作失败，请稍后重试。";
}
