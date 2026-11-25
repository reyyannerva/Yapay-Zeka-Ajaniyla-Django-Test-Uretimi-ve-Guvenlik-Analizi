import { useEffect, useRef, useState } from 'react';

import { TestStatusIndicator } from '../../components/ui/TestStatusIndicator';
import type { GeneratedTest, TestExecutionResult, TestExecutionStatus } from '../../types';

export interface OutputLine {
  seq: number;
  testId: number;
  status: TestExecutionStatus;
  text: string;
}

const MAX_LINES = 50;

function lineText(r: TestExecutionResult, name: string): string {
  if (r.status === 'RUNNING') return `${name} başladı`;
  const summary = r.error_summary || (r.observed_status !== null ? `HTTP ${r.observed_status}` : '');
  return summary ? `${name} — ${summary}` : name;
}

/** Önceki ve yeni anlık görüntü arasında durumu değişen testler için çıktı satırları üretir. */
export function diffLines(
  prev: ReadonlyMap<number, TestExecutionStatus>,
  next: readonly TestExecutionResult[],
  nameOf: (id: number) => string,
  startSeq: number,
): OutputLine[] {
  const lines: OutputLine[] = [];
  let seq = startSeq;
  for (const r of next) {
    if (r.status === 'PENDING') continue;
    if (prev.get(r.generated_test) === r.status) continue;
    lines.push({ seq: seq++, testId: r.generated_test, status: r.status, text: lineText(r, nameOf(r.generated_test)) });
  }
  return lines;
}

/** Canlı test çıktısı: yalnızca düz metin; en yeni satır en üstte. */
export function LiveOutput({ results, tests }: { results: readonly TestExecutionResult[]; tests: readonly GeneratedTest[] }) {
  const [lines, setLines] = useState<OutputLine[]>([]);
  const prev = useRef<Map<number, TestExecutionStatus>>(new Map());
  const seq = useRef(0);

  useEffect(() => {
    const nameOf = (id: number) => tests.find((t) => t.id === id)?.test_name ?? `Test ${id}`;
    const added = diffLines(prev.current, results, nameOf, seq.current);
    seq.current += added.length;
    prev.current = new Map(results.map((r) => [r.generated_test, r.status]));
    if (added.length > 0) setLines((current) => [...added.reverse(), ...current].slice(0, MAX_LINES));
  }, [results, tests]);

  return (
    <section aria-label="Canlı test çıktısı" className="flex min-w-0 flex-col gap-2 rounded-lg border border-border bg-surface p-4">
      <h2 className="text-sm font-semibold text-fg">Canlı test çıktısı</h2>
      {lines.length === 0 ? (
        <p className="text-sm text-muted">Henüz çıktı yok.</p>
      ) : (
        <ol aria-live="polite" className="flex max-h-72 flex-col gap-1 overflow-auto rounded-md bg-panel p-3">
          {lines.map((l) => (
            <li key={l.seq} className="flex min-w-0 items-start gap-2">
              <TestStatusIndicator status={l.status} />
              <span className="break-all font-mono text-xs leading-5 text-panel-fg">{l.text}</span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
