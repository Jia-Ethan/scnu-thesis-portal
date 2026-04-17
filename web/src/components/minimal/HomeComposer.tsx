import { useLayoutEffect, useRef, useState, type DragEvent as ReactDragEvent } from "react";
import type { FlowPhase } from "../../app/domain";
import type { CoverFields } from "../../generated/contracts";
import type { AIGenPhase } from "../../app/useMinimalExportFlow";
import { SegmentedControl } from "../ui/SegmentedControl";
import { WaveExportProgress } from "./WaveExportProgress";

type SourceTab = "upload" | "ai";

type HomeComposerProps = {
  rawText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  exportProgress: number;
  onTextChange: (value: string) => void;
  onUploadTrigger: () => boolean;
  onFileSelect: (file: File | null) => void;
  onSubmit: () => void;
  onClear: () => void;
  onDragActiveChange?: (active: boolean) => void;
  // AI gen
  sourceTab: SourceTab;
  onSourceTabChange: (tab: SourceTab) => void;
  aiPhase: AIGenPhase;
  researchPrompt: string;
  paperId: string | null;
  currentAgent: string | null;
  sectionIndex: number;
  revisionRound: number;
  aiError: string | null;
  coverFields: CoverFields;
  onResearchPromptChange: (v: string) => void;
  onCoverFieldsChange: (f: CoverFields) => void;
  onAIGenerate: () => void;
  onAIClear: () => void;
};

function hasFiles(event: Pick<DragEvent, "dataTransfer"> | Pick<ReactDragEvent, "dataTransfer">) {
  return Array.from(event.dataTransfer?.types ?? []).includes("Files");
}

