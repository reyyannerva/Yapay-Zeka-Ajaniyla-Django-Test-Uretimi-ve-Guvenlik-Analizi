import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Fragment, useId, useState } from 'react';
import type { ChangeEvent } from 'react';

import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { CodeBlock } from '../../components/ui/CodeBlock';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { ErrorState } from '../../components/ui/ErrorState';
import { HttpMethodBadge } from '../../components/ui/HttpMethodBadge';
import { Spinner } from '../../components/ui/Spinner';
import { Badge } from '../../components/ui/StatusBadge';
import { useToast } from '../../components/ui/Toast';
import { isApiError } from '../../lib/api/client';
import { errorMessage, flattenFieldErrors } from '../../lib/api/errors';
import {
  createReferenceRequirement,
  deleteReferenceRequirement,
  listReferenceRequirements,
  patchReferenceRequirement,
  replaceReferenceRequirement,
} from '../../lib/api/reference-requirements';
import { queryKeys } from '../../lib/queryKeys';
import type { ReferenceRequirement } from '../../types';
import { SAMPLE_REQUIREMENT_JSON, parseRequirementJson, toEditableJson } from './referenceJson';
import type { RequirementIssue } from './referenceJson';

const CATEGORY_LABEL: Record<ReferenceRequirement['category'], string> = {
  ROLE: 'Rol',
  ACCESS_RULE: 'Erişim kuralı',
  DEPLOY_EXPECTATION: 'Dağıtım beklentisi',
};

const MAX_JSON_FILE_BYTES = 1024 * 1024;

type EditorMode = { kind: 'create' } | { kind: 'edit'; item: ReferenceRequirement };

function IssueList({ issues, title }: { issues: RequirementIssue[]; title: string }) {
  return (
    <div role="alert" className="rounded-md border border-error bg-error-bg p-3 text-sm">
      <p className="font-semibold text-error">{title}</p>
      <ul className="mt-1 flex flex-col gap-0.5" data-testid="requirement-issues">
        {issues.map((issue, i) => (
          <li key={`${issue.index}-${issue.field}-${i}`} className="break-words">
            <span className="font-mono text-xs">{`#${issue.index} ${issue.field}`}</span>
            {`: ${issue.message}`}
          </li>
        ))}
      </ul>
    </div>
  );
}

function serverIssues(error: unknown, index: number): RequirementIssue[] {
  if (isApiError(error) && error.status === 400) {
    const fields = flattenFieldErrors(error.body);
    const entries = Object.entries(fields);
    if (entries.length > 0) return entries.map(([field, message]) => ({ index, field, message }));
  }
  return [{ index, field: '(sunucu)', message: errorMessage(error) }];
}

/**
 * Projenin referans gereksinimleri (H5-03 / #41): JSON yükleme/kaydetme (POST), görüntüleme (GET),
 * tam güncelleme (PUT), etkin/pasif (PATCH) ve silme (DELETE). Sahiplik ve şema doğrulaması sunucudadır.
 */
