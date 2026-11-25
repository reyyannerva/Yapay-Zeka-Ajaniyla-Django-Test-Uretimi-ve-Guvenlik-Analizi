import { useNavigate } from 'react-router-dom';

import { Card } from '../../components/ui/Card';
import { useToast } from '../../components/ui/Toast';
import { ProjectUpload } from './ProjectUpload';

/** `/projects/new`: bağımsız `ProjectUpload` bileşenini sayfa olarak sarar. */
export function ProjectNew() {
  const navigate = useNavigate();
  const toast = useToast();

  return (
    <div className="flex max-w-xl flex-col gap-6">
      <h1 className="font-display text-2xl font-semibold text-fg">Yeni proje</h1>
      <Card>
        <ProjectUpload
          onUploaded={(project) => {
            toast.show('Proje yüklendi.', 'success');
            navigate(`/projects/${project.id}`);
          }}
          onCancel={() => navigate('/projects')}
        />
      </Card>
    </div>
  );
}
