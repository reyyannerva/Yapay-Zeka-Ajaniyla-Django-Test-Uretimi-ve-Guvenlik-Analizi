import { useMemo, useState } from 'react';

import { Button } from '../../components/ui/Button';
import { DataTable } from '../../components/ui/DataTable';
import type { DataTableColumn } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { ToggleButton } from '../../components/ui/ToggleButton';
import { HttpMethodBadge } from '../../components/ui/HttpMethodBadge';
import { Spinner } from '../../components/ui/Spinner';
import { UNSUPPORTED_REASON_LABEL } from '../../lib/analysis-labels';
import type { AnalysisRunStatus, EndpointAnalysis, HttpMethod } from '../../types';
import { useAnalysisContext, useEndpoints } from './useAnalysisData';

export const HTTP_METHODS: readonly HttpMethod[] = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];

/** Kimlik doğrulama filtresi: kimlik doğrulama (kim olduğun) ile yetkilendirme (ne yapabildiğin) ayrıdır. */
export type AuthFilter = 'all' | 'declared' | 'unknown';
export type SupportFilter = 'all' | 'supported' | 'unsupported';

export interface EndpointFilters {
  methods: HttpMethod[];
  query: string;
  auth: AuthFilter;
  /** '' = tümü, '__none__' = izin sınıfı belirlenemedi, diğerleri sınıf adı. */
  permission: string;
  support: SupportFilter;
}

export const EMPTY_FILTERS: EndpointFilters = { methods: [], query: '', auth: 'all', permission: '', support: 'all' };
const NO_PERMISSION = '__none__';

export function filterEndpoints(rows: readonly EndpointAnalysis[], f: EndpointFilters): EndpointAnalysis[] {
  // Yol ve view adları kod tanımlayıcısıdır: Türkçe yerel ayarı (I → ı) eşleşmeyi bozacağı için
  // yerelden bağımsız küçük harfe çevrilir.
  const q = f.query.trim().toLowerCase();
  return rows.filter((e) => {
    if (f.methods.length > 0 && !f.methods.includes(e.http_method)) return false;
    if (q && !`${e.path} ${e.view_name}`.toLowerCase().includes(q)) return false;
    if (f.auth === 'declared' && e.auth_type === '') return false;
    if (f.auth === 'unknown' && e.auth_type !== '') return false;
    if (f.permission === NO_PERMISSION && e.permission_classes.length > 0) return false;
    if (f.permission && f.permission !== NO_PERMISSION && !e.permission_classes.includes(f.permission)) return false;
    if (f.support === 'supported' && !e.is_supported) return false;
    if (f.support === 'unsupported' && e.is_supported) return false;
    return true;
  });
}

function isFiltered(f: EndpointFilters): boolean {
  return (
    f.methods.length > 0 || f.query.trim() !== '' || f.auth !== 'all' || f.permission !== '' || f.support !== 'all'
  );
}

const COLUMNS: readonly DataTableColumn<EndpointAnalysis>[] = [
  { key: 'method', header: 'Metot', cell: (e) => <HttpMethodBadge method={e.http_method} /> },
  { key: 'path', header: 'URL', cell: (e) => <code className="break-all font-mono text-xs">{e.path}</code> },
  { key: 'view', header: 'View', cell: (e) => <code className="font-mono text-xs">{e.view_name}</code> },
  {
    key: 'auth',
    header: 'Kimlik doğrulama',
    cell: (e) => (e.auth_type ? e.auth_type : <span className="text-muted">Belirlenemedi</span>),
  },
  {
    key: 'perm',
    header: 'Yetkilendirme (izin sınıfı)',
    cell: (e) =>
      e.permission_classes.length > 0 ? (
        <code className="font-mono text-xs">{e.permission_classes.join(', ')}</code>
      ) : (
        <span className="text-muted">Belirlenemedi</span>
      ),
  },
  {
    key: 'support',
    header: 'Kapsam',
    cell: (e) =>
      e.is_supported ? (
        'Destekleniyor'
      ) : (
        <span className="text-muted">
          {`Kapsam dışı${e.unsupported_reason ? ` · ${UNSUPPORTED_REASON_LABEL[e.unsupported_reason]}` : ''}`}
        </span>
      ),
  },
];

const BEFORE_ANALYSIS: readonly AnalysisRunStatus[] = ['QUEUED', 'ANALYZING'];

