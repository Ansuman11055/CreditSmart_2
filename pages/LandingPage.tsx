import React from 'react';
import { Navbar } from '../components/Navbar';
import { HeroSection } from '../components/HeroSection';
import { CreditSmartWordReveal } from '../components/CreditSmartWordReveal';
import { ValueProposition } from '../components/ValueProposition';
import { useNavigate } from 'react-router-dom';
import { View } from '../types';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="bg-black w-full overflow-x-hidden">
      <Navbar currentView={View.LANDING} onViewChange={() => {}} />
      <HeroSection onExplore={() => navigate('/dashboard')} />
      <CreditSmartWordReveal />
      <ValueProposition onDashboard={() => navigate('/dashboard')} />
    </div>
  );
};
