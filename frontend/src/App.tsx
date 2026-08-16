import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import type { ActiveTab } from './components/Header';
import { AskPage } from './pages/AskPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { RetrievalLabPage } from './pages/RetrievalLabPage';
import { BenchmarkLabPage } from './pages/BenchmarkLabPage';
import { GuardrailsPage } from './pages/GuardrailsPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { DemoTourModal } from './components/DemoTourModal';
import { api } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('ask');
  const [systemMode, setSystemMode] = useState<string>('Demo');
  const [isDemoTourOpen, setIsDemoTourOpen] = useState<boolean>(false);
  const [presetQuery, setPresetQuery] = useState<string>('');

  useEffect(() => {
    checkSystemStatus();
  }, []);

  const checkSystemStatus = async () => {
    try {
      const status = await api.getSystemStatus();
      setSystemMode(status.llm_provider_mode);
    } catch {
      // Fallback
    }
  };

  const handleSelectSampleQuery = (query: string) => {
    setPresetQuery(query);
  };

  return (
    <div className="min-h-screen bg-[#080908] text-[#F3EBDD] flex flex-col font-sans selection:bg-[#1C563E] selection:text-[#F3EBDD] tech-grid">
      {/* Header */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        systemMode={systemMode}
        onLaunchDemoTour={() => setIsDemoTourOpen(true)}
      />

      {/* Main Tab Content */}
      <main className="flex-1">
        {activeTab === 'ask' && <AskPage key={presetQuery} initialQuery={presetQuery} />}
        {activeTab === 'knowledge' && <KnowledgeBasePage />}
        {activeTab === 'retrieval' && <RetrievalLabPage />}
        {activeTab === 'benchmarks' && <BenchmarkLabPage />}
        {activeTab === 'guardrails' && <GuardrailsPage />}
        {activeTab === 'system' && <SystemStatusPage />}
      </main>

      {/* Interactive Demo Tour Modal */}
      <DemoTourModal
        isOpen={isDemoTourOpen}
        onClose={() => setIsDemoTourOpen(false)}
        onNavigateTab={setActiveTab}
        onSelectSampleQuery={handleSelectSampleQuery}
      />

      {/* Minimal Editorial Footer */}
      <footer className="border-t border-[rgba(243,235,221,0.08)] py-6 bg-[#080908] font-mono">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-[11px] text-[#858983] gap-2">
          <div>
            <span className="font-bold text-[#F3EBDD]">VocaRAG</span> — VOICE-ENABLED RETRIEVAL AUGMENTED GENERATION
          </div>
          <div>
            HHGoa'26 • TASK #2 • FAISS INDEXFLATIP • SENTENCETRANSFORMERS • FASTAPI
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
