export type SegmentOption<T extends string> = {
  value: T;
  label: string;
  description?: string;
};

type SegmentedControlProps<T extends string> = {
  label: string;
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
};

export function SegmentedControl<T extends string>({ label, options, value, onChange }: SegmentedControlProps<T>) {
  return (
    <div className="segmented-control" role="tablist" aria-label={label}>
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={selected}
            className={selected ? "segment active" : "segment"}
            onClick={() => onChange(option.value)}
          >
            <span>{option.label}</span>
            {option.description ? <small>{option.description}</small> : null}
          </button>
        );
      })}
    </div>
  );
}
