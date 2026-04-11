import type { ReactNode } from "react";
import { StatusBadge } from "./StatusBadge";

type CapabilityCardProps = {
  label: string;
  value: string;
  detail?: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
};

export function CapabilityCard({ label, value, detail, tone = "neutral" }: CapabilityCardProps) {
  return (
    <article className="capability-card">
      <div className="capability-card-top">
        <span>{label}</span>
        <StatusBadge tone={tone}>{value}</StatusBadge>
      </div>
      {detail ? <p>{detail}</p> : null}
    </article>
  );
}
