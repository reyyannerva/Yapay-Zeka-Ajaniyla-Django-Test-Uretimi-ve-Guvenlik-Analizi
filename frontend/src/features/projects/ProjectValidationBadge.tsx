import { Badge } from '../../components/ui/StatusBadge';
import type { Tone } from '../../components/ui/StatusBadge';
import type { ProjectValidationStatus } from '../../types';

const META: Record<ProjectValidationStatus, { label: string; tone: Tone }> = {
  PENDING: { label: 'Bekliyor', tone: 'muted' },
  VALID: { label: 'Doğrulandı', tone: 'pass' },
  INVALID: { label: 'Geçersiz', tone: 'error' },
};

export function ProjectValidationBadge({ status }: { status: ProjectValidationStatus }) {
  const meta = META[status];
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('tr-TR', { dateStyle: 'medium', timeZone: 'UTC' });
}
