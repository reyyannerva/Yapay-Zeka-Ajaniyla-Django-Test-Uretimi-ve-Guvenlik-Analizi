import { useMemo, useState } from 'react';

import { Card } from '../../components/ui/Card';
import { CodeBlock } from '../../components/ui/CodeBlock';
import { ToggleButton } from '../../components/ui/ToggleButton';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { HttpMethodBadge } from '../../components/ui/HttpMethodBadge';
import { Badge } from '../../components/ui/StatusBadge';
import { Spinner } from '../../components/ui/Spinner';
import { METHOD_LABEL, TEST_METHOD_LABEL, VALIDATION_META } from '../../lib/analysis-labels';
import type { EndpointAnalysis, GeneratedTest, TestGenerationMethod } from '../../types';
import { ModelInfo } from './ModelInfo';
import { useAnalysisContext, useEndpoints, useGeneratedTests } from './useAnalysisData';

type MethodFilter = 'ALL' | TestGenerationMethod;

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="text-sm text-fg">{children}</dd>
    </div>
  );
}

function TestDetail({ test, endpoint }: { test: GeneratedTest; endpoint: EndpointAnalysis | undefined }) {
  const validation = VALIDATION_META[test.validation_status];
  return (
    <Card className="flex min-w-0 flex-col gap-4" role="region" aria-label="Test ayrıntısı">
      <div className="flex flex-col gap-2">
        <h2 className="break-all font-mono text-sm font-semibold text-fg">{test.test_name}</h2>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="muted">{TEST_METHOD_LABEL[test.generation_method]}</Badge>
          <Badge tone={validation.tone}>{validation.label}</Badge>
          {test.is_security_test ? <Badge tone="muted">Güvenlik testi</Badge> : null}
        </div>
      </div>
      <dl className="grid gap-3 sm:grid-cols-2">
        <Fact label="Hedef endpoint">
          {endpoint ? (
            <span className="inline-flex flex-wrap items-center gap-2">
              <HttpMethodBadge method={endpoint.http_method} />
              <code className="break-all font-mono text-xs">{endpoint.path}</code>
            </span>
          ) : (
            <span className="text-muted">Endpoint bağlantısı yok</span>
          )}
        </Fact>
        <Fact label="Rol / beklenen yanıt">{`${test.role || '—'} · ${test.expected_status ?? '—'}`}</Fact>
        <Fact label="Referans kural">{test.requirement_code ? <code className="font-mono text-xs">{test.requirement_code}</code> : '—'}</Fact>
        <Fact label="Düzeltme denemesi">{test.repair_count}</Fact>
      </dl>
      {test.validation_errors.length > 0 ? (
        <ul className="flex flex-col gap-1 rounded-md border border-error bg-error-bg p-3 text-xs text-fg">
          {test.validation_errors.map((e) => (
            <li key={e} className="break-words font-mono">
              {e}
            </li>
          ))}
        </ul>
      ) : null}
      <p className="text-xs text-muted">
        Sözdizimi ve politika doğrulaması testin çalıştırıldığını veya geçtiğini göstermez; yürütme sonucu “Test sonuçları” sekmesindedir.
      </p>
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-fg">Sağlayıcı ve model</h3>
        <ModelInfo test={test} />
      </div>
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-fg">
          Pytest kodu <span className="font-normal text-muted">{test.test_module}</span>
        </h3>
        <CodeBlock code={test.source_code} label={`${test.test_name} Pytest kodu`} copyable />
      </div>
    </Card>
  );
}

export function GeneratedTestsPage() {
  const { run } = useAnalysisContext();
  const tests = useGeneratedTests(run.id);
  const endpoints = useEndpoints(run.id);
  const [method, setMethod] = useState<MethodFilter>('ALL');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const rows = tests.data ?? [];
  const visible = useMemo(() => rows.filter((t) => method === 'ALL' || t.generation_method === method), [rows, method]);
  const counts = useMemo(
    () => ({
      rule: rows.filter((t) => t.generation_method === 'RULE_BASED').length,
      llm: rows.filter((t) => t.generation_method === 'LLM').length,
      fallback: rows.filter((t) => t.generation_metadata.fallback_used === true).length,
      invalid: rows.filter((t) => t.validation_status === 'INVALID_SYNTAX' || t.validation_status === 'REJECTED_POLICY').length,
    }),
    [rows],
  );

  if (tests.isLoading) return <Spinner label="Testler yükleniyor" />;
  if (tests.isError) return <ErrorState title="Üretilen testler alınamadı" description="Lütfen sayfayı yenileyip tekrar deneyin." />;
  if (rows.length === 0) {
    return run.status === 'QUEUED' || run.status === 'ANALYZING' || run.status === 'GENERATING' ? (
      <EmptyState title="Test üretimi henüz tamamlanmadı" description="Üretilen testler bu aşama bitince listelenir." />
    ) : (
      <EmptyState title="Test üretilmedi" description="Bu analizde desteklenen endpoint bulunmadığı veya analiz erken durduğu için test üretilmedi." />
    );
  }

  const selected = visible.find((t) => t.id === selectedId) ?? visible[0];
  const endpointOf = (t: GeneratedTest) => endpoints.data?.find((e) => e.id === t.endpoint);

  return (
    <section aria-label="Otomatik Pytest üretimi" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted">
        <span>{`Analiz yöntemi: ${METHOD_LABEL[run.method]}`}</span>
        <span>{`${rows.length} test · ${counts.rule} kural tabanlı · ${counts.llm} LLM`}</span>
        <span>{`${counts.fallback} testte fallback`}</span>
        <span>{`${counts.invalid} test doğrulamadan geçmedi`}</span>
      </div>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Üretim yöntemi">
        {(['ALL', 'RULE_BASED', 'LLM'] as const).map((m) => (
          <ToggleButton key={m} pressed={method === m} onClick={() => setMethod(m)}>
            {m === 'ALL' ? 'Tümü' : TEST_METHOD_LABEL[m]}
          </ToggleButton>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <ul className="flex min-w-0 flex-col gap-1 self-start rounded-lg border border-border bg-surface p-2" aria-label="Üretilen testler">
          {visible.map((t) => {
            const ep = endpointOf(t);
            const active = selected?.id === t.id;
            return (
              <li key={t.id}>
                <button
                  type="button"
                  aria-current={active ? 'true' : undefined}
                  onClick={() => setSelectedId(t.id)}
                  className={`flex w-full flex-col gap-1 rounded-md px-3 py-2 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent ${
                    active ? 'bg-accent-soft' : 'hover:bg-surface-2'
                  }`}
                >
                  <span className="break-all font-mono text-xs font-medium text-fg">{t.test_name}</span>
                  <span className="flex flex-wrap items-center gap-2 text-xs text-muted">
                    {ep ? <HttpMethodBadge method={ep.http_method} /> : null}
                    <span className="break-all">{ep?.path ?? '—'}</span>
                    <span>{`· ${TEST_METHOD_LABEL[t.generation_method]}`}</span>
                    {t.generation_metadata.fallback_used ? <span className="text-fail">· fallback</span> : null}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
        {selected ? <TestDetail test={selected} endpoint={endpointOf(selected)} /> : null}
      </div>
    </section>
  );
}