export function HomeComposer({
  rawText,
  selectedFile,
  phase,
  exportProgress,
  onTextChange,
  onUploadTrigger,
  onFileSelect,
  onSubmit,
  onClear,
  onDragActiveChange,
  sourceTab,
  onSourceTabChange,
  aiPhase,
  researchPrompt,
  currentAgent,
  sectionIndex,
  revisionRound,
  aiError,
  coverFields,
  onResearchPromptChange,
  onCoverFieldsChange,
  onAIGenerate,
  onAIClear,
}: HomeComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const dragDepthRef = useRef(0);
  const [isDragActive, setIsDragActive] = useState(false);
  const hasContent = Boolean(selectedFile || rawText.trim());
  const disabled = phase === "prechecking" || phase === "exporting";
  const aiBusy = aiPhase === "generating";
  const hintText =
    phase === "prechecking"
      ? "正在进行结构识别与规则检查…"
      : hasContent
        ? "按 Cmd/Ctrl + Enter 开始预检"
        : null;

  function setDragActive(active: boolean) {
    setIsDragActive(active);
    onDragActiveChange?.(active);
  }

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea || selectedFile) return;

    textarea.style.height = "0px";
    const computed = window.getComputedStyle(textarea);
    const fontSize = Number.parseFloat(computed.fontSize) || 16;
    const rawLineHeight = Number.parseFloat(computed.lineHeight);
    const lineHeight = computed.lineHeight.endsWith("px")
      ? rawLineHeight || fontSize * 1.5
      : rawLineHeight && rawLineHeight > 0 && rawLineHeight < 3
        ? fontSize * rawLineHeight
        : fontSize * 1.5;
    const minHeight = Math.ceil(lineHeight);
    const maxHeight = Math.ceil(lineHeight * 4 + 4);
    const nextHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);

    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  }, [rawText, selectedFile, phase]);

  function resetDragState() {
    dragDepthRef.current = 0;
    setDragActive(false);
  }

  return (
    <div className="composer-shell" data-has-content={hasContent} data-busy={disabled || aiBusy}>
      {/* Tab switcher */}
      <div className="composer-tab-bar">
        <SegmentedControl
          label="输入来源"
          value={sourceTab}
          onChange={onSourceTabChange as (v: string) => void}
          options={[
            { value: "upload", label: "上传文档" },
            { value: "ai", label: "AI 生成" },
          ]}
        />
      </div>

      {/* AI Generation tab */}
      {sourceTab === "ai" ? (
        <AIGenPanel
          aiPhase={aiPhase}
          researchPrompt={researchPrompt}
          currentAgent={currentAgent}
          sectionIndex={sectionIndex}
          revisionRound={revisionRound}
          aiError={aiError}
          coverFields={coverFields}
          onPromptChange={onResearchPromptChange}
          onCoverFieldsChange={onCoverFieldsChange}
          onGenerate={onAIGenerate}
          onClear={onAIClear}
        />
      ) : (
        /* Upload / text tab */
        <div
          className={`composer ${selectedFile ? "composer-file" : ""} ${disabled ? "composer-busy" : ""}`}
          data-drag-active={isDragActive}
          data-has-file={Boolean(selectedFile)}
          data-busy={disabled}
          tabIndex={selectedFile ? 0 : -1}
          aria-busy={disabled}
          onKeyDown={(event) => {
            if (!selectedFile || disabled) return;
            if (event.key === "Enter") {
              event.preventDefault();
              onSubmit();
            }
          }}
          onDragEnter={(event) => {
            if (!hasFiles(event)) return;
            event.preventDefault();
            dragDepthRef.current += 1;
            if (!disabled) setDragActive(true);
          }}
          onDragOver={(event) => {
            if (!hasFiles(event)) return;
            event.preventDefault();
            event.dataTransfer.dropEffect = disabled ? "none" : "copy";
            if (!disabled && !isDragActive) setDragActive(true);
          }}
          onDragLeave={(event) => {
            if (!hasFiles(event)) return;
            event.preventDefault();
            dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
            if (dragDepthRef.current === 0) setDragActive(false);
          }}
          onDrop={(event) => {
            if (!hasFiles(event)) return;
            event.preventDefault();
            const file = event.dataTransfer.files?.[0] ?? null;
            resetDragState();
            if (!file || disabled) return;
            if (!onUploadTrigger()) return;
            onFileSelect(file);
          }}
        >
          <button
            type="button"
            className="composer-plus"
            aria-label="上传 .docx 文件"
            disabled={disabled}
            onClick={() => {
              if (!onUploadTrigger()) return;
              fileInputRef.current?.click();
            }}
          >
            +
          </button>
          <input
            ref={fileInputRef}
            className="composer-file-input visually-hidden-input"
            type="file"
            accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            hidden
            tabIndex={-1}
            aria-hidden="true"
            disabled={disabled}
            onFocus={(event) => {
              event.currentTarget.blur();
            }}
            onChange={(event) => {
              const input = event.currentTarget;
              onFileSelect(input.files?.[0] ?? null);
              input.value = "";
            }}
          />

          {phase === "exporting" ? (
            <div className="composer-progress">
              <WaveExportProgress progress={exportProgress} />
            </div>
          ) : selectedFile ? (
            <div className="composer-file-pill" aria-label="当前已选文件">
              <strong>{selectedFile.name}</strong>
            </div>
          ) : (
            <textarea
              ref={textareaRef}
              className="composer-textarea"
              aria-label="论文正文输入框"
              value={rawText}
              disabled={disabled}
              onChange={(event) => onTextChange(event.target.value)}
              onKeyDown={(event) => {
                if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                  event.preventDefault();
                  onSubmit();
                }
              }}
            />
          )}

          <button
            type="button"
            className="composer-submit"
            aria-label="开始预检"
            onClick={onSubmit}
            disabled={disabled}
          >
            →
          </button>
        </div>
      )}

      <div className="composer-meta">
        <div className="composer-hint-shell" aria-live="polite">
          {hintText && sourceTab === "upload" ? (
            <p className="composer-hint">{hintText}</p>
          ) : (
            <span className="composer-hint-placeholder" aria-hidden="true" />
          )}
        </div>
        {sourceTab === "upload" && hasContent ? (
          <button type="button" className="composer-clear" onClick={onClear} disabled={disabled}>
            清空
          </button>
        ) : (
          <span className="composer-clear-placeholder" />
        )}
      </div>
    </div>
  );
}

// ─── AI Generation Panel (inline, no separate file needed) ───────────────────

type AIGenPanelProps = {
  aiPhase: AIGenPhase;
  researchPrompt: string;
  currentAgent: string | null;
  sectionIndex: number;
  revisionRound: number;
  aiError: string | null;
  coverFields: CoverFields;
  onPromptChange: (v: string) => void;
  onCoverFieldsChange: (f: CoverFields) => void;
  onGenerate: () => void;
  onClear: () => void;
};

const AGENT_LABELS: Record<string, string> = {
  architect: "架构师",
  writer: "写作",
  evaluator: "评估",
  refiner: "精修",
};

