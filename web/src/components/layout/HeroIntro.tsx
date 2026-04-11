import type { HealthResponse } from "../../generated/contracts";
import { formatBytes } from "../../app/domain";
import { CapabilitySummary } from "../../features/health/CapabilitySummary";
import { GlassPanel, InfoNotice, StatusBadge } from "../ui";

type HeroIntroProps = {
  health: HealthResponse | null;
};

export function HeroIntro({ health }: HeroIntroProps) {
  return (
    <section className="hero-intro" aria-labelledby="hero-title">
      <div className="hero-copy">
        <p className="eyebrow">SCNU Thesis Portal v0.2</p>
        <h1 id="hero-title">把论文内容带入清晰、可校对的模板工程。</h1>
        <p className="hero-lede">
          上传论文内容，识别结构，修正字段，然后导出规范化的 <code>.tex</code> 工程 zip。
        </p>
        <div className="hero-flow" aria-label="核心流程">
          {["上传内容", "识别结构", "校对字段", "导出工程"].map((item, index) => (
            <div className="hero-flow-item" key={item}>
              <span>{index + 1}</span>
              <strong>{item}</strong>
            </div>
          ))}
        </div>
        <InfoNotice title="使用边界">
          <p>
            当前不是学校官方认证工具。主产物是 <code>.tex</code> 工程 zip；生产环境默认关闭 PDF。
          </p>
        </InfoNotice>
      </div>

      <GlassPanel as="aside" className="hero-status" aria-label="当前能力摘要">
        <div className="hero-status-top">
          <div>
            <p className="section-eyebrow">当前能力</p>
            <h2>轻量结构化工作台</h2>
          </div>
          <StatusBadge tone={health?.ok ? "success" : "info"}>{health?.ok ? "在线" : "加载中"}</StatusBadge>
        </div>
        <CapabilitySummary health={health} compact />
        <p className="hero-status-footnote">上传上限：{formatBytes(health?.limits.max_docx_size_bytes)}</p>
      </GlassPanel>
    </section>
  );
}
