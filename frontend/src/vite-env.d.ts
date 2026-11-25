/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Django/DRF API taban adresi (ör. http://localhost:8000). Gizli değer içermez; tarayıcıda görünür. */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
