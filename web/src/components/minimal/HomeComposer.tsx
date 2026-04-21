import { useLayoutEffect, useRef, useState, type DragEvent as ReactDragEvent } from "react";
import type { FlowPhase } from "../../app/domain";
import { WaveExportProgress } from "./WaveExportProgress";

type HomeComposerProps = {
  rawText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  exportProgress: number;
  exportMessage?: string;
  onTextChange: (value: string) => void;
  onUploadTrigger: () => boolean;
  onFileSelect: (file: File | null) => void;
  onSubmit: () => void;
  onCancelExport: () => void;
  onClear: () => void;
};

function hasFiles(event: Pick<DragEvent, "dataTransfer"> | Pick<ReactDragEvent, "dataTransfer">) {
  return Array.from(event.dataTransfer?.types ?? []).includes("Files");
}

export function HomeComposer({
  rawText,
  selectedFile,
  phase,
  exportProgress,
  exportMessage,
  onTextChange,
  onUploadTrigger,
  onFileSelect,
  onSubmit,
  onCancelExport,
  onClear,
}: HomeComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const dragDepthRef = useRef(0);
  const [isDragActive, setIsDragActive] = useState(false);
  const hasContent = Boolean(selectedFile || rawText.trim());
  const disabled = phase === "prechecking" || phase === "exporting";

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea || selectedFile) return;

    textarea.style.height = "0px";
    const computed = window.getComputedStyle(textarea);
    const fontSize = Number.parseFloat(computed.fontSize) || 16;
    const rawLineHeight = Number.parseFloat(computed.lineHeight);
    const lineHeight = computed.lineHeight.endsWith("px")
      ? rawLineHeight || fontSize * 1.55
      : rawLineHeight && rawLineHeight > 0 && rawLineHeight < 3
        ? fontSize * rawLineHeight
        : fontSize * 1.55;
    const minHeight = Math.ceil(lineHeight * 5);
    const maxHeight = Math.ceil(lineHeight * 10);
    const nextHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);

    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  }, [rawText, selectedFile, phase]);

  function resetDragState() {
    dragDepthRef.current = 0;
    setIsDragActive(false);
  }

  return (
    <div className="formatter-composer-shell" data-has-content={hasContent} data-busy={disabled}>
      <div
        className="formatter-composer"
        data-drag-active={isDragActive}
        data-has-file={Boolean(selectedFile)}
        data-busy={disabled}
        aria-busy={disabled}
        onDragEnter={(event) => {
          if (!hasFiles(event)) return;
          event.preventDefault();
          dragDepthRef.current += 1;
          if (!disabled) setIsDragActive(true);
        }}
        onDragOver={(event) => {
          if (!hasFiles(event)) return;
          event.preventDefault();
          event.dataTransfer.dropEffect = disabled ? "none" : "copy";
          if (!disabled && !isDragActive) setIsDragActive(true);
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
          if (!file || disabled) return;
          if (!onUploadTrigger()) return;
          onFileSelect(file);
        }}
      >
        <div className="formatter-composer-top">
          <div className="formatter-composer-copy">
            <p className="formatter-composer-label">开始</p>
            <h2>把论文内容放进这里。</h2>
          </div>
          <button
            type="button"
            className="formatter-upload-button"
            aria-label="上传 .docx 文件"
            disabled={disabled}
            onClick={() => {
              if (!onUploadTrigger()) return;
              fileInputRef.current?.click();
            }}
          >
            选择 `.docx`
          </button>
        </div>

        <input
          ref={fileInputRef}
          className="visually-hidden-input"
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
          <div className="formatter-export-state">
            <WaveExportProgress progress={exportProgress} message={exportMessage} onCancel={onCancelExport} />
          </div>
        ) : (
          <>
            {selectedFile ? (
              <div className="formatter-file-summary" aria-label="当前已选文件">
                <span className="formatter-file-kicker">已载入</span>
                <strong>{selectedFile.name}</strong>
              </div>
            ) : (
              <textarea
                ref={textareaRef}
                className="formatter-textarea"
                aria-label="论文正文输入框"
                placeholder="或直接粘贴论文正文"
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

            <div className="formatter-composer-footer">
              <p className="formatter-composer-hint">
                {selectedFile ? "已准备好进入预检。" : "也可以直接粘贴已有正文。"}
              </p>
              <div className="formatter-composer-actions">
                {hasContent ? (
                  <button type="button" className="formatter-clear-button" onClick={onClear} disabled={disabled}>
                    清空
                  </button>
                ) : null}
                <button type="button" className="formatter-primary-button" onClick={onSubmit} disabled={disabled}>
                  开始预检
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
