/** Actual local observation time; its reserved width must not depend on the current digits. */
export function PublicReadTime({ at }: { at: number }) {
  const observed = new Date(at);
  return (
    <time data-visual-clock="true" dateTime={observed.toISOString()}>
      {observed.toLocaleTimeString('ro-RO', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hourCycle: 'h23',
      })}
    </time>
  );
}
