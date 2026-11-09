import type { Job } from './api';

export type ResearchIdea = {
  requestId: string;
  retainUntil: string;
  title: string;
  hypothesis: string;
  tests: string[];
};
export function researchIdea(job: Job): ResearchIdea | null {
  if (
    job.kind !== 'INFER' ||
    job.role !== 'RESEARCH' ||
    job.state !== 'SUCCEEDED' ||
    job.content_expired ||
    !job.context_available ||
    !(Date.parse(job.retain_until) > Date.now())
  )
    return null;
  const output = job.output;
  if (
    !output ||
    typeof output !== 'object' ||
    !('hypothesis' in output) ||
    !('test_plan' in output) ||
    !('title' in output) ||
    !('verified' in output) ||
    output.verified !== false ||
    typeof output.title !== 'string' ||
    typeof output.hypothesis !== 'string' ||
    !Array.isArray(output.test_plan)
  )
    return null;
  return {
    requestId: job.id,
    retainUntil: job.retain_until,
    title: output.title.slice(0, 2000),
    hypothesis: output.hypothesis.slice(0, 2000),
    tests: output.test_plan
      .filter((v): v is string => typeof v === 'string')
      .slice(0, 12)
      .map((v) => v.slice(0, 2000)),
  };
}
