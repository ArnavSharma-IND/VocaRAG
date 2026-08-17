import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { AskPage } from './pages/AskPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { BenchmarkLabPage } from './pages/BenchmarkLabPage';
import { GuardrailsPage } from './pages/GuardrailsPage';
import { api } from './services/api';
import type { SystemStatus } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'ask' | 'kb' | 'retrieval' | 'benchmark' | 'guardrails'>('ask');
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const st = await api.getSystemStatus();
      setSystemStatus(st);
    } catch (err) {
      console.error('Failed to load system status:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#080908] text-[#F3EBDD] font-sans flex flex-col selection:bg-[#1C563E] selection:text-[#F3EBDD]">
      {/* Sticky Header */}
      <Header activeTab={activeTab} onTabChange={setActiveTab} systemStatus={systemStatus} />

      {/* Main Routed Content */}
      <main className="flex-1">
        {activeTab === 'ask' && <AskPage />}
        {activeTab === 'kb' && <KnowledgeBasePage />}
        {activeTab === 'benchmark' && <BenchmarkLabPage />}
        {activeTab === 'guardrails' && <GuardrailsPage />}
      </main>

      {/* Global Footer */}
      <footer className="border-t border-[rgba(243,235,221,0.08)] py-6 text-center text-xs text-[#858983] font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>VocaRAG v2.1 — Multilingual Voice-Enabled RAG for Indic Languages</span>
          <span>Sarvam AI Saaras v3 + Bulbul v2 | Groq LPU | MPNet-768D | FAISS</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
