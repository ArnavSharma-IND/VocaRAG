import React from 'react';
import { Play } from 'lucide-react';

export type ActiveTab = 'ask' | 'knowledge' | 'retrieval' | 'benchmarks' | 'guardrails' | 'system';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  systemMode: string;
  onLaunchDemoTour: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  systemMode,
  onLaunchDemoTour,
}) => {
  const navItems: { id: ActiveTab; label: string }[] = [
    { id: 'ask', label: 'ASK' },
    { id: 'knowledge', label: 'KNOWLEDGE' },
    { id: 'retrieval', label: 'RETRIEVAL' },
    { id: 'benchmarks', label: 'BENCHMARK' },
    { id: 'guardrails', label: 'GUARDRAILS' },
    { id: 'system', label: 'SYSTEM' },
  ];

  const isLive = systemMode === 'Live';

  return (
    <header className="sticky top-0 z-40 bg-[#080908]/90 backdrop-blur-md border-b border-[rgba(243,235,221,0.12)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo & Identity */}
          <div className="flex items-center space-x-3">
            <button
              onClick={() => onTabChange('ask')}
              className="flex items-center space-x-2.5 text-left group focus:outline-none"
            >
              <div className="w-6 h-6 rounded bg-[#123B2A] border border-[#1C563E] flex items-center justify-center text-[#F3EBDD] shadow-sm group-hover:border-[#297A59] transition-colors">
                <span className="w-2 h-2 bg-[#A8D5BA] rounded-xs" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-base tracking-tight text-[#F3EBDD] font-mono">
                    Voca<span className="text-[#1C563E]">RAG</span>
                  </span>
                  <span className="text-[9px] font-mono text-[#858983] uppercase tracking-widest hidden sm:inline-block">
                    VOICE-ENABLED RAG
                  </span>
                </div>
              </div>
            </button>
          </div>

          {/* Center Navigation: Minimal Pill Tabs */}
          <nav className="hidden md:flex items-center space-x-1 border border-[rgba(243,235,221,0.12)] bg-[#111311] px-1 py-0.5 rounded-full">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={`px-3 py-1 rounded-full text-[11px] font-mono tracking-wider transition-all ${
                    isActive
                      ? 'bg-[#171a17] text-[#F3EBDD] font-semibold border border-[rgba(243,235,221,0.22)] shadow-xs'
                      : 'text-[#858983] hover:text-[#F3EBDD] hover:bg-[#171a17]/50'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Actions: System Status & Understated Badge */}
          <div className="flex items-center space-x-3">
            {/* System Ready Pill */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono bg-[#111311] border border-[rgba(243,235,221,0.14)] text-[#C9C2B5]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#1C563E] animate-pulse" />
              <span>{isLive ? 'SYSTEM LIVE' : 'SYSTEM READY'}</span>
            </div>

            {/* HHGoa Task 2 Badge */}
            <div className="hidden lg:flex flex-col text-right leading-none">
              <span className="text-[9px] font-mono text-[#858983] uppercase tracking-widest">
                HHGoa'26
              </span>
              <span className="text-[9px] font-mono text-[#C9C2B5] font-semibold">
                TASK #2
              </span>
            </div>

            {/* Launch Demo Button */}
            <button
              onClick={onLaunchDemoTour}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono font-medium bg-[#171a17] text-[#F3EBDD] hover:bg-[#1E231E] border border-[rgba(243,235,221,0.18)] transition-all hover-lift"
            >
              <Play className="w-2.5 h-2.5 fill-[#F3EBDD]" />
              <span className="hidden sm:inline">DEMO</span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden flex overflow-x-auto space-x-1 py-1.5 border-t border-[rgba(243,235,221,0.08)]">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`px-2.5 py-1 rounded-md text-[10px] font-mono whitespace-nowrap ${
                  isActive
                    ? 'bg-[#171a17] text-[#F3EBDD] font-bold border border-[rgba(243,235,221,0.2)]'
                    : 'text-[#858983] hover:bg-[#111311]'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
