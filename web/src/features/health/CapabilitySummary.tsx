import type { HealthResponse } from "../../generated/contracts";
import { CapabilityCard } from "../../components/ui";

type CapabilitySummaryProps = {
  health: HealthResponse | null;
  compact?: boolean;
};

export function CapabilitySummary({ health, compact = false }: CapabilitySummaryProps) {
  const pdfEnabled = Boolean(health?.capabilities.pdf);

  return (
    <div className={compact ? "capability-grid capability-grid-compact" : "capability-grid"}>
      <CapabilityCard
        label="模板"
        value={health?.template ?? "加载中"}
        tone={health?.template ? "success" : "info"}
        detail="当前主线模板工程。"
      />
      <CapabilityCard
        label="主产物"
        value=".tex zip"
        tone="success"
        detail="适合下载后本地编译或继续人工调整。"
      />
      <CapabilityCard
        label="PDF"
        value={pdfEnabled ? "已开启" : "未开启"}
        tone={pdfEnabled ? "success" : "warning"}
        detail={health?.capabilities.pdf_reason ?? "生产环境默认关闭 PDF，请导出 tex 工程 zip。"}
      />
    </div>
  );
}
