type InlineErrorProps = {
  message?: string | null;
  actionLabel?: string;
  onAction?: () => void;
};

export function InlineError({ message, actionLabel, onAction }: InlineErrorProps) {
  return (
    <div className="inline-error" aria-live="polite">
      {message ? (
        <p>
          <span>{message}</span>
          {actionLabel && onAction ? (
            <button type="button" onClick={onAction}>
              {actionLabel}
            </button>
          ) : null}
        </p>
      ) : (
        <span>&nbsp;</span>
      )}
    </div>
  );
}
