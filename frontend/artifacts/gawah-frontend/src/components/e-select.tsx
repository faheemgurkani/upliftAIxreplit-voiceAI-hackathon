import { useEffect, useId, useRef, useState } from 'react';

export type ESelectOption = {
  value: string;
  label: string;
};

type ESelectProps = {
  id?: string;
  value: string;
  options: readonly ESelectOption[];
  onChange: (value: string) => void;
  className?: string;
  'aria-label'?: string;
};

export function ESelect({
  id,
  value,
  options,
  onChange,
  className = '',
  'aria-label': ariaLabel,
}: ESelectProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const selected = options.find((o) => o.value === value) ?? options[0];

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  return (
    <div
      ref={rootRef}
      className={`e-select-wrap${open ? ' is-open' : ''}${className ? ` ${className}` : ''}`}
    >
      <button
        type="button"
        id={id}
        className="e-select-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={ariaLabel}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="e-select-value">{selected?.label ?? value}</span>
        <span className="e-select-chevron" aria-hidden>
          ▾
        </span>
      </button>
      {open && (
        <ul id={listId} className="e-select-menu" role="listbox" aria-labelledby={id}>
          {options.map((opt) => {
            const active = opt.value === value;
            return (
              <li key={opt.value} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={active}
                  className={`e-select-option${active ? ' is-active' : ''}`}
                  onClick={() => {
                    onChange(opt.value);
                    setOpen(false);
                  }}
                >
                  {opt.label}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
