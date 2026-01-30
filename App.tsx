import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { HeroSection } from './components/HeroSection';
import { ValueProposition } from './components/ValueProposition';
import { Dashboard } from './components/Dashboard';
import { Navbar } from './components/Navbar';

enum View {
  LANDING = 'LANDING',
  DASHBOARD = 'DASHBOARD'
}

export default function App() {
  const [currentView, setCurrentView] = useState<View>(View.LANDING);

  return (
    <>
      {currentView === View.LANDING ? (
        <div className="bg-black w-full overflow-x-hidden">
          <Navbar currentView={currentView} onViewChange={setCurrentView} />
          <HeroSection onExplore={() => setCurrentView(View.DASHBOARD)} />
          <ValueProposition onDashboard={() => setCurrentView(View.DASHBOARD)} />
        </div>
      ) : (
        <Layout currentView={currentView} onViewChange={setCurrentView}>
          <Dashboard />
        </Layout>
      )}
    </>
  );
}