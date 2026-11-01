export function Badge({ count, className }: { count: number; className?: string }) {
  if (count <= 0) return null;
  return (
    <span className={`badge${className ? ` ${className}` : ""}`} aria-hidden="true">
      {count > 99 ? "99+" : count}
    </span>
  );
}
