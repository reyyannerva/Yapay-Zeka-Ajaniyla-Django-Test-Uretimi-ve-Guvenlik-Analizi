import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';

import { getProject } from '../../lib/api/projects';
import { queryKeys } from '../../lib/queryKeys';

/** Rota parametresindeki (`:id`, string) projeyi yükler; id'ler number olduğundan `Number()` ile çevrilir. */
export function useRouteProject() {
  const { id: rawId } = useParams();
  const id = Number(rawId);
  const isValidId = Number.isInteger(id) && id > 0;
  const query = useQuery({
    queryKey: queryKeys.projects.detail(id),
    queryFn: () => getProject(id),
    enabled: isValidId,
    retry: false,
  });
  return { id, isValidId, ...query };
}
