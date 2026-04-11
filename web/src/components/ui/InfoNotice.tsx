import type { ReactNode } from "react";

type InfoNoticeProps = {
  title: string;
  children: ReactNode;
  tone?: "info" | "warning" | "danger" | "success";
};

export function InfoNotice({ title, children, tone = "info" }: InfoNoticeProps) {
  return (
    <div className={`info-notice info-notice-${tone}`} role={tone === "danger" ? "alert" : "note"}>
      <strong>{title}</strong>
      <div>{children}</div>
    </div>
  );
}
