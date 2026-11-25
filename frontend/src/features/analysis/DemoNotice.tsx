/** Analiz ekranlarındaki DEMO uyarısı: gösterilen sonuçlar gerçek bir analiz çıktısı değildir. */
export function DemoNotice({ children }: { children?: string }) {
  return (
    <p className="inline-flex items-center gap-2 rounded-md border border-fail bg-fail-bg px-3 py-1.5 text-xs text-fg">
      <span className="font-mono font-semibold tracking-wider text-fail">DEMO</span>
      <span>{children ?? 'Örnek veri: gerçek bir analiz, sandbox yürütmesi veya güvenlik taraması sonucu değildir.'}</span>
    </p>
  );
}