export function EndpointsPage() {
  const { run } = useAnalysisContext();
  const endpoints = useEndpoints(run.id);
  const [filters, setFilters] = useState<EndpointFilters>(EMPTY_FILTERS);

  const rows = endpoints.data ?? [];
  const permissionOptions = useMemo(
    () => [...new Set(rows.flatMap((e) => e.permission_classes))].sort(),
    [rows],
  );
  const visible = useMemo(() => filterEndpoints(rows, filters), [rows, filters]);
  const methodCounts = useMemo(
    () => HTTP_METHODS.map((m) => [m, rows.filter((e) => e.http_method === m).length] as const),
    [rows],
  );

  if (endpoints.isLoading) return <Spinner label="Endpointler yükleniyor" />;
  if (endpoints.isError) {
    return <ErrorState title="Endpointler alınamadı" description="Lütfen sayfayı yenileyip tekrar deneyin." />;
  }
  if (rows.length === 0) {
    return BEFORE_ANALYSIS.includes(run.status) ? (
      <EmptyState title="Kaynak kod analizi henüz tamamlanmadı" description="Analiz aşaması bitince bulunan endpointler burada listelenir." />
    ) : (
      <EmptyState
        title="Endpoint bulunamadı"
        description="Bu analizde desteklenen bir URL/view yapısı tespit edilmedi; bu nedenle test üretilmedi."
      />
    );
  }

  const unsupported = rows.filter((e) => !e.is_supported).length;
  const toggleMethod = (m: HttpMethod) =>
    setFilters((f) => ({
      ...f,
      methods: f.methods.includes(m) ? f.methods.filter((x) => x !== m) : [...f.methods, m],
    }));

  return (
    <section aria-label="Kaynak kod analizi" className="flex flex-col gap-4">
      <p className="text-sm text-muted">
        {`${rows.length} endpoint tespit edildi; ${unsupported} tanesi analiz kapsamı dışında. Kaynak kod AST ile okunur, hedef uygulama çalıştırılmaz.`}
      </p>

      <fieldset className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-5">
        <legend className="float-left w-full font-display text-lg font-semibold text-fg">Filtreler</legend>
        <div className="flex flex-wrap items-center gap-2" role="group" aria-label="HTTP metodu">
          {methodCounts.map(([m, count]) => (
            <ToggleButton key={m} pressed={filters.methods.includes(m)} onClick={() => toggleMethod(m)} className="font-mono">
              {m}
              <span className="font-sans font-normal text-muted">{count}</span>
            </ToggleButton>
          ))}
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Input
            label="Endpoint veya view ara"
            type="search"
            value={filters.query}
            onChange={(e) => setFilters((f) => ({ ...f, query: e.target.value }))}
            placeholder="/api/orders/"
          />
          <Select
            label="Kimlik doğrulama"
            value={filters.auth}
            onChange={(e) => setFilters((f) => ({ ...f, auth: e.target.value as AuthFilter }))}
          >
            <option value="all">Tümü</option>
            <option value="declared">Kimlik doğrulama türü belirli</option>
            <option value="unknown">Belirlenemedi</option>
          </Select>
          <Select
            label="Yetkilendirme (izin sınıfı)"
            value={filters.permission}
            onChange={(e) => setFilters((f) => ({ ...f, permission: e.target.value }))}
          >
            <option value="">Tümü</option>
            {permissionOptions.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
            <option value={NO_PERMISSION}>Belirlenemedi</option>
          </Select>
          <Select
            label="Kapsam"
            value={filters.support}
            onChange={(e) => setFilters((f) => ({ ...f, support: e.target.value as SupportFilter }))}
          >
            <option value="all">Tümü</option>
            <option value="supported">Destekleniyor</option>
            <option value="unsupported">Kapsam dışı</option>
          </Select>
        </div>
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-muted" aria-live="polite">{`${visible.length} / ${rows.length} endpoint gösteriliyor`}</p>
          <Button variant="ghost" onClick={() => setFilters(EMPTY_FILTERS)} disabled={!isFiltered(filters)}>
            Filtreleri temizle
          </Button>
        </div>
      </fieldset>

      <DataTable
        columns={COLUMNS}
        rows={visible}
        rowKey={(e) => e.id}
        emptyState={
          <EmptyState
            title="Filtrelerle eşleşen endpoint yok"
            description="Filtreleri değiştirin veya temizleyin."
            action={
              <Button variant="ghost" onClick={() => setFilters(EMPTY_FILTERS)}>
                Filtreleri temizle
              </Button>
            }
          />
        }
      />
      <p className="text-xs text-muted">
        “Belirlenemedi”, bilginin kaynak koddan kesin olarak çıkarılamadığı anlamına gelir; uç nokta herkese açık veya güvenli sayılmaz.
      </p>
    </section>
  );
}
