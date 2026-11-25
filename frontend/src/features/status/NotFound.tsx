import { Link } from 'react-router-dom';

import { EmptyState } from '../../components/ui/EmptyState';
import { NEW_PROJECT_LINK_CLASSES } from '../projects/ProjectList';

/** Bilinmeyen rota (`*`). */
export function NotFound() {
  return (
    <EmptyState
      title="Sayfa bulunamadı"
      description="Aradığınız sayfa taşınmış ya da hiç var olmamış olabilir."
      action={
        <Link to="/dashboard" className={NEW_PROJECT_LINK_CLASSES}>
          Panele dön
        </Link>
      }
    />
  );
}
