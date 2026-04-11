import type { ReactNode } from "react";

type FieldGroupProps = {
  label: string;
  htmlFor?: string;
  hint?: string;
  error?: string;
  children: ReactNode;
};

export function FieldGroup({ label, htmlFor, hint, error, children }: FieldGroupProps) {
  return (
    <div className={error ? "field-group field-group-error" : "field-group"}>
      <label htmlFor={htmlFor}>{label}</label>
      {children}
      {hint ? <p className="field-hint">{hint}</p> : null}
      {error ? <p className="field-error">{error}</p> : null}
    </div>
  );
}
