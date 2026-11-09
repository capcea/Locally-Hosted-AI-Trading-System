// One-use, owner-bound handoff only. No URL, localStorage, automatic request or rights acknowledgement.
let draft: { owner: string; question: string } | null = null;
let review: { owner: string; experiment: string } | null = null;
export function offerExperimentReview(owner: string, experiment: string) {
  offerAIQuestion(
    owner,
    'Critică rezultatul acestui experiment: costuri, mărimea eșantionului, limite, supraoptimizare și ce dovezi ar mai trebui. Nu trata profitul istoric ca promisiune.',
  );
  review = { owner, experiment };
}
export function takeExperimentReview(owner: string) {
  const current = review;
  review = null;
  return current?.owner === owner ? current.experiment : '';
}
export function offerAIQuestion(owner: string, question: string) {
  review = null;
  draft = { owner, question: question.trim().slice(0, 4000) };
}
export function takeAIQuestion(owner: string) {
  const current = draft;
  draft = null;
  return current?.owner === owner ? current.question : '';
}
export function clearAIQuestion() {
  draft = null;
  review = null;
}
