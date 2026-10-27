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
};
const drafts = new Map<string, ResearchDraft>();
export const readResearchDraft = (owner: string) => drafts.get(owner);
export const writeResearchDraft = (owner: string, value: ResearchDraft) => drafts.set(owner, value);
export const clearResearchDrafts = () => drafts.clear();
