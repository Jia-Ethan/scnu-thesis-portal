import { MinimalHome } from "../components/minimal/MinimalHome";
import { PrecheckModal } from "../components/minimal/PrecheckModal";
import { useMinimalExportFlow } from "./useMinimalExportFlow";

export function AppShell() {
  const flow = useMinimalExportFlow();

  return (
    <>
      <MinimalHome
        rawText={flow.rawText}
        selectedFile={flow.selectedFile}
        phase={flow.phase}
        exportProgress={flow.exportProgress}
        error={flow.inlineError}
        onTextChange={flow.handleTextChange}
        onUploadTrigger={flow.handleUploadTrigger}
        onFileSelect={flow.handleFileSelect}
        onSubmit={flow.handlePrecheck}
        onClear={flow.clearAll}
        sourceTab={flow.sourceTab}
        onSourceTabChange={flow.setSourceTab}
        aiPhase={flow.aiPhase}
        researchPrompt={flow.researchPrompt}
        paperId={flow.paperId}
        currentAgent={flow.currentAgent}
        sectionIndex={flow.sectionIndex}
        revisionRound={flow.revisionRound}
        aiError={flow.aiError}
        coverFields={flow.coverFields}
        onResearchPromptChange={flow.setResearchPrompt}
        onCoverFieldsChange={flow.setCoverFields}
        onAIGenerate={flow.handleAIGenerate}
        onAIClear={flow.handleAIClear}
      />
      <PrecheckModal open={flow.previewModalOpen} precheck={flow.precheck} onCancel={flow.handleCancelPreview} onConfirm={flow.handleConfirmExport} />
    </>
  );
}
