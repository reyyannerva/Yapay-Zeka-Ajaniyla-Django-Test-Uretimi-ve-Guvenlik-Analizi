import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import { DataTable } from './DataTable';

test('DataTable boş satırda emptyState gösterir', () => {
  render(<DataTable columns={[]} rows={[]} emptyState={<div>Boş</div>} />);
  expect(screen.getByText('Boş')).toBeInTheDocument();
});

interface Row {
  id: number;
  name: string;
}

test('DataTable başlıkları ve satırları çizer', () => {
  render(
    <DataTable<Row>
      columns={[{ key: 'name', header: 'Ad', cell: (r) => r.name }]}
      rows={[
        { id: 1, name: 'Alfa' },
        { id: 2, name: 'Beta' },
      ]}
      rowKey={(r) => r.id}
      emptyState={<div>Boş</div>}
    />,
  );
  expect(screen.getByRole('columnheader', { name: 'Ad' })).toBeInTheDocument();
  expect(screen.getByText('Alfa')).toBeInTheDocument();
  expect(screen.getByText('Beta')).toBeInTheDocument();
  expect(screen.queryByText('Boş')).not.toBeInTheDocument();
});
