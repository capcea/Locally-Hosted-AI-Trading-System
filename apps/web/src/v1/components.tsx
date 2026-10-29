import type { LucideIcon } from 'lucide-react';
import { ArrowRight, CircleHelp } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link } from '../navigation/history';

export function Kpi({
  label,
  value,
  help,
  icon: Icon,
  tone = 'blue',
  valueKind = 'metric',
}: {
  label: string;
  value: ReactNode;
  help: string;
  icon: LucideIcon;
  tone?: 'blue' | 'violet' | 'green' | 'amber';
  valueKind?: 'metric' | 'status';
}) {
  return (
    <article className={`v1-kpi v1-tint-${tone}`}>
      <span className="v1-icon">
        <Icon size={25} aria-hidden="true" />
      </span>
      <div>
        <h3>{label}</h3>
        <strong className="v1-kpi-value" data-kind={valueKind}>
          {value}
        </strong>
        <p>{help}</p>
      </div>
    </article>
  );
}
export function CardTitle({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: LucideIcon;
  children?: ReactNode;
}) {
  return (
    <header className="v1-card-title">
      <h2>
        <span className="v1-icon">
          <Icon size={20} aria-hidden="true" />
        </span>
        {title}
      </h2>
      {children}
    </header>
  );
}
export function EmptyState({
  title,
  children,
  href,
  action,
  icon: Icon = CircleHelp,
}: {
  title: string;
  children: ReactNode;
  href?: string;
  action?: string;
  icon?: LucideIcon;
}) {
  return (
    <div className="v1-empty">
      <span className="v1-icon">
        <Icon size={28} aria-hidden="true" />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
      {href && action && (
        <Link className="secondary-button" href={href}>
          {action}
          <ArrowRight size={16} aria-hidden="true" />
        </Link>
      )}
    </div>
  );
}
export function StatusPill({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: 'neutral' | 'positive' | 'attention' | 'danger';
}) {
  return <span className={`v1-status v1-status-${tone}`}>{children}</span>;
}
