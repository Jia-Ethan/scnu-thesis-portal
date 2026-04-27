import { useEffect, useMemo, useState } from "react";
import { GuidePage } from "../components/minimal/GuidePage";
import { MinimalHome } from "../components/minimal/MinimalHome";
import { useMinimalExportFlow } from "./useMinimalExportFlow";

export function AppShell() {
  const [hash, setHash] = useState(() => window.location.hash);

  useEffect(() => {
    function handleHashChange() {
      setHash(window.location.hash);
    }

    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    if (hash.startsWith("#/") && hash !== "#/guide") {
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
      setHash("");
    }
  }, [hash]);

  const route = useMemo(() => {
    if (hash === "#/guide") return "guide";
    return "home";
  }, [hash]);

  return route === "guide" ? <GuidePage /> : <HomeRoute />;
}

function HomeRoute() {
  const flow = useMinimalExportFlow();

  return (
    <MinimalHome
      requirementText={flow.requirementText}
      selectedFile={flow.selectedFile}
      phase={flow.phase}
      precheck={flow.precheck}
      fixApplied={flow.fixApplied}
      exportProgress={flow.exportProgress}
      exportMessage={flow.exportMessage}
      error={flow.inlineError}
      canRetryExport={flow.canRetryExport}
      onRequirementChange={flow.handleRequirementChange}
      onUseExampleRequirement={flow.handleUseExampleRequirement}
      onUploadTrigger={flow.handleUploadTrigger}
      onFileSelect={flow.handleFileSelect}
      onPrecheck={flow.handlePrecheck}
      onApplyMockFix={flow.handleApplyMockFix}
      onExport={flow.handleConfirmExport}
      onCancelExport={flow.handleCancelExport}
      onRetryExport={flow.handleRetryExport}
      onClear={flow.clearAll}
    />
  );
}
