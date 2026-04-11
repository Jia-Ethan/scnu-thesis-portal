import { WorkspaceStep, stepIndex } from "../../app/domain";

const steps = [
  { key: "input", label: "输入内容", description: "上传或粘贴论文文本" },
  { key: "recognizing", label: "结构识别", description: "抽取摘要、章节与参考文献" },
  { key: "review", label: "校对修正", description: "补全字段并检查正文" },
  { key: "export", label: "导出成果", description: "生成 .tex 工程 zip" },
] as const;

type ProgressStepsProps = {
  step: WorkspaceStep;
};

export function ProgressSteps({ step }: ProgressStepsProps) {
  const activeIndex = stepIndex(step);

  return (
    <nav className="progress-steps" aria-label="处理步骤">
      {steps.map((item, index) => {
        const state = index < activeIndex ? "done" : index === activeIndex ? "current" : "upcoming";
        return (
          <div
            key={item.key}
            className={`progress-step progress-step-${state}`}
            aria-current={state === "current" ? "step" : undefined}
          >
            <span className="progress-step-marker">{index + 1}</span>
            <span>
              <strong>{item.label}</strong>
              <small>{item.description}</small>
            </span>
          </div>
        );
      })}
    </nav>
  );
}
