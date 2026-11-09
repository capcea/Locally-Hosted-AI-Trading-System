import { afterEach, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import type { Job } from './api';
import { researchIdea } from './research-idea';
import { ResponseContent } from './AIChat';
import { clearResearchDrafts, offerResearchIdea, takeResearchIdea } from '../research-drafts';
import {
  clearAIQuestion,
  offerExperimentReview,
  takeAIQuestion,
  takeExperimentReview,
} from './draft';
import { resolveRoute } from '../navigation/routes';

const job: Job = {
  id: '11111111-1111-4111-8111-111111111111',
  kind: 'INFER',
  role: 'RESEARCH',
  state: 'SUCCEEDED',
  attempts: 1,
  cancel_requested: false,
  error: null,
  created_at: '2026-10-29T10:00:00Z',
  expires_at: new Date(Date.now() + 60000).toISOString(),
  retain_until: new Date(Date.now() + 3600000).toISOString(),
  model_output_verified_evidence: false,
  context_available: true,
  content_expired: false,
  output: {
    schema_version: 1,
    title: 'Ipoteză testabilă',
    hypothesis: 'O idee care necesită dovezi',
    test_plan: ['Include costuri'],
    evidence_refs: [],
    missing_evidence: { items: ['Date istorice'] },
    verified: false,
  },
};
afterEach(() => {
  clearResearchDrafts();
  clearAIQuestion();
});
it('offers a test preparation action only for an accessible completed research proposal', () => {
  const html = renderToStaticMarkup(
    <ResponseContent job={job} onCritic={() => undefined} onTest={() => undefined} />,
  );
  expect(html).toContain('Pregătește testul acestei idei');
  expect(html).toContain('Propunere AI neverificată');
  for (const patch of [
    { state: 'FAILED' },
    { role: 'CODING' },
    { kind: 'PROBE' },
    { content_expired: true },
    { context_available: false },
    { retain_until: '2000-01-01T00:00:00Z' },
  ]) {
    const invalid = { ...job, ...patch } as Job;
    expect(researchIdea(invalid)).toBeNull();
    expect(
      renderToStaticMarkup(
        <ResponseContent job={invalid} onCritic={() => undefined} onTest={() => undefined} />,
      ),
    ).not.toContain('Pregătește testul acestei idei');
  }
});
it('hands off only bounded proposal text without account, budget, acknowledgement or executable configuration', () => {
  const idea = researchIdea(job)!;
  offerResearchIdea('owner-a', idea);
  idea.title = 'Changed later';
  expect(takeResearchIdea('owner-a')?.title).toBe('Ipoteză testabilă');
  offerResearchIdea('owner-a', researchIdea(job)!);
  expect(takeResearchIdea('owner-b')).toBeUndefined();
  offerResearchIdea('owner-a', researchIdea(job)!);
  const taken = takeResearchIdea('owner-a')!;
  expect(taken.title).toBe('Ipoteză testabilă');
  expect(Object.keys(taken).sort()).toEqual([
    'hypothesis',
    'requestId',
    'retainUntil',
    'tests',
    'title',
  ]);
  expect(takeResearchIdea('owner-a')).toBeUndefined();
  offerResearchIdea('owner-a', researchIdea(job)!);
  clearResearchDrafts();
  expect(takeResearchIdea('owner-a')).toBeUndefined();
});
it('prepares an experiment critique as a draft, requiring a separate actual inference submission', () => {
  offerExperimentReview('owner', job.id);
  expect(takeAIQuestion('owner')).toContain('Critică rezultatul');
  expect(takeExperimentReview('other')).toBe('');
  offerExperimentReview('owner', job.id);
  expect(takeExperimentReview('owner')).toBe(job.id);
  expect(takeExperimentReview('owner')).toBe('');
  expect(resolveRoute(`/strategy-lab/analize/${job.id}`).jobId).toBe(job.id);
  expect(resolveRoute('/strategy-lab/analize/not-a-uuid').screen).toBe('not-found');
});
