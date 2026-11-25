import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { useToast } from '../../components/ui/Toast';
import { createAnalysisRun } from '../../lib/api/analysis-runs';
import { errorMessage, flattenFieldErrors } from '../../lib/api/errors';
import { isApiError } from '../../lib/api/client';
import { METHOD_LABEL, PROVIDER_LABEL } from '../../lib/analysis-labels';
import { queryKeys } from '../../lib/queryKeys';
import type { AnalysisMethod, LlmProvider, Project } from '../../types';

const METHODS: AnalysisMethod[] = ['RULE_BASED', 'DIRECT_LLM', 'HYBRID'];
const PROVIDERS: LlmProvider[] = ['GROQ', 'GEMINI', 'OLLAMA'];

/**
 * Analiz kaydı oluşturma (POST /api/analysis-runs/, H5-03 / #41). Backend kaydı QUEUED durumunda açar;
 * analiz motoru bu sürümde otomatik başlatılmaz. Proje sahipliği sunucuda doğrulanır.
 */
export function StartAnalysisCard({ project }: { project: Project }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const toast = useToast();
  const [method, setMethod] = useState<AnalysisMethod>('RULE_BASED');
  const [provider, setProvider] = useState<LlmProvider>('GROQ');
  const [model, setModel] = useState('');
  const [fallback, setFallback] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);

  const usesLlm = method !== 'RULE_BASED';

  const mutation = useMutation({
    mutationFn: createAnalysisRun,
    retry: false,
    onSuccess: async (run) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.analysisRuns.all() }),
        queryClient.invalidateQueries({ queryKey: queryKeys.projects.all() }),
      ]);
      toast.show(`Analiz kaydı #${run.id} oluşturuldu (kuyrukta).`, 'success');
      navigate(`/analyses/${run.id}`);
    },
    onError: (error) => {
      const fields = isApiError(error) && error.status === 400 ? flattenFieldErrors(error.body) : {};
      setFieldErrors(fields);
      const generic = fields.project ?? fields.non_field_errors;
      setFormError(Object.keys(fields).length === 0 ? errorMessage(error) : generic ?? null);
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (mutation.isPending) return; // çift gönderim engeli
    setFieldErrors({});
    setFormError(null);
    if (usesLlm && !model.trim()) {
      setFieldErrors({ llm_model: 'LLM yöntemlerinde model adı zorunludur.' });
      return;
    }
    mutation.mutate({
      project: project.id,
      method,
      llm_provider: usesLlm ? provider : null,
      llm_model: usesLlm ? model.trim() : null,
      fallback_enabled: fallback,
    });
  }

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-lg font-semibold">Analizler</h2>
        <Link
          to={`/analyses?project=${project.id}`}
          className="text-sm font-medium text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
        >
          {`Analizleri görüntüle (${project.analysis_run_count})`}
        </Link>
      </div>
      <p className="text-sm text-muted">
        Yeni analiz kaydı kuyrukta (QUEUED) oluşturulur. Bu sürümde analiz motoru otomatik başlatılmaz; kayıt ve
        projenin etkin referans gereksinimlerinin anlık görüntüsü veritabanına kaydedilir.
      </p>
      <form noValidate onSubmit={onSubmit} className="flex flex-col gap-4" aria-label="Analiz başlat">
        {formError ? (
          <div role="alert" className="rounded-md border border-error bg-error-bg p-3 text-sm">
            {formError}
          </div>
        ) : null}
        <div className="grid gap-3 sm:grid-cols-3">
          <Select label="Yöntem" value={method} onChange={(e) => setMethod(e.target.value as AnalysisMethod)}>
            {METHODS.map((m) => (
              <option key={m} value={m}>
                {METHOD_LABEL[m]}
              </option>
            ))}
          </Select>
          <Select
            label="LLM sağlayıcı"
            value={provider}
            disabled={!usesLlm}
            onChange={(e) => setProvider(e.target.value as LlmProvider)}
          >
            {PROVIDERS.map((p) => (
              <option key={p} value={p}>
                {PROVIDER_LABEL[p]}
              </option>
            ))}
          </Select>
          <Input
            label="Model"
            value={model}
            disabled={!usesLlm}
            placeholder={usesLlm ? 'ör. llama-3.3-70b-versatile' : 'Kural tabanlıda kullanılmaz'}
            error={fieldErrors.llm_model ?? fieldErrors.llm_provider}
            onChange={(e) => setModel(e.target.value)}
          />
        </div>
        <label className="inline-flex items-center gap-2 text-sm text-fg">
          <input
            type="checkbox"
            checked={fallback}
            onChange={(e) => setFallback(e.target.checked)}
            className="h-4 w-4 accent-[var(--accent)]"
          />
          Birincil model erişilemezse yedeğe (fallback) geçilsin
        </label>
        <div className="flex justify-end">
          <Button type="submit" disabled={mutation.isPending} aria-busy={mutation.isPending}>
            {mutation.isPending ? 'Oluşturuluyor…' : 'Analiz başlat'}
          </Button>
        </div>
      </form>
    </Card>
  );
}
