import type { ReactNode } from 'react';

export interface DataTableColumn<T> {
  key: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  className?: string;
}

export interface DataTableProps<T> {
  columns: readonly DataTableColumn<T>[];
  rows: readonly T[];
  emptyState: ReactNode;
  rowKey?: (row: T, index: number) => string | number;
}

export function DataTable<T>({ columns, rows, emptyState, rowKey }: DataTableProps<T>) {
  if (rows.length === 0) {
    return <>{emptyState}</>;
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-surface">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-surface-2 text-xs text-muted">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={`border-b border-border px-4 py-2 font-medium ${column.className ?? ''}`}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={rowKey ? rowKey(row, index) : index}
              className="border-b border-border last:border-b-0"
            >
              {columns.map((column) => (
                <td key={column.key} className={`px-4 py-2 text-fg ${column.className ?? ''}`}>
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
