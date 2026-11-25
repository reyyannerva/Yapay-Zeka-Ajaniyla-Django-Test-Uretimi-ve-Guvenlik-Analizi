// H5-05 (#43) çevrimdışı deney sonuçlarının tipli görünümü (H5-06 / #44).
// Veri `demo/h5_06/export_experiment_snapshot.py` ile metrics_summary.json'dan kopyalanır; burada
// hiçbir metrik yeniden hesaplanmaz. Ölçülemeyen değer `value: null` + "Ölçülemedi" olarak gelir.
import snapshot from '../../data/h5-05-experiment.json';

export interface ExactMetric {
  value: number | null;
  exact: string | null;
  display: string;
}

export interface MethodResult {
  key: 'rule_based' | 'llm' | 'hybrid';
  label: string;
  attempted: boolean;
  scenarios: number;
  confusion: { TP: number; FP: number; TN: number; FN: number; EXCLUDED: number };
  precision: ExactMetric;
  recall: ExactMetric;
  f1: ExactMetric;
  syntaxValid: { count: number; of: number };
  collected: { count: number; of: number };
  firstPassExecutable: ExactMetric & { count: number; of: number };
  testLevel: { executable: number; tests: number };
  status5: Record<'PASS' | 'FAIL' | 'ERROR' | 'TIMEOUT' | 'NOT_RUN', number>;
  targets: { f1: string; executability: string };
}

export interface LayerResult {
  key: 'A' | 'B';
  scenarios: number;
  splitName: string;
  positives: number;
  httpMethods: Record<string, number>;
  llmStatus: string;
  llmNote: string;
  llmModel: string | null;
  comparable: boolean;
  comparabilityReason: string;
  hybrid: {
    rule_based_candidates: number;
    llm_candidates: number;
    duplicates: number;
    merged: number;
    conflicts_resolved: number;
    conflicts_unresolved: number;
    final_tests: number;
    code_identical_pairs: number;
    semantic_key_equal_pairs: number;
  };
  methods: MethodResult[];
}

export interface ExperimentSnapshot {
  kind: 'OFFLINE_EXPERIMENT';
  issue: string;
  experimentId: string;
  source: string;
  sourceSha256: string;
  runTimestampUtc: string;
  model: string;
  plannedModel: string;
  promptVersion: string;
  targets: { f1: number; executability: number };
  layers: LayerResult[];
}

export const experiment = snapshot as unknown as ExperimentSnapshot;

export const LAYER_TITLES: Record<LayerResult['key'], string> = {
  A: "Katman A — H5-04'ün 20 geliştirme senaryosu",
  B: 'Katman B — kontrollü ek geliştirme kümesi (5 HTTP metodu, 3 bilinen kusur)',
};

/** "Karşılandı" dışındaki hedef durumları başarı gibi gösterilmez. */
export function targetTone(status: string): 'pass' | 'fail' | 'muted' {
  if (status === 'Karşılandı') return 'pass';
  if (status === 'Karşılanmadı') return 'fail';
  return 'muted';
}

/** 0–1 oranını yüzde olarak gösterir; ölçülemiyorsa metindeki "Ölçülemedi" korunur. */
export function formatRatio(m: ExactMetric): string {
  if (m.value === null) return m.display;
  return m.value.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
