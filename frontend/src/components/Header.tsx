import React from 'react';
import { Volume2, ShieldCheck } from 'lucide-react';

export type ActiveTab = 'ask' | 'kb' | 'retrieval' | 'benchmark' | 'guardrails';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  systemStatus?: any;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onTabChange }) => {
  return (
    <header className="sticky top-0 z-40 bg-[#080908]/80 backdrop-blur-xl border-b border-[rgba(243,235,221,0.08)] px-4 sm:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onTabChange('ask')}>
          <div className="w-8 h-8 rounded-xl bg-[#1C563E] border border-[#A8D5BA]/40 flex items-center justify-center shadow-lg">
            <Volume2 className="w-4 h-4 text-[#F3EBDD]" />
          </div>
          <div>
            <span className="font-editorial text-lg font-bold text-[#F3EBDD] tracking-tight">VocaRAG</span>
            <span className="ml-2 text-[9px] px-2 py-0.5 rounded-full bg-[#1C563E]/30 text-[#A8D5BA] font-mono border border-[#1C563E]/40">
              v2.1
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 sm:space-x-2 text-xs font-mono">
          <button
            onClick={() => onTabChange('ask')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              activeTab === 'ask'
                ? 'bg-[#1C563E] text-[#F3EBDD] font-semibold shadow-sm'
                : 'text-[#858983] hover:text-[#F3EBDD] hover:bg-[#171A17]'
            }`}
          >
            Voice Q&A
          </button>
          <button
            onClick={() => onTabChange('kb')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              activeTab === 'kb'
                ? 'bg-[#1C563E] text-[#F3EBDD] font-semibold shadow-sm'
                : 'text-[#858983] hover:text-[#F3EBDD] hover:bg-[#171A17]'
            }`}
          >
            Index Studio
          </button>
          <button
            onClick={() => onTabChange('benchmark')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              activeTab === 'benchmark'
                ? 'bg-[#1C563E] text-[#F3EBDD] font-semibold shadow-sm'
                : 'text-[#858983] hover:text-[#F3EBDD] hover:bg-[#171A17]'
            }`}
          >
            Benchmark Lab
          </button>
          <button
            onClick={() => onTabChange('guardrails')}
            className={`px-3 py-1.5 rounded-xl transition-all flex items-center space-x-1 ${
              activeTab === 'guardrails'
                ? 'bg-[#1C563E] text-[#F3EBDD] font-semibold shadow-sm'
                : 'text-[#858983] hover:text-[#F3EBDD] hover:bg-[#171A17]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Security Lab</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
