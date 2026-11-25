import type { ComponentType } from 'react';
import { Link } from 'react-router-dom';

import { EmptyState } from '../../components/ui/EmptyState';
import { useAnalysisContext } from './useAnalysisData';

/**
 * H5-02 sonuç ekranlarını yalnızca DEMO kaynağında çalıştırır. Gerçek analizlerde bu sonuç türleri için
 * backend servisi henüz bulunmadığından örnek veri gösterilmez; durum açıkça belirtilir (H5-03 / #41).
 */
export function demoOnly<P extends object>(Component: ComponentType<P>, resultName: string) {
  function DemoOnly(props: P) {
    const { source } = useAnalysisContext();
    if (source === 'demo') return <Component {...props} />;
    return (
      <EmptyState
        title={`${resultName} henüz bağlı değil`}
        description={`Bu analiz gerçek bir backend kaydıdır. ${resultName} için backend servisi bu sürümde bulunmadığından sonuç gösterilmez; örnek veriyle gerçek kayıt karıştırılmaz.`}
        action={
          <Link to="/demo/analyses" className="text-sm font-medium text-accent hover:underline">
            Ekranın DEMO örneğini görüntüle
          </Link>
        }
      />
    );
  }
  DemoOnly.displayName = `DemoOnly(${Component.displayName ?? Component.name})`;
  return DemoOnly;
}
