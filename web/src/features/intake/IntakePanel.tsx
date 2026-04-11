import { FormEvent } from "react";
import type { HealthResponse } from "../../generated/contracts";
import type { InputMode } from "../../app/domain";
import { formatBytes } from "../../app/domain";
import { EmptyState, FieldGroup, InfoNotice, PrimaryButton, SegmentedControl } from "../../components/ui";

type IntakePanelProps = {
  health: HealthResponse | null;
  mode: InputMode;
  selectedFile: File | null;
  rawText: string;
  busy: boolean;
  onModeChange: (mode: InputMode) => void;
  onFileChange: (file: File | null) => void;
  onTextChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
};

export function IntakePanel({
  health,
  mode,
  selectedFile,
  rawText,
  busy,
  onModeChange,
  onFileChange,
  onTextChange,
  onSubmit,
}: IntakePanelProps) {
  return (
    <section className="intake-panel" aria-labelledby="intake-title">
      <div className="section-card-header">
        <div>
          <p className="section-eyebrow">开始</p>
          <h2 id="intake-title">选择输入方式</h2>
          <p className="section-description">先把内容交给系统识别，解析完成后再进入校对工作台。</p>
        </div>
      </div>

      <SegmentedControl
        label="输入方式"
        value={mode}
        onChange={onModeChange}
        options={[
          { value: "docx", label: "上传 .docx", description: "适合已有论文文档" },
          { value: "text", label: "粘贴正文", description: "适合快速整理结构" },
        ]}
      />

      <form className="intake-form" onSubmit={onSubmit}>
        {mode === "docx" ? (
          <div className="dropzone" data-has-file={selectedFile ? "true" : "false"}>
            <FieldGroup
              label="论文文件"
              htmlFor="docx-file"
              hint={`仅支持 .docx，当前上传上限 ${formatBytes(health?.limits.max_docx_size_bytes)}。`}
            >
              <input
                id="docx-file"
                type="file"
                accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
              />
            </FieldGroup>
            <EmptyState
              title={selectedFile ? selectedFile.name : "拖入或选择 .docx 文件"}
              message={
                selectedFile
                  ? "文件已就绪。点击开始识别后，系统会抽取可校对的论文结构。"
                  : "常见失败原因：上传 .doc、空文件、损坏文件，或文件超过当前大小上限。"
              }
            />
          </div>
        ) : (
          <FieldGroup
            label="论文正文"
            htmlFor="raw-text"
            hint="可直接粘贴带标题的文本，例如：摘要、Abstract、第一章、参考文献、致谢、附录。"
          >
            <textarea
              id="raw-text"
              rows={12}
              value={rawText}
              onChange={(event) => onTextChange(event.target.value)}
              placeholder="在这里粘贴论文正文。系统会尝试识别摘要、关键词、章节标题、参考文献、致谢与附录。"
            />
          </FieldGroup>
        )}

        <InfoNotice title="当前不会做的事">
          <p>不保留 Word 原始样式，不承诺复杂表格、图片、脚注或特殊排版完整恢复。</p>
        </InfoNotice>

        <div className="actions actions-end">
          <PrimaryButton type="submit" disabled={busy}>
            {busy ? "正在识别结构" : "开始识别"}
          </PrimaryButton>
        </div>
      </form>
    </section>
  );
}
