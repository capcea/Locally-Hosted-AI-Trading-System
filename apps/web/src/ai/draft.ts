// One-use, owner-bound handoff only. No URL, localStorage, automatic request or rights acknowledgement.
let draft: { owner: string; question: string } | null = null;
export function offerAIQuestion(owner: string, question: string) {
  draft = { owner, question: question.trim().slice(0, 4000) };
}
export function takeAIQuestion(owner: string) {
  const current = draft;
  draft = null;
  return current?.owner === owner ? current.question : '';
}
export function clearAIQuestion() {
  draft = null;
}
