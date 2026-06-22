import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import VirtualTryOnPage from './pages/VirtualTryOnPage';
import MeasurementPage from './pages/MeasurementPage';

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/virtual-tryon" replace />} />
          <Route path="/virtual-tryon" element={<VirtualTryOnPage />} />
          <Route path="/measure" element={<MeasurementPage />} />
          <Route path="/tryon" element={<Navigate to="/virtual-tryon" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
