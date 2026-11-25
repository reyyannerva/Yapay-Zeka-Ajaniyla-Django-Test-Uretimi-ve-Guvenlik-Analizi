import type { HttpMethod } from '../../types';

// Metot rozetleri yalnızca nötr tema token'larını kullanır: metot bir güvenlik veya sonuç durumu
// değildir, bu yüzden başarı/hata renkleri verilmez. Metot adı her zaman yazıyla görünür.
const METHOD_CLASSES: Record<HttpMethod, string> = {
  GET: 'border-border-strong text-fg',
  POST: 'border-accent text-accent',
  PUT: 'border-accent text-accent',
  PATCH: 'border-accent text-accent',
  DELETE: 'border-fg text-fg',
};

export function HttpMethodBadge({ method }: { method: HttpMethod }) {
  return (
    <span
      data-method={method}
      className={`inline-flex min-w-[3.75rem] justify-center rounded border bg-surface px-1.5 py-0.5 font-mono text-[11px] font-semibold tracking-wide ${METHOD_CLASSES[method]}`}
    >
      {method}
    </span>
  );
}
