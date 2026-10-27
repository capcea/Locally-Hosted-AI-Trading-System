import { useEffect, useId, useRef } from 'react';
import type { InputHTMLAttributes, SelectHTMLAttributes, ReactNode } from 'react';

export function Field({
  label,
  help,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; help?: string }) {
  const id = useId();
  return (
    <label className="management-field" htmlFor={id}>
      <span>{label}</span>
      <input {...props} id={id} aria-describedby={help ? `${id}-help` : undefined} />
      {help && <small id={`${id}-help`}>{help}</small>}
    </label>
  );
}
export function SelectField({
  label,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  const id = useId();
  return (
    <label className="management-field" htmlFor={id}>
      <span>{label}</span>
      <select {...props} id={id} aria-label={label}>
        {children}
      </select>
    </label>
  );
}
export function Notice({ children, error = false }: { children: ReactNode; error?: boolean }) {
  return (
    <div className={error ? 'error-banner' : 'notice'} role={error ? 'alert' : 'status'}>
      {children}
    </div>
  );
}
export function Evidence({
  value,
  title = 'Date tehnice originale',
}: {
  value: unknown;
  title?: string;
}) {
  return (
    <details>
      <summary>{title}</summary>
      <pre tabIndex={0} className="market-json">
        {JSON.stringify(value, null, 2)}
      </pre>
    </details>
  );
}
export function ConfirmDialog({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const dialog = ref.current!;
    dialog.showModal();
    return () => {
      dialog.close();
      trigger?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      aria-labelledby={id}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <h2 id={id}>{title}</h2>
      {children}
      <button type="button" className="secondary-button" onClick={onClose}>
        Renunță
      </button>
    </dialog>
  );
}
