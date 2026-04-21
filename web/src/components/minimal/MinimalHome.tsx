import { useRef } from "react";
import type { FlowPhase, InlineErrorState } from "../../app/domain";
import { HeroAmbient } from "./HeroAmbient";
import { HomeComposer } from "./HomeComposer";
import { InlineError } from "./InlineError";

type MinimalHomeProps = {
  rawText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  exportProgress: number;
  exportMessage?: string;
  error: InlineErrorState | null;
  canRetryExport: boolean;
  onTextChange: (value: string) => void;
  onUploadTrigger: () => boolean;
  onFileSelect: (file: File | null) => void;
  onSubmit: () => void;
  onCancelExport: () => void;
  onRetryExport: () => void;
  onClear: () => void;
};

export function MinimalHome(props: MinimalHomeProps) {
  const heroRef = useRef<HTMLElement | null>(null);

  return (
    <main className="formatter-page">
      <section ref={heroRef} className="formatter-hero" aria-labelledby="formatter-title">
        <HeroAmbient containerRef={heroRef} />
        <div className="formatter-hero-copy">
          <p className="formatter-eyebrow">SCNU Thesis Formatter</p>
          <h1 id="formatter-title" className="formatter-title">
            论文格式，
            <br />
            安静归位。
          </h1>
          <p className="formatter-subtitle">上传 `.docx` 或粘贴正文，完成预检后导出规范化 Word。</p>
        </div>

        <section className="formatter-surface" aria-label="格式规范化工具">
          <HomeComposer
            rawText={props.rawText}
            selectedFile={props.selectedFile}
            phase={props.phase}
            exportProgress={props.exportProgress}
            exportMessage={props.exportMessage}
            onTextChange={props.onTextChange}
            onUploadTrigger={props.onUploadTrigger}
            onFileSelect={props.onFileSelect}
            onSubmit={props.onSubmit}
            onCancelExport={props.onCancelExport}
            onClear={props.onClear}
          />
          <InlineError
            message={props.error?.message ?? null}
            actionLabel={props.canRetryExport ? "重新导出" : undefined}
            onAction={props.canRetryExport ? props.onRetryExport : undefined}
          />
        </section>
      </section>
    </main>
  );
}
