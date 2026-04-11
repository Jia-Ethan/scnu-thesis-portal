import { useState } from "react";
import type { WorkspaceStep } from "./domain";
import { useExportFlow } from "./useExportFlow";
import { useIntakeFlow } from "./useIntakeFlow";
import { useThesisEditor } from "./useThesisEditor";
import { useWorkspaceBoot } from "./useWorkspaceBoot";

export function useThesisWorkspace() {
  const { health, bootError } = useWorkspaceBoot();
  const editor = useThesisEditor(health);
  const intake = useIntakeFlow({ onParsed: editor.setParsedThesis });
  const exportFlow = useExportFlow({
    thesis: editor.currentThesis,
    readiness: editor.exportReadiness,
  });
  const [showDebug, setShowDebug] = useState(false);

  const step: WorkspaceStep = exportFlow.exporting ? "export" : intake.busy ? "recognizing" : editor.thesis ? "review" : "input";
  const error = intake.intakeError ?? exportFlow.exportError ?? bootError;
  const toast = exportFlow.exportToast ?? intake.intakeToast;

  function clearToast() {
    exportFlow.clearExportToast();
    intake.clearIntakeToast();
  }

  return {
    health,
    mode: intake.mode,
    selectedFile: intake.selectedFile,
    rawText: intake.rawText,
    thesis: editor.thesis,
    currentThesis: editor.currentThesis,
    exportReadiness: editor.exportReadiness,
    busy: intake.busy,
    exporting: exportFlow.exporting,
    error,
    showDebug,
    toast,
    step,
    setShowDebug,
    clearToast,
    handleModeChange: intake.handleModeChange,
    handleFileChange: intake.handleFileChange,
    handleTextChange: intake.handleTextChange,
    handleParse: intake.handleParse,
    handleExport: exportFlow.handleExport,
    updateMetadata: editor.updateMetadata,
    updateAbstract: editor.updateAbstract,
    updateSection: editor.updateSection,
    addSection: editor.addSection,
    removeSection: editor.removeSection,
    updateReferences: editor.updateReferences,
    updateLongText: editor.updateLongText,
  };
}
