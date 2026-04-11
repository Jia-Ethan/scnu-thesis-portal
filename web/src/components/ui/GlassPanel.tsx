import type { HTMLAttributes, ReactNode } from "react";

type GlassPanelProps = HTMLAttributes<HTMLElement> & {
  as?: "section" | "article" | "aside" | "div";
  children: ReactNode;
};

export function GlassPanel({ as: Component = "section", children, className = "", ...props }: GlassPanelProps) {
  return (
    <Component className={`glass-panel ${className}`.trim()} {...props}>
      {children}
    </Component>
  );
}
