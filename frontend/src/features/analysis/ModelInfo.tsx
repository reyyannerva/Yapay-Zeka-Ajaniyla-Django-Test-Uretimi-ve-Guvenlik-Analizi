import { PROVIDER_LABEL } from '../../lib/analysis-labels';
import type { GeneratedTest } from '../../types';

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="text-sm text-fg">{children}</dd>
    </div>
  );
}

const UNKNOWN = <span className="text-muted">Bilinmiyor</span>;

/**
 * Sağlayıcı / model / fallback bilgisi. Yalnızca backend'in döndürdüğü alanlar gösterilir:
 * fallback kullanıldığı açıkça bildirilmemişse "kullanıldı" denmez.
 */
export function ModelInfo({ test }: { test: GeneratedTest }) {
  if (test.generation_method === 'RULE_BASED') {
    return (
      <p className="text-sm text-muted" data-testid="model-info">
        Kural tabanlı üretim: dil modeli kullanılmadı.
      </p>
    );
  }
  const m = test.generation_metadata;
  const hasAny = m.provider || m.model || m.requested_provider || m.requested_model || m.fallback_used !== undefined;
  if (!hasAny) {
    return (
      <p className="text-sm text-muted" data-testid="model-info">
        Sağlayıcı ve model bilgisi backend tarafından döndürülmedi.
      </p>
    );
  }
  return (
    <dl className="grid gap-3 sm:grid-cols-2" data-testid="model-info">
      <Row label="İstenen sağlayıcı">{m.requested_provider ? PROVIDER_LABEL[m.requested_provider] : UNKNOWN}</Row>
      <Row label="Kullanılan sağlayıcı">{m.provider ? PROVIDER_LABEL[m.provider] : UNKNOWN}</Row>
      <Row label="İstenen model">{m.requested_model ? <code className="font-mono text-xs">{m.requested_model}</code> : UNKNOWN}</Row>
      <Row label="Kullanılan model">{m.model ? <code className="font-mono text-xs">{m.model}</code> : UNKNOWN}</Row>
      <Row label="Fallback">
        {m.fallback_used === true ? (
          <span className="inline-flex flex-wrap items-center gap-2">
            <span className="rounded border border-fail bg-fail-bg px-1.5 py-0.5 text-xs font-semibold text-fail">Fallback kullanıldı</span>
            {m.fallback_reason ? <span className="text-xs text-muted">{m.fallback_reason}</span> : null}
          </span>
        ) : m.fallback_used === false ? (
          'Kullanılmadı'
        ) : (
          UNKNOWN
        )}
      </Row>
      <Row label="İstem sürümü">{m.prompt_version ? <code className="font-mono text-xs">{m.prompt_version}</code> : UNKNOWN}</Row>
    </dl>
  );
}
