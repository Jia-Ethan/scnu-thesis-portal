import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export function PrimaryButton({ children, className = "", ...props }: ButtonProps) {
  return (
    <button className={`button button-primary ${className}`.trim()} {...props}>
      {children}
    </button>
  );
}

export function SecondaryButton({ children, className = "", ...props }: ButtonProps) {
  return (
    <button className={`button button-secondary ${className}`.trim()} {...props}>
      {children}
    </button>
  );
}

export function GhostDangerButton({ children, className = "", ...props }: ButtonProps) {
  return (
    <button className={`button button-ghost-danger ${className}`.trim()} {...props}>
      {children}
    </button>
  );
}
