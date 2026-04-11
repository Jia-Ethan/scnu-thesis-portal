import type { NormalizedThesis } from "../../generated/contracts";
import type { ExportKind } from "../../app/domain";
import { InfoNotice, PrimaryButton, SecondaryButton, SectionCard, StatusBadge } from "../../components/ui";

type ExportPanelProps = {
  thesis: NormalizedThesis;
  exporting: ExportKind | null;
  onExport: (kind: ExportKind) => void;
};

export function ExportPanel({ thesis, exporting, onExport }: ExportPanelProps) {
  const pdfEnabled = thesis.capabilities.pdf;

  return (
    <SectionCard
      title="导出成果"
      eyebrow="最终产物"
      description="当前主产物是可继续调整的 LaTeX 工程。"
      className="export-panel"
    >
      <div className="export-product">
        <div>
          <p className="export-product-label">推荐导出</p>
          <h3>.tex 工程 zip</h3>
          <p>包含 normalized 内容映射后的模板工程，适合本地编译或人工继续修正。</p>
        </div>
        <StatusBadge tone="success">主路径</StatusBadge>
      </div>

      <div className="export-actions">
        <PrimaryButton type="button" onClick={() => onExport("tex")} disabled={exporting !== null}>
          {exporting === "tex" ? "正在生成 zip" : "导出 .tex 工程 zip"}
        </PrimaryButton>
        <SecondaryButton type="button" onClick={() => onExport("pdf")} disabled={!pdfEnabled || exporting !== null}>
          {exporting === "pdf" ? "正在生成 PDF" : "导出 PDF"}
        </SecondaryButton>
      </div>

      {!pdfEnabled ? (
        <InfoNotice title="PDF 当前未开启" tone="warning">
          <p>{thesis.capabilities.pdf_reason ?? "生产环境默认关闭 PDF，请先导出 tex 工程 zip。"}</p>
          <p>建议路径：下载 zip 后，在本地 TeX 环境中编译并人工检查格式。</p>
        </InfoNotice>
      ) : null}
    </SectionCard>
  );
}
