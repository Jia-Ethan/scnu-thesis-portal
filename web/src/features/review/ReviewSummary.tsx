import type { NormalizedThesis } from "../../generated/contracts";
import { bodySummary } from "../../app/domain";
import { InfoNotice, SectionCard, StatusBadge } from "../../components/ui";

type ReviewSummaryProps = {
  thesis: NormalizedThesis;
};

export function ReviewSummary({ thesis }: ReviewSummaryProps) {
  const summary = bodySummary(thesis);

  return (
    <SectionCard title="识别概览" eyebrow="Review" description="先看结构，再做字段修正。">
      <div className="summary-list">
        <SummaryRow label="中文摘要" value={summary.abstractCn ? "已识别" : "待补充"} done={summary.abstractCn} />
        <SummaryRow label="Abstract" value={summary.abstractEn ? "已识别" : "待补充"} done={summary.abstractEn} />
        <SummaryRow label="正文章节" value={`${summary.bodyCount} 个`} done={summary.bodyCount > 0} />
        <SummaryRow label="参考文献" value={`${summary.referencesCount} 条`} done={summary.referencesCount > 0} />
        <SummaryRow label="致谢" value={summary.acknowledgements ? "已识别" : "待补充"} done={summary.acknowledgements} />
        <SummaryRow label="附录" value={summary.appendix ? "已识别" : "待补充"} done={summary.appendix} />
      </div>

      {thesis.warnings.length > 0 ? (
        <InfoNotice title="需要留意" tone="warning">
          <ul className="plain-list">
            {thesis.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </InfoNotice>
      ) : null}

      {thesis.parse_errors.length > 0 ? (
        <InfoNotice title="解析提示" tone="danger">
          <ul className="plain-list">
            {thesis.parse_errors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        </InfoNotice>
      ) : null}
    </SectionCard>
  );
}

function SummaryRow({ label, value, done }: { label: string; value: string; done: boolean }) {
  return (
    <div className="summary-row">
      <span>{label}</span>
      <StatusBadge tone={done ? "success" : "warning"}>{value}</StatusBadge>
    </div>
  );
}
