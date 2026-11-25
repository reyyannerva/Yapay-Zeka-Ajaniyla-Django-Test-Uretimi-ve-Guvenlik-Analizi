import { Link } from 'react-router-dom';

import { EmptyState } from '../../components/ui/EmptyState';
import { NEW_PROJECT_LINK_CLASSES } from '../projects/ProjectList';

/** Ekran 13: gerçek 403 yanıtı (ör. başkasının analizine/kaynağına erişim). 404 buraya düşmez. */
export function Unauthorized() {
  return (
    <EmptyState
      title="Bu sayfaya erişim yetkiniz yok"
      description="Bu kaynağı görüntüleme izniniz bulunmuyor. Kendi projelerinize panelden ulaşabilirsiniz."
      action={
        <Link to="/dashboard" className={NEW_PROJECT_LINK_CLASSES}>
          Panele dön
        </Link>
      }
    />
  );
}
