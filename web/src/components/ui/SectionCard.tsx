import type { ReactNode } from "react";

type SectionCardProps = {
  title?: string;
  eyebrow?: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function SectionCard({ title, eyebrow, description, action, children, className = "" }: SectionCardProps) {
  return (
    <section className={`section-card ${className}`.trim()}>
      {(title || eyebrow || description || action) && (
        <div className="section-card-header">
          <div>
            {eyebrow ? <p className="section-eyebrow">{eyebrow}</p> : null}
            {title ? <h2>{title}</h2> : null}
            {description ? <p className="section-description">{description}</p> : null}
          </div>
          {action ? <div className="section-action">{action}</div> : null}
        </div>
      )}
      {children}
    </section>
  );
}
