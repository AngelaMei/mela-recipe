export interface StepRowProps {
  index: number;
  text: string;
  onMerge?: () => void;
  mergeLabel?: string;
}

export function StepRow({ index, text, onMerge, mergeLabel }: StepRowProps) {
  return (
    <li className="step-row">
      <span className="step-row__num">{index + 1}</span>
      <div>
        <div className="step-row__text">{text}</div>
        {onMerge && (
          <button type="button" className="step-row__merge" onClick={onMerge}>
            {mergeLabel}
          </button>
        )}
      </div>
    </li>
  );
}
