"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";

import { Icon } from "../core/Icon";

interface BaseProps {
  label?: string;
  hideLabel?: boolean;
  icon?: string;
  helper?: React.ReactNode;
  helperTone?: "default" | "success";
  helperIcon?: string;
  end?: React.ReactNode;
}

export type TextFieldProps = BaseProps & React.InputHTMLAttributes<HTMLInputElement>;

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, hideLabel, icon, helper, helperTone = "default", helperIcon, end, id, className, ...rest },
  ref,
) {
  return (
    <label className={`field${className ? ` ${className}` : ""}`} htmlFor={id}>
      {label && <span className={hideLabel ? "visually-hidden" : "field__label"}>{label}</span>}
      <span className="field__control">
        {icon && <Icon name={icon} size={22} />}
        <input ref={ref} id={id} className="field__input" {...rest} />
        {end}
      </span>
      {helper && <Helper tone={helperTone} icon={helperIcon}>{helper}</Helper>}
    </label>
  );
});

export type TextAreaProps = BaseProps & React.TextareaHTMLAttributes<HTMLTextAreaElement> & { autoGrow?: boolean };

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea(
  { label, hideLabel, icon, helper, helperTone = "default", helperIcon, id, className, autoGrow = true, value, ...rest },
  ref,
) {
  const inner = useRef<HTMLTextAreaElement>(null);
  useImperativeHandle(ref, () => inner.current as HTMLTextAreaElement);
  useEffect(() => {
    const el = inner.current;
    if (!autoGrow || !el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 360)}px`;
  }, [value, autoGrow]);
  return (
    <label className={`field${className ? ` ${className}` : ""}`} htmlFor={id}>
      {label && <span className={hideLabel ? "visually-hidden" : "field__label"}>{label}</span>}
      <span className="field__control field__control--multiline">
        {icon && <Icon name={icon} size={22} />}
        <textarea ref={inner} id={id} className="field__input" value={value} {...rest} />
      </span>
      {helper && <Helper tone={helperTone} icon={helperIcon}>{helper}</Helper>}
    </label>
  );
});

function Helper({ tone, icon, children }: { tone: "default" | "success"; icon?: string; children: React.ReactNode }) {
  return (
    <span className={`field__helper${tone === "success" ? " field__helper--success" : ""}`} aria-live="polite">
      {icon && <Icon name={icon} size={16} />}
      <span>{children}</span>
    </span>
  );
}
