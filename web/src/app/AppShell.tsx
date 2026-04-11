import { friendlyError } from "./domain";
import { useThesisWorkspace } from "./useThesisWorkspace";
import { HeroIntro, ProgressSteps, WorkspaceLayout } from "../components/layout";
import { InfoNotice, SecondaryButton, Toast } from "../components/ui";
import { ExportPanel } from "../features/export/ExportPanel";
import { CapabilitySummary } from "../features/health/CapabilitySummary";
import { IntakePanel } from "../features/intake/IntakePanel";
import { ReviewSummary } from "../features/review/ReviewSummary";
import { ReviewWorkspace } from "../features/review/ReviewWorkspace";

export function AppShell() {
  const workspace = useThesisWorkspace();
  const error = friendlyError(workspace.error);

  return (
    <div className="page-shell">
      <main className="page">
        <HeroIntro health={workspace.health} />

        <section className="workspace-section" aria-labelledby="workspace-title">
          <div className="workspace-heading">
            <div>
              <p className="section-eyebrow">Workspace</p>
              <h2 id="workspace-title">论文结构化工作区</h2>
            </div>
            <p>先完成输入与识别，再集中校对并导出。</p>
          </div>

          <ProgressSteps step={workspace.step} />

          {error ? (
            <InfoNotice title={error.title} tone="danger">
              <p>{error.message}</p>
              <p>{error.action}</p>
              {error.code ? <small>错误代码：{error.code}</small> : null}
            </InfoNotice>
          ) : null}

          {!workspace.thesis ? (
            <WorkspaceLayout
              main={
                <IntakePanel
                  health={workspace.health}
                  mode={workspace.mode}
                  selectedFile={workspace.selectedFile}
                  rawText={workspace.rawText}
                  busy={workspace.busy}
                  onModeChange={workspace.handleModeChange}
                  onFileChange={workspace.handleFileChange}
                  onTextChange={workspace.handleTextChange}
                  onSubmit={workspace.handleParse}
                />
              }
              side={
                <div className="side-stack">
                  <CapabilitySummary health={workspace.health} compact />
                  <InfoNotice title="建议路径">
                    <p>如果 Word 文档结构复杂，优先粘贴正文获取稳定的章节骨架，再手动补字段。</p>
                  </InfoNotice>
                </div>
              }
            />
          ) : (
            <>
              <WorkspaceLayout
                main={
                  <ReviewWorkspace
                    thesis={workspace.currentThesis}
                    readiness={workspace.exportReadiness}
                    updateMetadata={workspace.updateMetadata}
                    updateAbstract={workspace.updateAbstract}
                    updateSection={workspace.updateSection}
                    addSection={workspace.addSection}
                    removeSection={workspace.removeSection}
                    updateReferences={workspace.updateReferences}
                    updateLongText={workspace.updateLongText}
                  />
                }
                side={
                  <div className="side-stack">
                    <ReviewSummary thesis={workspace.currentThesis} />
                    <ExportPanel
                      thesis={workspace.currentThesis}
                      readiness={workspace.exportReadiness}
                      exporting={workspace.exporting}
                      onExport={workspace.handleExport}
                    />
                  </div>
                }
              />

              <section className="debug-section">
                <div className="debug-header">
                  <div>
                    <p className="section-eyebrow">Debug</p>
                    <h2>调试信息</h2>
                  </div>
                  <SecondaryButton type="button" onClick={() => workspace.setShowDebug((prev) => !prev)}>
                    {workspace.showDebug ? "隐藏 JSON" : "显示 JSON"}
                  </SecondaryButton>
                </div>
                {workspace.showDebug ? <pre className="debug-box">{JSON.stringify(workspace.currentThesis, null, 2)}</pre> : null}
              </section>
            </>
          )}
        </section>
      </main>

      <Toast toast={workspace.toast} onDismiss={workspace.clearToast} />
    </div>
  );
}
