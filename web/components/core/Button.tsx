import { forwardRef } from "react";

import { Icon } from "./Icon";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "dark" | "secondary" | "ghost";
  size?: "md" | "sm";
  block?: boolean;
  icon?: string;
  done?: boolean;
}

/** One `primary` (terracotta) per screen. Labels start with a verb. */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "secondary", size = "md", block, icon, done, className, children, type = "button", ...rest },
  ref,
) {
  const cls = [
    "btn",
    `btn--${variant}`,
    size === "sm" && "btn--sm",
    block && "btn--block",
    done && "btn--done",
    className,
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <button ref={ref} type={type} className={cls} {...rest}>
      {icon && <Icon name={icon} size={size === "sm" ? 18 : 22} />}
      {children}
    </button>
  );
});
