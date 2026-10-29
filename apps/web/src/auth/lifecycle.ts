// Memory-only generation fence. Contains no cookie, password, MFA code or CSRF value.
let revision = 0;
export const authRevision = () => revision;
export const advanceAuthRevision = () => ++revision;
export const MFA_MESSAGE =
  'Pentru această acțiune trebuie să reconfirmi autentificarea în doi pași.';

export const authMessages: Record<string, string> = {
  LOGIN_REQUIRED: 'Autentifică-te și verifică autentificarea în doi pași pentru a continua.',
  SESSION_EXPIRED: 'Sesiunea a expirat sau a fost revocată. Autentifică-te din nou.',
  LOGIN_INVALID: 'Numele de utilizator sau parola nu sunt corecte.',
  MFA_INVALID:
    'Codul MFA este invalid, expirat sau deja folosit. Folosește un cod nou din autentificator.',
  MFA_RECENT_REQUIRED: MFA_MESSAGE,
  MFA_REQUIRED: 'Completează autentificarea în doi pași pentru a continua.',
  CSRF_FAILED:
    'Protecția cererii nu mai corespunde sesiunii. Actualizăm sesiunea; verifică și retrimite acțiunea.',
  ROLE_REQUIRED: 'Această acțiune este disponibilă numai proprietarului.',
  ORIGIN_REJECTED:
    'Originea cererii nu este permisă. Folosește aceeași adresă a aplicației pe tot parcursul autentificării.',
  AUTH_STATE_CHANGED:
    'Sesiunea s-a schimbat între timp. Reîncarcă informațiile înainte de o nouă acțiune.',
};
const details: Record<string, string> = {
  'Authentication required': 'LOGIN_REQUIRED',
  'Session expired or revoked': 'SESSION_EXPIRED',
  'Invalid credentials': 'LOGIN_INVALID',
  'Invalid, expired or already used MFA code': 'MFA_INVALID',
  'Recent MFA verification required': 'MFA_RECENT_REQUIRED',
  AI_RECENT_MFA_REQUIRED: 'MFA_RECENT_REQUIRED',
  AI_SESSION_EXPIRED: 'SESSION_EXPIRED',
  'Complete MFA before accessing management records': 'MFA_REQUIRED',
  'Owner role required': 'ROLE_REQUIRED',
  'CSRF validation failed': 'CSRF_FAILED',
  'Origin rejected': 'ORIGIN_REJECTED',
  'Cross-site request rejected': 'ORIGIN_REJECTED',
};
export function authCode(header: string | null, detail: unknown): string {
  if (header && Object.hasOwn(authMessages, header)) return header;
  return typeof detail === 'string' && Object.hasOwn(details, detail) ? details[detail] : '';
}
export const rotatesSession = (path: string) =>
  [
    '/auth/login',
    '/auth/bootstrap',
    '/auth/mfa/verify',
    '/auth/mfa/confirm',
    '/auth/mfa/recover',
    '/auth/reauthenticate',
    '/auth/logout',
    '/auth/password',
    '/auth/sessions/revoke-all',
  ].includes(path);
