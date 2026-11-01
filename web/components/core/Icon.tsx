export interface IconProps {
  name: string;
  size?: number;
  fill?: boolean;
  className?: string;
}

/** Material Symbols Rounded. Outline by default; only the active nav tab uses fill. */
export function Icon({ name, size, fill, className }: IconProps) {
  return (
    <span
      className={`icon${fill ? " icon--fill" : ""}${className ? ` ${className}` : ""}`}
      style={size ? ({ "--icon-size": `${size}px` } as React.CSSProperties) : undefined}
      aria-hidden="true"
    >
      {name}
    </span>
  );
}
