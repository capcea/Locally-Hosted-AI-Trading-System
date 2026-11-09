import type { ResearchIdea } from './ai/research-idea';
// Memory only. Never store auth, acknowledgements, uploaded files or arbitrary JSON.
export type ResearchDraft = {
  account: string;
  dataset: string;
  templateId: string;
  strategy: string;
  step: number;
  requestKey: string;
  values: Record<string, string>;
  review: Record<string, string>;
  aiIdea?: ResearchIdea;
};
const drafts = new Map<string, ResearchDraft>();
export const readResearchDraft = (owner: string) => drafts.get(owner);
export const writeResearchDraft = (owner: string, value: ResearchDraft) => drafts.set(owner, value);
const ideas = new Map<string, ResearchIdea>();
export const offerResearchIdea = (owner: string, idea: ResearchIdea) =>
  ideas.set(owner, structuredClone(idea));
export const takeResearchIdea = (owner: string) => {
  const idea = ideas.get(owner);
  ideas.clear();
  return idea && Date.parse(idea.retainUntil) > Date.now() ? idea : undefined;
};
export const clearResearchDrafts = () => {
  drafts.clear();
  ideas.clear();
};
