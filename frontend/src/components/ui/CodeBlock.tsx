import { useEffect, useRef, useState } from 'react';

export interface CodeBlockProps {
  /** Güvenilmeyen metin: yalnızca düz metin olarak çizilir, HTML olarak yorumlanmaz. */
  code: string;
  /** Erişilebilir ad (ör. "test_x Pytest kodu"). */
  label: string;
  /** Kopyalama düğmesini gösterir. */
  copyable?: boolean;
  /** Uzun çıktılarda kutunun en fazla yüksekliği (Tailwind sınıfı). */
  maxHeightClass?: string;
}

type CopyState = 'idle' | 'copied' | 'failed';

export function CodeBlock({ code, label, copyable = false, maxHeightClass = 'max-h-80' }: CodeBlockProps) {
  const [copy, setCopy] = useState<CopyState>('idle');
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  async function onCopy() {
    try {
      if (!navigator.clipboard) throw new Error('clipboard yok');
      await navigator.clipboard.writeText(code);
      setCopy('copied');
    } catch {
      setCopy('failed');
    }
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setCopy('idle'), 2000);
  }

  return (
    <div className="relative min-w-0">
      {copyable ? (
        <div className="absolute right-2 top-2 flex items-center gap-2">
          <span role="status" aria-live="polite" className="text-xs text-panel-muted">
            {copy === 'copied' ? 'Kopyalandı' : copy === 'failed' ? 'Kopyalanamadı' : ''}
          </span>
          <button
            type="button"
            onClick={onCopy}
            aria-label={`${label} kopyala`}
            className="rounded border border-panel-muted/40 bg-panel-2 px-2 py-0.5 text-xs text-panel-fg hover:border-panel-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-panel-accent"
          >
            Kopyala
          </button>
        </div>
      ) : null}
      <pre
        aria-label={label}
        tabIndex={0}
        className={`overflow-auto rounded-lg bg-panel p-4 pr-24 font-mono text-xs leading-relaxed text-panel-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent ${maxHeightClass}`}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}
