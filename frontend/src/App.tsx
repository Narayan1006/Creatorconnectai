import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import TopNav from './components/TopNav'
import Sidebar from './components/Sidebar'
import Footer from './components/Footer'
import Dashboard from './pages/Dashboard'
import { AuthProvider, useAuth } from './context/AuthContext'

const LandingPage = lazy(() => import('./pages/LandingPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const BusinessDashboard = lazy(() => import('./pages/BusinessDashboard'))
const CreatorDashboard = lazy(() => import('./pages/CreatorDashboard'))

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function DashboardShell() {
  return (
    <div className="min-h-screen flex flex-col bg-surface font-sans">
      <TopNav />
      <div className="flex flex-1 mx-auto w-full max-w-[1440px]">
        <Sidebar />
        <Dashboard />
      </div>
      <Footer />
    </div>
  )
}

const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-[#f9f9f9]">
    <div className="w-6 h-6 rounded-full border-2 border-black border-t-transparent animate-spin" />
  </div>
)

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/business"
              element={
                <ProtectedRoute>
                  <BusinessDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/creator"
              element={
                <ProtectedRoute>
                  <CreatorDashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/dashboard" element={<DashboardShell />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  )
}
