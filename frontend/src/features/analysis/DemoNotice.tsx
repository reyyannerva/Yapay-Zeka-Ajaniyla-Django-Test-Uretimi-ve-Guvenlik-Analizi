import { Badge } from '../../components/ui/StatusBadge';

/** Analiz ekranlarındaki DEMO uyarısı (Genel bakış'taki "Örnek veri" notuyla aynı görünüm). */
export function DemoNotice({ children }: { children?: string }) {
  return (
    <p className="flex flex-wrap items-center gap-2 text-sm text-muted">
      <Badge tone="muted">DEMO</Badge>
      <span>{children ?? 'Örnek veri: gerçek bir analiz, sandbox yürütmesi veya güvenlik taraması sonucu değildir.'}</span>
    </p>
  );
}
