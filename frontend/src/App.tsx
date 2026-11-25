import { Suspense, lazy } from 'react';
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
import { Profile } from './features/profile/Profile';
import { NotFound } from './features/status/NotFound';
import { Unauthorized } from './features/status/Unauthorized';
import { Spinner } from './components/ui/Spinner';

// Analiz ekranları (#40) grafik kütüphanesi içerdiği için ayrı bir parçada yüklenir.
const AnalysisLayout = lazy(() => import('./features/analysis/AnalysisLayout').then((m) => ({ default: m.AnalysisLayout })));
const AnalysisList = lazy(() => import('./features/analysis/AnalysisList').then((m) => ({ default: m.AnalysisList })));
const EndpointsPage = lazy(() => import('./features/analysis/EndpointsPage').then((m) => ({ default: m.EndpointsPage })));
const GeneratedTestsPage = lazy(() =>
  import('./features/analysis/GeneratedTestsPage').then((m) => ({ default: m.GeneratedTestsPage })),
);
const ResultsPage = lazy(() => import('./features/analysis/ResultsPage').then((m) => ({ default: m.ResultsPage })));
const FindingsPage = lazy(() => import('./features/analysis/FindingsPage').then((m) => ({ default: m.FindingsPage })));
const ExperimentResults = lazy(() =>
  import('./features/experiments/ExperimentResults').then((m) => ({ default: m.ExperimentResults })),
);
const ReportPage = lazy(() => import('./features/analysis/ReportPage').then((m) => ({ default: m.ReportPage })));
const RunSummaryPage = lazy(() =>
  import('./features/analysis/RunSummaryPage').then((m) => ({ default: m.RunSummaryPage })),
);

function Lazy({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<Spinner label="Sayfa yükleniyor" />}>{children}</Suspense>;
}

// Sonuç sekmeleri: DEMO kaynağında H5-02 ekranları; gerçek analizde servis bağlı değil durumu (demoOnly).
const analysisResultRoutes = (
  <>
    <Route path="endpoints" element={<Lazy><EndpointsPage /></Lazy>} />
    <Route path="tests" element={<Lazy><GeneratedTestsPage /></Lazy>} />
    <Route path="results" element={<Lazy><ResultsPage /></Lazy>} />
    <Route path="findings" element={<Lazy><FindingsPage /></Lazy>} />
    <Route path="report" element={<Lazy><ReportPage /></Lazy>} />
  </>
);

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
          {/* Gerçek backend analiz kayıtları (H5-03 / #41) */}
          <Route path="/analyses" element={<Lazy><AnalysisList source="api" /></Lazy>} />
          <Route path="/analyses/:id" element={<Lazy><AnalysisLayout source="api" /></Lazy>}>
            <Route index element={<Navigate to="summary" replace />} />
            <Route path="summary" element={<Lazy><RunSummaryPage /></Lazy>} />
            {analysisResultRoutes}
          </Route>
          {/* H5-02 prototip ekranları: açıkça DEMO verisi, gerçek kayıtlardan ayrı rota ve önbellek */}
          <Route path="/demo/analyses" element={<Lazy><AnalysisList source="demo" /></Lazy>} />
          <Route path="/demo/analyses/:id" element={<Lazy><AnalysisLayout source="demo" /></Lazy>}>
            <Route index element={<Navigate to="endpoints" replace />} />
            {analysisResultRoutes}
          </Route>
          <Route path="/experiments" element={<Lazy><ExperimentResults /></Lazy>} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/forbidden" element={<Unauthorized />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
