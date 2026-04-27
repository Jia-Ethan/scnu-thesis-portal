import { useLayoutEffect, useRef, useState, type DragEvent as ReactDragEvent } from "react";
import type { FlowPhase } from "../../app/domain";

type HomeComposerProps = {
  requirementText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  onRequirementChange: (value: string) => void;
  onUseExampleRequirement: () => void;
  onUploadTrigger: () => boolean;
  onFileSelect: (file: File | null) => void;
  onPrecheck: () => void;
  onClear: () => void;
};

function hasFiles(event: Pick<DragEvent, "dataTransfer"> | Pick<ReactDragEvent, "dataTransfer">) {
  return Array.from(event.dataTransfer?.types ?? []).includes("Files");
}

function formatFileSize(size: number) {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export function HomeComposer({
  requirementText,
  selectedFile,
  phase,
  onRequirementChange,
  onUseExampleRequirement,
  onUploadTrigger,
  onFileSelect,
  onPrecheck,
  onClear,
}: HomeComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const dragDepthRef = useRef(0);
  const [isDragActive, setIsDragActive] = useState(false);
  const busy = phase === "analyzing" || phase === "exporting";
  const hasContent = Boolean(requirementText.trim() || selectedFile);

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "0px";
    const nextHeight = Math.min(Math.max(textarea.scrollHeight, 168), 320);
    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > 320 ? "auto" : "hidden";
  }, [requirementText]);

  function resetDragState() {
    dragDepthRef.current = 0;
    setIsDragActive(false);
  }

  function openFileDialog() {
    if (!onUploadTrigger()) return;
    fileInputRef.current?.click();
  }

  return (
    <section className="portal-composer" aria-label="论文格式检查入口" data-phase={phase}>
      <div className="portal-composer-grid">
        <div className="requirement-panel">
          <div className="panel-heading">
            <h2>Requirements</h2>
          </div>

          <textarea
            ref={textareaRef}
            className="requirement-textarea"
            aria-label="论文格式要求输入框"
            placeholder="粘贴学校、学院或期刊的格式要求。"
            value={requirementText}
            disabled={busy}
            onChange={(event) => onRequirementChange(event.target.value)}
          />

          <div className="requirement-actions">
            <button type="button" className="ghost-button" disabled={busy} onClick={onUseExampleRequirement}>
              Example
            </button>
            <span>{requirementText.trim() ? `${requirementText.trim().length} chars` : "Paste text"}</span>
          </div>
        </div>

        <div id="upload" className="upload-panel">
          <div className="panel-heading">
            <h2>Thesis file</h2>
          </div>

          <input
            ref={fileInputRef}
            className="visually-hidden-input"
            type="file"
            accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            hidden
            tabIndex={-1}
            aria-hidden="true"
            disabled={busy}
            onChange={(event) => {
              const input = event.currentTarget;
              onFileSelect(input.files?.[0] ?? null);
              input.value = "";
            }}
          />

          <button
            type="button"
            className="dropzone"
            data-drag-active={isDragActive}
            aria-label={selectedFile ? `当前已选文件 ${selectedFile.name}` : "上传 .docx 文件"}
            disabled={busy}
            onClick={openFileDialog}
            onDragEnter={(event) => {
              if (!hasFiles(event)) return;
              event.preventDefault();
              dragDepthRef.current += 1;
              if (!busy) setIsDragActive(true);
            }}
            onDragOver={(event) => {
              if (!hasFiles(event)) return;
              event.preventDefault();
              event.dataTransfer.dropEffect = busy ? "none" : "copy";
              if (!busy && !isDragActive) setIsDragActive(true);
            }}
            onDragLeave={(event) => {
              if (!hasFiles(event)) return;
              event.preventDefault();
              dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
              if (dragDepthRef.current === 0) setIsDragActive(false);
            }}
            onDrop={(event) => {
              if (!hasFiles(event)) return;
              event.preventDefault();
              const file = event.dataTransfer.files?.[0] ?? null;
              resetDragState();
              if (!file || busy) return;
              if (!onUploadTrigger()) return;
              onFileSelect(file);
            }}
          >
            {selectedFile ? (
              <span className="file-card">
                <span className="file-icon">DOCX</span>
                <span>
                  <strong>{selectedFile.name}</strong>
                  <small>{formatFileSize(selectedFile.size)} · Ready</small>
                </span>
              </span>
            ) : (
              <span className="dropzone-empty">
                <strong>Drop .docx here</strong>
                <small>or choose from your device</small>
              </span>
            )}
          </button>
        </div>
      </div>

      <div className="composer-command-bar">
        <p>需要格式要求和 .docx 文件才能开始。</p>
        <div className="composer-command-actions">
          {hasContent ? (
            <button type="button" className="secondary-action" disabled={busy} onClick={onClear}>
              Reset
            </button>
          ) : null}
          <button type="button" className="primary-action" disabled={busy} onClick={onPrecheck}>
            {phase === "analyzing" ? "Analyzing" : "Start preview"}
          </button>
        </div>
      </div>
    </section>
  );
}
