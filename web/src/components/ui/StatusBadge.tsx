type StatusBadgeProps = {
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
  children: string;
};

export function StatusBadge({ tone = "neutral", children }: StatusBadgeProps) {
  return <span className={`status-badge status-badge-${tone}`}>{children}</span>;
}