function AIGenPanel({
  aiPhase,
  researchPrompt,
  currentAgent,
  sectionIndex,
  revisionRound,
  aiError,
  coverFields,
  onPromptChange,
  onCoverFieldsChange,
  onGenerate,
  onClear,
}: AIGenPanelProps) {
  const isBusy = aiPhase === "generating";
  const taRef = useRef<HTMLTextAreaElement | null>(null);

  useLayoutEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "0px";
    ta.style.height = `${Math.min(ta.scrollHeight, 320)}px`;
    ta.style.overflowY = ta.scrollHeight > 320 ? "auto" : "hidden";
  }, [researchPrompt]);

  function updateCover(field: keyof CoverFields, value: string) {
    onCoverFieldsChange({ ...coverFields, [field]: value });
  }

  const agentSteps = ["architect", "writer", "evaluator", "refiner"] as const;
  const activeIndex = currentAgent ? agentSteps.indexOf(currentAgent as (typeof agentSteps)[number]) : -1;

  return (
    <div className="ai-gen-panel">
      {/* Research prompt */}
      <div className="ai-gen-section">
        <label className="field-label" htmlFor="ai-research-prompt">
          研究方向与想法
        </label>
        <textarea
          id="ai-research-prompt"
          ref={taRef}
          className="composer-textarea ai-prompt-textarea"
          placeholder="描述你的研究问题、方向或初步想法…"
          value={researchPrompt}
          onChange={(e) => onPromptChange(e.target.value)}
          disabled={isBusy}
          rows={3}
        />
      </div>

      {/* Cover fields */}
      <div className="ai-gen-section">
        <p className="field-label">论文封面信息（生成后需补全）</p>
        <div className="cover-fields-grid">
          <label className="cover-field">
            <span>学生姓名</span>
            <input
              type="text"
              placeholder="必填"
              value={coverFields.student_name}
              onChange={(e) => updateCover("student_name", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>学号</span>
            <input
              type="text"
              placeholder="必填"
              value={coverFields.student_id}
              onChange={(e) => updateCover("student_id", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>专业</span>
            <input
              type="text"
              placeholder="必填"
              value={coverFields.major}
              onChange={(e) => updateCover("major", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>班级</span>
            <input
              type="text"
              placeholder="如：2022 级 1 班"
              value={coverFields.class_name}
              onChange={(e) => updateCover("class_name", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>指导老师</span>
            <input
              type="text"
              placeholder="必填"
              value={coverFields.advisor}
              onChange={(e) => updateCover("advisor", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>毕业时间</span>
            <input
              type="text"
              placeholder="如：2026 年 6 月"
              value={coverFields.graduation_time}
              onChange={(e) => updateCover("graduation_time", e.target.value)}
              disabled={isBusy}
            />
          </label>
        </div>
      </div>

      {/* Generation progress */}
      {aiPhase === "generating" && (
        <div className="ai-gen-progress">
          <div className="agent-steps">
            {agentSteps.map((agent, i) => {
              const isActive = currentAgent === agent;
              const isDone = i < activeIndex;
              return (
                <span
                  key={agent}
                  className={`agent-step ${isActive ? "active" : ""} ${isDone ? "done" : ""}`}
                >
                  {AGENT_LABELS[agent]}
                </span>
              );
            })}
          </div>
          <p className="agent-hint">
            {currentAgent ? `${AGENT_LABELS[currentAgent]}进行中` : "启动中…"}
            {sectionIndex > 0 ? ` 第 ${sectionIndex} 节` : ""}
            {revisionRound > 0 ? ` 第 ${revisionRound} 轮修订` : ""}
          </p>
        </div>
      )}

      {/* Error */}
      {aiPhase === "error" && aiError && (
        <div className="ai-gen-error">
          <p>{aiError}</p>
        </div>
      )}

      {/* Actions */}
      <div className="ai-gen-actions">
        {aiPhase === "generating" ? (
          <button type="button" className="btn-secondary" disabled>
            生成中…
          </button>
        ) : (
          <button
            type="button"
            className="btn-primary"
            disabled={!researchPrompt.trim()}
            onClick={onGenerate}
          >
            生成论文
          </button>
        )}
        {(aiPhase === "done" || aiPhase === "error") && (
          <button type="button" className="btn-ghost" onClick={onClear}>
            重新开始
          </button>
        )}
      </div>
    </div>
  );
}
