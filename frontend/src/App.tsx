import { Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { ForgotPassword } from './features/auth/ForgotPassword';
import { Login } from './features/auth/Login';
import { ResetPassword } from './features/auth/ResetPassword';
import { SessionExpired } from './features/auth/SessionExpired';
import { Overview } from './features/dashboard/Overview';
import { ProjectDetail } from './features/projects/ProjectDetail';
import { ProjectEdit } from './features/projects/ProjectEdit';
import { ProjectList } from './features/projects/ProjectList';
import { ProjectNew } from './features/projects/ProjectNew';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/session-expired" element={<SessionExpired />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Overview />} />
          <Route path="/projects" element={<ProjectList />} />
          <Route path="/projects/new" element={<ProjectNew />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/projects/:id/edit" element={<ProjectEdit />} />
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
