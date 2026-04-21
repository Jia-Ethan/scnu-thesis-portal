import type { PrecheckResponse } from "../../generated/contracts";

type PrecheckModalProps = {
  open: boolean;
  precheck: PrecheckResponse | null;
  onCancel: () => void;
  onConfirm: () => void;
};

type SummaryItem = {
  key: string;
  label: string;
  detail: string;
  tone: "calm" | "attention";
};

export function PrecheckModal({ open, precheck, onCancel, onConfirm }: PrecheckModalProps) {
  if (!open || !precheck) return null;

  const summaryItems = buildSummaryItems(precheck);
  const attentionCount = summaryItems.filter((item) => item.tone === "attention").length;

  return (
    <div className="modal-overlay" role="presentation">
      <div className="precheck-sheet" role="dialog" aria-modal="true" aria-labelledby="precheck-title">
        <div className="precheck-sheet-top">
          <div>
            <p className="precheck-sheet-eyebrow">Precheck</p>
            <h2 id="precheck-title">检查完成</h2>
            <p className="precheck-sheet-intro">
              {attentionCount > 0 ? `发现 ${attentionCount} 处需要留意的摘要，仍可继续导出。` : "结构主线已完成识别，可以继续导出。"}
            </p>
          </div>
          <button type="button" className="precheck-sheet-close" onClick={onCancel} aria-label="关闭预检结果">
            ×
          </button>
        </div>

        <div className="precheck-sheet-status">
          <strong>可导出</strong>
          <span>Word 将按当前识别结果生成。</span>
        </div>

        <div className="precheck-sheet-list">
          {summaryItems.map((item) => (
            <article key={item.key} className={`precheck-summary-row precheck-summary-row-${item.tone}`}>
              <p>{item.label}</p>
              <strong>{item.detail}</strong>
            </article>
          ))}
        </div>

        <div className="precheck-sheet-actions">
          <button type="button" className="button button-subtle" onClick={onCancel}>
            返回
          </button>
          <button type="button" className="button button-primary" onClick={onConfirm}>
            导出 Word
          </button>
        </div>
      </div>
    </div>
  );
}

function buildSummaryItems(precheck: PrecheckResponse): SummaryItem[] {
  const issueMap = new Map(precheck.issues.map((issue) => [issue.id, issue]));
  const summary = precheck.preview_blocks
    .filter((block) => block.status !== "ok" || block.issue_ids.length > 0)
    .slice(0, 4)
    .map<SummaryItem>((block) => {
      const firstIssue = block.issue_ids.map((id) => issueMap.get(id)).find(Boolean);
      return {
        key: block.key,
        label: block.label,
        detail: firstIssue?.message || block.preview,
        tone: block.status === "ok" ? "calm" : "attention",
      };
    });

  if (summary.length > 0) return summary;

  return [
    {
      key: "abstract",
      label: "摘要",
      detail: "摘要结构已识别，可继续导出。",
      tone: "calm",
    },
    {
      key: "body",
      label: "正文",
      detail: "正文主线已识别，未发现显著阻塞。",
      tone: "calm",
    },
    {
      key: "references",
      label: "参考文献",
      detail: "参考文献章节已纳入导出结果。",
      tone: "calm",
    },
  ];
}