export function ReferenceRequirementsCard({ projectId }: { projectId: number }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const textareaId = useId();
  const requirements = useQuery({
    queryKey: queryKeys.referenceRequirements.list(),
    queryFn: ({ signal }) => listReferenceRequirements(signal),
  });
  const [mode, setMode] = useState<EditorMode | null>(null);
  const [text, setText] = useState('');
  const [issues, setIssues] = useState<RequirementIssue[]>([]);
  const [issueTitle, setIssueTitle] = useState('');
  const [saving, setSaving] = useState(false);
  const [openId, setOpenId] = useState<number | null>(null);
  const [pendingDelete, setPendingDelete] = useState<ReferenceRequirement | null>(null);
  const [deleteError, setDeleteError] = useState<string | undefined>();
  const [busyId, setBusyId] = useState<number | null>(null);

  const rows = (requirements.data ?? []).filter((r) => r.project === projectId);

  const refresh = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.referenceRequirements.all() }),
      // Yeni analizler etkin gereksinimlerin anlık görüntüsünü alır; analiz önbelleği etkilenmez.
    ]);

  function openEditor(next: EditorMode) {
    setMode(next);
    setIssues([]);
    setText(next.kind === 'edit' ? toEditableJson(next.item) : '');
  }

  function closeEditor() {
    setMode(null);
    setIssues([]);
    setText('');
  }

  async function onFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (file.size > MAX_JSON_FILE_BYTES) {
      setIssueTitle('Dosya okunamadı');
      setIssues([{ index: 1, field: '(dosya)', message: 'JSON dosyası en fazla 1 MiB olabilir.' }]);
      return;
    }
    setText(await file.text());
    setIssues([]);
  }

  async function onSave() {
    if (!mode || saving) return;
    const parsed = parseRequirementJson(text, projectId);
    if (!parsed.ok) {
      setIssueTitle('JSON doğrulanamadı; hiçbir kayıt gönderilmedi.');
      setIssues(parsed.issues);
      return;
    }
    if (mode.kind === 'edit' && parsed.items.length !== 1) {
      setIssueTitle('Düzenlemede tek bir gereksinim nesnesi olmalıdır.');
      setIssues([{ index: 1, field: '(JSON)', message: 'Dizi yerine tek nesne girin.' }]);
      return;
    }
    setSaving(true);
    setIssues([]);
    try {
      if (mode.kind === 'edit') {
        const [item] = parsed.items;
        try {
          await replaceReferenceRequirement(mode.item.id, { ...item!, source: mode.item.source ?? 'JSON_UPLOAD' });
          toast.show(`${item!.requirement_code} güncellendi.`, 'success');
          closeEditor();
        } catch (error) {
          setIssueTitle('Sunucu kaydı reddetti; değişiklik kaydedilmedi.');
          setIssues(serverIssues(error, 1));
        }
        return;
      }
      const failures: RequirementIssue[] = [];
      let saved = 0;
      // Sıralı gönderim: her kayıt ayrı doğrulanır; reddedilenler sunucu mesajıyla raporlanır.
      for (const [i, item] of parsed.items.entries()) {
        try {
          await createReferenceRequirement(item);
          saved += 1;
        } catch (error) {
          failures.push(...serverIssues(error, i + 1));
        }
      }
      if (failures.length === 0) {
        toast.show(`${saved} referans gereksinim kaydedildi.`, 'success');
        closeEditor();
      } else {
        setIssueTitle(
          saved > 0
            ? `${saved} kayıt kaydedildi; aşağıdaki ${parsed.items.length - saved} kayıt sunucu tarafından reddedildi.`
            : 'Sunucu kayıtları reddetti; hiçbir kayıt kaydedilmedi.',
        );
        setIssues(failures);
      }
    } finally {
      setSaving(false);
      await refresh();
    }
  }

  async function toggleActive(item: ReferenceRequirement) {
    setBusyId(item.id);
    try {
      await patchReferenceRequirement(item.id, { is_active: !item.is_active });
      toast.show(`${item.requirement_code} ${item.is_active ? 'pasifleştirildi' : 'etkinleştirildi'}.`, 'success');
    } catch (error) {
      toast.show(errorMessage(error), 'error');
    } finally {
      setBusyId(null);
      await refresh();
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setBusyId(pendingDelete.id);
    setDeleteError(undefined);
    try {
      await deleteReferenceRequirement(pendingDelete.id);
      toast.show(`${pendingDelete.requirement_code} silindi.`, 'success');
      setPendingDelete(null);
      await refresh();
    } catch (error) {
      setDeleteError(errorMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Card className="flex flex-col gap-4" role="region" aria-label="Referans gereksinimler">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-lg font-semibold">Referans gereksinimler</h2>
        {mode === null ? (
          <Button variant="ghost" onClick={() => openEditor({ kind: 'create' })}>
            JSON yükle
          </Button>
        ) : null}
      </div>
      <p className="text-sm text-muted">
        Kaynak koddan bağımsız beklenen davranışlar (rol, erişim kuralı, dağıtım beklentisi). Erişim kurallarında HTTP
        metodu GET, POST, PUT, PATCH veya DELETE olmalıdır; doğrulama sunucuda da yapılır.
      </p>

      {mode !== null ? (
        <div className="flex flex-col gap-3 rounded-lg border border-border p-4" aria-label="Referans JSON düzenleyici" role="group">
          <h3 className="text-sm font-semibold text-fg">
            {mode.kind === 'edit' ? `${mode.item.requirement_code} kaydını düzenle (PUT)` : 'Yeni referans gereksinim JSON'}
          </h3>
          {issues.length > 0 ? <IssueList issues={issues} title={issueTitle} /> : null}
          <div className="flex flex-col gap-1">
            <label htmlFor={textareaId} className="text-sm font-medium text-fg">
              JSON (tek nesne veya nesne dizisi)
            </label>
            <textarea
              id={textareaId}
              value={text}
              spellCheck={false}
              onChange={(e) => setText(e.target.value)}
              rows={12}
              placeholder={SAMPLE_REQUIREMENT_JSON}
              className="w-full rounded-md border border-border-strong bg-surface px-3 py-2 font-mono text-xs text-fg placeholder:text-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
            />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <label className="inline-flex cursor-pointer items-center gap-2 text-sm text-accent">
              <input type="file" accept=".json,application/json" className="sr-only" onChange={(e) => void onFile(e)} />
              <span className="rounded-md border border-border-strong px-3 py-1.5 font-medium text-fg hover:bg-surface-2">
                .json dosyası seç
              </span>
            </label>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={closeEditor} disabled={saving}>
                Vazgeç
              </Button>
              <Button onClick={() => void onSave()} disabled={saving || !text.trim()} aria-busy={saving}>
                {saving ? 'Kaydediliyor…' : 'Doğrula ve kaydet'}
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {requirements.isLoading ? (
        <Spinner label="Referans gereksinimler yükleniyor" />
      ) : requirements.isError ? (
        <ErrorState title="Referans gereksinimler alınamadı" description={errorMessage(requirements.error)} />
      ) : rows.length === 0 ? (
        <p className="rounded-md border border-dashed border-border-strong px-3 py-6 text-center text-sm text-muted">
          Bu proje için referans gereksinim yok.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border bg-surface">
          <table className="w-full min-w-[640px] border-collapse text-left text-sm">
            <thead className="bg-surface-2 text-xs text-muted">
              <tr>
                <th scope="col" className="border-b border-border px-4 py-2 font-medium">Kod</th>
                <th scope="col" className="border-b border-border px-4 py-2 font-medium">Kategori</th>
                <th scope="col" className="border-b border-border px-4 py-2 font-medium">Başlık</th>
                <th scope="col" className="border-b border-border px-4 py-2 font-medium">Durum</th>
                <th scope="col" className="border-b border-border px-4 py-2 font-medium">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => {
                const open = openId === item.id;
                return (
                  <Fragment key={item.id}>
                    <tr className="border-b border-border align-top last:border-b-0">
                      <td className="px-4 py-2">
                        <button
                          type="button"
                          aria-expanded={open}
                          onClick={() => setOpenId(open ? null : item.id)}
                          className="font-mono text-xs font-medium text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
                        >
                          {item.requirement_code}
                        </button>
                        <span className="block text-xs text-muted">{`r${item.revision}`}</span>
                      </td>
                      <td className="px-4 py-2">
                        <span className="flex flex-wrap items-center gap-2">
                          {CATEGORY_LABEL[item.category]}
                          {item.http_method ? <HttpMethodBadge method={item.http_method} /> : null}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-fg">{item.title}</td>
                      <td className="px-4 py-2">
                        <Badge tone={item.is_active ? 'pass' : 'muted'}>{item.is_active ? 'Etkin' : 'Pasif'}</Badge>
                      </td>
                      <td className="px-4 py-2">
                        <span className="flex flex-wrap gap-2">
                          <button type="button" className="text-xs font-medium text-accent hover:underline" onClick={() => openEditor({ kind: 'edit', item })}>
                            Düzenle
                          </button>
                          <button
                            type="button"
                            className="text-xs font-medium text-accent hover:underline disabled:opacity-50"
                            disabled={busyId === item.id}
                            onClick={() => void toggleActive(item)}
                          >
                            {item.is_active ? 'Pasifleştir' : 'Etkinleştir'}
                          </button>
                          <button
                            type="button"
                            className="text-xs font-medium text-error hover:underline"
                            onClick={() => {
                              setDeleteError(undefined);
                              setPendingDelete(item);
                            }}
                          >
                            Sil
                          </button>
                        </span>
                      </td>
                    </tr>
                    {open ? (
                      <tr className="border-b border-border">
                        <td colSpan={5} className="bg-surface-2 px-4 py-3">
                          <CodeBlock code={toEditableJson(item)} label={`${item.requirement_code} JSON`} maxHeightClass="max-h-64" />
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={pendingDelete !== null}
        destructive
        busy={busyId !== null && busyId === pendingDelete?.id}
        title="Referans gereksinimi sil"
        description={pendingDelete ? `"${pendingDelete.requirement_code}" kalıcı olarak silinecek. Mevcut analizlerin anlık görüntüleri değişmez.` : ''}
        confirmLabel="Sil"
        cancelLabel="Vazgeç"
        error={deleteError}
        onConfirm={() => void confirmDelete()}
        onCancel={() => setPendingDelete(null)}
      />
    </Card>
  );
}
