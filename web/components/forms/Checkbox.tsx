import { Icon } from "../core/Icon";

/** Visual checkbox. The full row is the touch target (role="checkbox" lives on the row). */
export function Checkbox({ checked }: { checked: boolean }) {
  return (
    <span className={`checkbox${checked ? " checkbox--checked" : ""}`} aria-hidden="true">
      <Icon name="check" size={16} />
    </span>
  );
}
