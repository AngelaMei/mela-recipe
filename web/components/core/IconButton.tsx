import { forwardRef } from "react";

import { Icon } from "./Icon";

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: string;
  label: string; // required: icon-only buttons always have aria-label
  variant?: "default" | "overlay" | "plain" | "dark-square";
  iconSize?: number;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { icon, label, variant = "default", iconSize = 22, className, type = "button", ...rest },
  ref,
) {
  const cls = ["icon-btn", variant !== "default" && `icon-btn--${variant}`, className].filter(Boolean).join(" ");
  return (
    <button ref={ref} type={type} className={cls} aria-label={label} title={label} {...rest}>
      <Icon name={icon} size={iconSize} />
    </button>
  );
});
