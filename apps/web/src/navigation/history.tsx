import { useEffect, useState } from 'react';
import type { AnchorHTMLAttributes, MouseEvent } from 'react';
import { resolveRoute } from './routes';

export function navigate(path: string, replace = false) {
  if (resolveRoute(path).screen === 'not-found') return;
  if (window.location.pathname !== path)
    window.history[replace ? 'replaceState' : 'pushState']({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
export function useRoute() {
  const [route, setRoute] = useState(() => resolveRoute(window.location.pathname));
  useEffect(() => {
    const update = () => setRoute(resolveRoute(window.location.pathname));
    window.addEventListener('popstate', update);
    return () => window.removeEventListener('popstate', update);
  }, []);
  return route;
}
export function Link({
  href,
  onClick,
  ...props
}: AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) {
  return (
    <a
      {...props}
      href={href}
      onClick={(event: MouseEvent<HTMLAnchorElement>) => {
        onClick?.(event);
        if (
          !event.defaultPrevented &&
          event.button === 0 &&
          !event.metaKey &&
          !event.ctrlKey &&
          !event.shiftKey &&
          !event.altKey &&
          !props.target
        ) {
          event.preventDefault();
          navigate(href);
        }
      }}
    />
  );
}
