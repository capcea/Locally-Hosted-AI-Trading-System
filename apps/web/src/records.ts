import { api } from './management-api';
import type { RecordItem, RecordPage } from './management-api';

/** Refuse to label a truncated catalog complete. */
export async function allRecords(kind: string): Promise<RecordItem[]> {
  const items: RecordItem[] = [];
  const ids = new Set<string>();
  let total: number | null = null;
  for (let offset = 0; offset < 10000; offset += 100) {
    const page = await api<RecordPage>(`/records/${kind}?offset=${offset}&limit=100`);
    if (total !== null && total !== page.total)
      throw new Error(
        'Catalogul nu a putut fi citit complet. Nu presupunem că înregistrările lipsă sunt sigure sau inexistente.',
      );
    total = page.total;
    for (const item of page.items) {
      if (ids.has(item.id))
        throw new Error(
          'Catalogul nu a putut fi citit complet. Nu presupunem că înregistrările lipsă sunt sigure sau inexistente.',
        );
      ids.add(item.id);
      items.push(item);
    }
    if (items.length >= page.total) return items;
    if (!page.items.length) break;
  }
  throw new Error(
    'Catalogul nu a putut fi citit complet. Nu presupunem că înregistrările lipsă sunt sigure sau inexistente.',
  );
}
