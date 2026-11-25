import React from 'react';
import ReactDOM from 'react-dom/client';

import { ThemeToggle } from './components/ui/ThemeToggle';
import { ThemeProvider } from './lib/theme-context';
import './index.css';

// Geçici kök: sonraki görevlerde yönlendirme ve yerleşim ile değiştirilecek.
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <div className="p-6">
        <ThemeToggle />
      </div>
    </ThemeProvider>
  </React.StrictMode>,
);
