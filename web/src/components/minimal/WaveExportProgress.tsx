type WaveExportProgressProps = {
  progress: number;
  message?: string;
  onCancel?: () => void;
};

export function WaveExportProgress({ progress, message = "正在生成 Word 文件", onCancel }: WaveExportProgressProps) {
  return (
    <div className="wave-progress" aria-live="polite" aria-label={`正在导出，当前进度 ${Math.round(progress)}%`}>
      <div className="wave-progress-track">
        <div className="wave-progress-fill" style={{ width: `${Math.max(progress, 6)}%` }}>
          <div className="wave-progress-ripple" />
        </div>
      </div>
      <div className="wave-progress-meta">
        <strong>{message}</strong>
        <span>{Math.round(progress)}%</span>
      </div>
      {onCancel ? (
        <button type="button" className="wave-progress-cancel" onClick={onCancel}>
          取消导出
        </button>
      ) : null}
    </div>
  );
}
