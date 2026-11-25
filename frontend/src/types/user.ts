// docs/api/authentication.md — GET /api/auth/me/
export interface User {
  id: number;
  username: string;
  email: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

// POST /api/auth/login/ ve /api/auth/refresh/ yanıtı
export interface AuthTokens {
  access: string;
  refresh: string;
}
