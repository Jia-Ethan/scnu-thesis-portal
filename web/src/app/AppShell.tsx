import { useEffect } from "react";
import { MinimalHome } from "../components/minimal/MinimalHome";
import { PrecheckModal } from "../components/minimal/PrecheckModal";
import { useMinimalExportFlow } from "./useMinimalExportFlow";

export function AppShell() {
  useEffect(() => {
    if (window.location.hash) {
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }
  }, []);

  return <HomeRoute />;
}

function HomeRoute() {
  const flow = useMinimalExportFlow();

  return (
    <>
      <MinimalHome
        rawText={flow.rawText}
        selectedFile={flow.selectedFile}
        phase={flow.phase}
        exportProgress={flow.exportProgress}
        exportMessage={flow.exportMessage}
        error={flow.inlineError}
        canRetryExport={flow.canRetryExport}
        onTextChange={flow.handleTextChange}
        onUploadTrigger={flow.handleUploadTrigger}
        onFileSelect={flow.handleFileSelect}
        onSubmit={flow.handlePrecheck}
        onCancelExport={flow.handleCancelExport}
        onRetryExport={flow.handleRetryExport}
        onClear={flow.clearAll}
      />
      <PrecheckModal open={flow.previewModalOpen} precheck={flow.precheck} onCancel={flow.handleCancelPreview} onConfirm={flow.handleConfirmExport} />
    </>
  );
}
