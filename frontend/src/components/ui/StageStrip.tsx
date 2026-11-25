import { STAGES, STATUS_META, stageIndex } from '../../lib/analysis-status';
import type { AnalysisProgress, AnalysisRunStatus } from '../../types';

export interface StageStripProps {
  status: AnalysisRunStatus;
  progress: Pick<AnalysisProgress, 'total' | 'percent'>;
}

type NodeState = 'done' | 'current' | 'upcoming';

const NODE_CLASSES: Record<NodeState, string> = {
  done: 'border-pass bg-pass-bg text-pass',
  current: 'border-process bg-process-bg text-process',
  upcoming: 'border-border-strong bg-surface text-muted',
};

export function StageStrip({ status, progress }: StageStripProps) {
  const terminalFailure = status === 'FAILED' || status === 'CANCELLED';
  const completed = status === 'COMPLETED';
  const activeIndex = terminalFailure ? -1 : stageIndex(status);

  function stateOf(index: number): NodeState {
    if (completed) return 'done';
    if (index < activeIndex) return 'done';
    if (index === activeIndex) return 'current';
    return 'upcoming';
  }

  const { percent } = progress;

  return (
    <div className="flex flex-col gap-3">
      <ol className="flex flex-wrap items-center gap-2" aria-label="Analiz aşamaları">
        {STAGES.map((stage, index) => {
          const state = stateOf(index);
          const isCurrent = state === 'current' && !completed;
          return (
            <li
              key={stage.key}
              aria-current={isCurrent ? 'step' : undefined}
              data-state={state}
              className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${NODE_CLASSES[state]}`}
            >
              <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
              {stage.label}
            </li>
          );
        })}
      </ol>

      {terminalFailure ? (
        <p
          role="status"
          className={`text-sm font-medium ${status === 'FAILED' ? 'text-error' : 'text-muted'}`}
        >
          {STATUS_META[status].label}
        </p>
      ) : null}

      {percent === null ? (
        <p className="text-sm text-muted">Henüz veri yok</p>
      ) : (
        <div className="flex items-center gap-3">
          <div
            role="progressbar"
            aria-label="Test ilerlemesi"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percent}
            className="h-2 flex-1 overflow-hidden rounded-full bg-surface-2"
          >
            <div
              className="h-full rounded-full bg-process"
              style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
            />
          </div>
          <span className="text-sm font-medium text-fg">{`%${percent}`}</span>
        </div>
      )}
    </div>
  );
}
