import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { CurrencyProvider } from './src/context/CurrencyContext';
import { AuthProvider } from './src/context/AuthContext'; // Phase 4C Local Auth
import { ProtectedRoute } from './src/components/ProtectedRoute'; // Phase 4C Local Auth
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProductPage } from './pages/ProductPage';
import { RiskEnginePage } from './pages/RiskEnginePage';
import { ExplainabilityPage } from './pages/ExplainabilityPage';
import { DevelopersPage } from './pages/DevelopersPage';
import { LoginPage } from './pages/LoginPage';
import GeometryDemoPage from './pages/GeometryDemoPage';

// Page transition wrapper component
const PageTransition: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  return (
    <motion.div
      initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={prefersReducedMotion ? {} : { opacity: 0, y: -20 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
};

export default function App() {
  const location = useLocation();
  
  return (
    // Phase 4C Local Auth - Wrap with AuthProvider
    <AuthProvider>
      <CurrencyProvider>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<PageTransition><LandingPage /></PageTransition>} />
            <Route path="/product" element={<PageTransition><ProductPage /></PageTransition>} />
            <Route path="/developers" element={<PageTransition><DevelopersPage /></PageTransition>} />
            <Route path="/login" element={<PageTransition><LoginPage /></PageTransition>} />
            
            {/* Phase 4C Local Auth - Protected Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <PageTransition><DashboardPage /></PageTransition>
              </ProtectedRoute>
            } />
            <Route path="/risk-engine" element={
              <ProtectedRoute>
                <PageTransition><RiskEnginePage /></PageTransition>
              </ProtectedRoute>
            } />
            <Route path="/explainability" element={
              <ProtectedRoute>
                <PageTransition><ExplainabilityPage /></PageTransition>
              </ProtectedRoute>
            } />
            <Route path="/geometry-demo" element={<PageTransition><GeometryDemoPage /></PageTransition>} />
          </Routes>
        </AnimatePresence>
      </CurrencyProvider>
    </AuthProvider>
  );
}