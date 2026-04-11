import type { ReactNode } from "react";

type WorkspaceLayoutProps = {
  main: ReactNode;
  side?: ReactNode;
};

export function WorkspaceLayout({ main, side }: WorkspaceLayoutProps) {
  return (
    <div className={side ? "workspace-layout" : "workspace-layout workspace-layout-single"}>
      <div className="workspace-main">{main}</div>
      {side ? <aside className="workspace-side">{side}</aside> : null}
    </div>
  );
}
