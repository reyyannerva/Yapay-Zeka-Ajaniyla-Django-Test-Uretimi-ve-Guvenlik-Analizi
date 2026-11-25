import { Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { ForgotPassword } from './features/auth/ForgotPassword';
import { Login } from './features/auth/Login';
import { ResetPassword } from './features/auth/ResetPassword';
import { SessionExpired } from './features/auth/SessionExpired';

// Gerçek sayfalar sonraki görevlerde (T6/T7/T8) bu yer tutucuların yerini alır.
// Not: `:id` rotalarında `useParams().id` string'tir; kullanılırken `Number()` ile çevrilmelidir (id'ler number).
function Placeholder({ title }: { title: string }) {
  return <h1 className="font-display text-2xl font-semibold">{title}</h1>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/session-expired" element={<SessionExpired />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Placeholder title="Genel bakış" />} />
          <Route path="/projects" element={<Placeholder title="Projeler" />} />
          <Route path="/projects/new" element={<Placeholder title="Yeni proje" />} />
          <Route path="/projects/:id" element={<Placeholder title="Proje detayı" />} />
          <Route path="/projects/:id/edit" element={<Placeholder title="Projeyi düzenle" />} />
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
