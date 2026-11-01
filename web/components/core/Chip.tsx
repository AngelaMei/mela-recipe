export interface ChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean;
  count?: number;
}

export function Chip({ selected, count, children, type = "button", className, ...rest }: ChipProps) {
  return (
    <button type={type} className={`chip${className ? ` ${className}` : ""}`} aria-pressed={selected} {...rest}>
      {children}
      {count !== undefined && <span className="chip__count">{count}</span>}
    </button>
  );
}
