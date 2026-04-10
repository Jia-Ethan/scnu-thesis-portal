import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
import type { HealthResponse, JobCreateResponse, JobStatusResponse } from "./types";

type TabKey = "docx" | "form";

type MetaFields = {
  title: string;
  author_name: string;
  student_id: string;
  department: string;
  major: string;
  class_name: string;
  advisor_name: string;
  submission_date: string;
};

type StructuredFields = MetaFields & {
  abstract_cn: string;
  abstract_en: string;
  keywords_cn: string;
  keywords_en: string;
  body: string;
  references: string;
  acknowledgements: string;
  appendix: string;
};

const defaultMeta: MetaFields = {
  title: "",
  author_name: "",
  student_id: "",
  department: "",
  major: "",
  class_name: "",
  advisor_name: "",
  submission_date: new Date().toISOString().slice(0, 10),
};

const defaultStructured: StructuredFields = {
  ...defaultMeta,
  abstract_cn: "",
  abstract_en: "",
  keywords_cn: "",
  keywords_en: "",
  body: "",
  references: "",
  acknowledgements: "",
  appendix: "",
};

async function apiJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error_message || response.statusText);
  }
  return data as T;
}

function AppHome() {
  const [activeTab, setActiveTab] = useState<TabKey>("docx");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metaFields, setMetaFields] = useState<MetaFields>(defaultMeta);
  const [structuredFields, setStructuredFields] = useState<StructuredFields>(defaultStructured);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    apiJson<HealthResponse>("/api/health")
      .then(setHealth)
      .catch((err) => setError(err.message));
  }, []);

  const missingTex = useMemo(() => health?.tex.missing_styles ?? [], [health]);

  function updateMetaField(field: keyof MetaFields, value: string) {
    setMetaFields((prev) => ({ ...prev, [field]: value }));
    setStructuredFields((prev) => ({ ...prev, [field]: value }));
  }

  function updateStructuredField(field: keyof StructuredFields, value: string) {
    setStructuredFields((prev) => ({ ...prev, [field]: value }));
    if (field in defaultMeta) {
      setMetaFields((prev) => ({ ...prev, [field as keyof MetaFields]: value }));
    }
  }

  async function handleStructuredSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = structuredFields;
      const result = await apiJson<JobCreateResponse>("/api/jobs/from-form", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      navigate(`/jobs/${result.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDocxSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedFile) {
      setError("请先选择 .docx 文件。");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const formData = new FormData();
      Object.entries(metaFields).forEach(([key, value]) => formData.append(key, value));
      formData.append("file", selectedFile);
      const result = await apiJson<JobCreateResponse>("/api/jobs/from-docx", {
        method: "POST",
        body: formData,
      });
      navigate(`/jobs/${result.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">SCNU Thesis Portal Local MVP</p>
          <h1>本地论文模板映射演示站</h1>
          <p className="hero-copy">
            只支持 <code>.docx</code> 与结构化输入，不保留原 Word 样式。当前目标是稳定跑通结构化映射 → LaTeX 工程 → PDF 导出。
          </p>
        </div>
        <div className="status-card">
          <h2>本机环境</h2>
          <p>XeLaTeX：{health?.tex.xelatex ? "可用" : "缺失"}</p>
          <p>kpsewhich：{health?.tex.kpsewhich ? "可用" : "缺失"}</p>
          {missingTex.length > 0 ? (
            <div className="warning">
              <strong>缺少 TeX 宏包：</strong>
              <div>{missingTex.join(", ")}</div>
            </div>
          ) : (
            <p className="ok">TeX 关键依赖已通过预检。</p>
          )}
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="tabs">
        <button className={activeTab === "docx" ? "tab active" : "tab"} onClick={() => setActiveTab("docx")}>
          上传 .docx
        </button>
        <button className={activeTab === "form" ? "tab active" : "tab"} onClick={() => setActiveTab("form")}>
          结构化输入
        </button>
      </section>

      <div className="layout">
        <section className="panel">
          <h2>封面与基础信息</h2>
          <div className="form-grid">
            {Object.entries(metaFields).map(([key, value]) => (
              <label key={key}>
                <span>{labelMap[key as keyof MetaFields]}</span>
                <input
                  value={value}
                  onChange={(event) => updateMetaField(key as keyof MetaFields, event.target.value)}
                />
              </label>
            ))}
          </div>
        </section>

        {activeTab === "docx" ? (
          <section className="panel">
            <h2>上传 .docx</h2>
            <form onSubmit={handleDocxSubmit} className="stack">
              <label className="file-input">
                <span>选择论文文件（仅 .docx）</span>
                <input
                  type="file"
                  accept=".docx"
                  onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                />
              </label>
              <p className="helper">
                上传后系统会提取文本和标题层级，再映射到本科论文模板。它不会保留原 Word 排版。
              </p>
              <button type="submit" disabled={submitting}>
                {submitting ? "处理中..." : "上传并生成"}
              </button>
            </form>
          </section>
        ) : (
          <section className="panel">
            <h2>结构化输入</h2>
            <form onSubmit={handleStructuredSubmit} className="stack">
              {structuredFieldOrder.map((field) => (
                <label key={field}>
                  <span>{structuredLabelMap[field]}</span>
                  {longTextFields.has(field) ? (
                    <textarea
                      rows={field === "body" ? 12 : 6}
                      value={structuredFields[field]}
                      onChange={(event) => updateStructuredField(field, event.target.value)}
                    />
                  ) : (
                    <input
                      value={structuredFields[field]}
                      onChange={(event) => updateStructuredField(field, event.target.value)}
                    />
                  )}
                </label>
              ))}
              <button type="submit" disabled={submitting}>
                {submitting ? "处理中..." : "生成 PDF 与 tex 工程"}
              </button>
            </form>
          </section>
        )}
      </div>
    </div>
  );
}

function JobPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    let timer: number | undefined;
    let cancelled = false;

    async function load() {
      try {
        const data = await apiJson<JobStatusResponse>(`/api/jobs/${jobId}`);
        if (cancelled) return;
        setJob(data);
        if (data.status === "queued" || data.status === "processing") {
          timer = window.setTimeout(load, 1500);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "任务查询失败");
        }
      }
    }

    load();

    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [jobId]);

  if (error) {
    return (
      <div className="page narrow">
        <Link to="/">返回首页</Link>
        <div className="error-banner">{error}</div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="page narrow">
        <Link to="/">返回首页</Link>
        <p>正在加载任务状态...</p>
      </div>
    );
  }

  return (
    <div className="page narrow">
      <Link to="/">返回首页</Link>
      <h1>任务 {job.job_id}</h1>
      <div className={`status-pill ${job.status}`}>{job.status}</div>
      <p>输入来源：{job.source_type}</p>
      <p>模板：{job.template}</p>
      {job.error_code ? (
        <div className="error-card">
          <strong>{job.error_code}</strong>
          <p>{job.error_message}</p>
        </div>
      ) : null}
      {job.warnings.length > 0 ? (
        <div className="warning">
          <strong>提示</strong>
          <ul>
            {job.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {job.sections.length > 0 ? (
        <section className="panel">
          <h2>识别出的章节</h2>
          <ul className="section-list">
            {job.sections.map((section, index) => (
              <li key={`${section.title}-${index}`}>
                <strong>{section.kind}</strong> · {section.title}
                <p>{section.content.slice(0, 160) || "（空内容）"}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {job.artifacts ? (
        <section className="panel">
          <h2>导出结果</h2>
          <div className="actions">
            <a href={`/api/jobs/${job.job_id}/artifacts/pdf`} target="_blank" rel="noreferrer">
              下载 PDF
            </a>
            <a href={`/api/jobs/${job.job_id}/artifacts/texzip`} target="_blank" rel="noreferrer">
              下载 tex 工程 zip
            </a>
          </div>
          <p>编译日志：{job.artifacts.compile_log_path || "无"}</p>
        </section>
      ) : null}
      {job.compile_command.length > 0 ? (
        <section className="panel">
          <h2>编译命令</h2>
          <code>{job.compile_command.join(" ")}</code>
        </section>
      ) : null}
    </div>
  );
}

const labelMap: Record<keyof MetaFields, string> = {
  title: "论文题目",
  author_name: "学生姓名",
  student_id: "学号",
  department: "学院 / 系别",
  major: "专业",
  class_name: "班级",
  advisor_name: "指导老师",
  submission_date: "日期",
};

const structuredFieldOrder: (keyof StructuredFields)[] = [
  "abstract_cn",
  "abstract_en",
  "keywords_cn",
  "keywords_en",
  "body",
  "references",
  "acknowledgements",
  "appendix",
];

const structuredLabelMap: Record<keyof StructuredFields, string> = {
  ...labelMap,
  abstract_cn: "中文摘要",
  abstract_en: "英文摘要",
  keywords_cn: "中文关键词",
  keywords_en: "英文关键词",
  body: "正文（支持 Markdown 风格标题）",
  references: "参考文献（每行一条）",
  acknowledgements: "致谢",
  appendix: "附录（可选）",
};

const longTextFields = new Set<keyof StructuredFields>([
  "abstract_cn",
  "abstract_en",
  "body",
  "references",
  "acknowledgements",
  "appendix",
]);

export function App() {
  return (
    <Routes>
      <Route path="/" element={<AppHome />} />
      <Route path="/jobs/:jobId" element={<JobPage />} />
    </Routes>
  );
}
