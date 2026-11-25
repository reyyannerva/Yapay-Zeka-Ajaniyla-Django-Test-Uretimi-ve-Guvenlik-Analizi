import type { Config } from 'tailwindcss';

// Renkler CSS değişkenlerine bağlıdır (src/index.css, J görsel kimliği).
// Tema, kök elemandaki data-theme özniteliğiyle değişir; dark: varyantı yalnızca ince ayar içindir.
const config: Config = {
  darkMode: ['selector', '[data-theme="dark"]'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'app-bg': 'var(--app-bg)',
        surface: 'var(--surface)',
        'surface-2': 'var(--surface-2)',
        fg: 'var(--fg)',
        muted: 'var(--muted)',
        border: 'var(--border)',
        'border-strong': 'var(--border-strong)',
        accent: 'var(--accent)',
        'accent-fg': 'var(--accent-fg)',
        'accent-soft': 'var(--accent-soft)',
        pass: 'var(--pass)',
        'pass-bg': 'var(--pass-bg)',
        fail: 'var(--fail)',
        'fail-bg': 'var(--fail-bg)',
        error: 'var(--error)',
        'error-bg': 'var(--error-bg)',
        process: 'var(--process)',
        'process-bg': 'var(--process-bg)',
        panel: 'var(--panel)',
        'panel-2': 'var(--panel-2)',
        'panel-fg': 'var(--panel-fg)',
        'panel-muted': 'var(--panel-muted)',
        'panel-accent': 'var(--panel-accent)',
        'panel-active': 'var(--panel-active)',
        scrim: 'var(--scrim)',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
