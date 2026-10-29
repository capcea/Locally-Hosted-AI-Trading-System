import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { AuthProvider } from '../auth/AuthProvider';
import { resolveRoute, primary } from '../navigation/routes';
import { activeSection } from '../navigation/sections';
import CampaignCenter from './CampaignCenter';
import { campaignErrors, campaignStates, decisions } from './copy';

describe('bounded campaign navigation and honest states', () => {
  it('retains five destinations and stable guarded campaign deep links', () => {
    expect(primary).toHaveLength(5);
    const route = resolveRoute('/testeaza/campanii/11111111-1111-4111-8111-111111111111');
    expect(route.screen).toBe('campaigns');
    expect(route.campaignId).toBe('11111111-1111-4111-8111-111111111111');
    expect(activeSection(route)).toBe('/testeaza/campanii');
    expect(resolveRoute('/testeaza/campanii/not-an-id').screen).toBe('not-found');
  });
  it('keeps missing-model and candidate labels distinct from execution approval', () => {
    expect(campaignErrors.MODEL_UNAVAILABLE).toContain('nu folosim automat o fixtură');
    expect(campaignStates.UNKNOWN).toContain('neconfirmată');
    expect(decisions.RESEARCH_CANDIDATE).toContain('fără aprobare');
  });
  it('does not manufacture progress or enable owner mutations without an owner', () => {
    vi.stubGlobal('window', { location: { pathname: '/testeaza/campanii' } });
    try {
      const html = renderToStaticMarkup(
        <AuthProvider>
          <CampaignCenter />
        </AuthProvider>,
      );
      expect(html).toContain('SIMULATED / DENY_ALL');
      expect(html).toContain('SYNTHETIC_FIXTURE');
      expect(html).toContain('MFA recentă');
      expect(html).toContain('disabled=""');
      expect(html).not.toContain('AI online');
      expect(html).not.toContain('3 idei');
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
