import React from 'react';
import { Layout } from '../components/Layout';
import { Dashboard } from '../components/Dashboard';
import { View } from '../types';

export const ConsolePage: React.FC = () => {
  return (
    <Layout currentView={View.DASHBOARD} onViewChange={() => {}}>
      <Dashboard />
    </Layout>
  );
};
