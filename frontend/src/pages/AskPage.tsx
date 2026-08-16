import React, { useState } from 'react';
import { VoiceHero } from '../components/VoiceHero';
import { PipelineVisualizer } from '../components/PipelineVisualizer';
import { AnswerCard } from '../components/AnswerCard';
import { LatencyBreakdown } from '../components/LatencyBreakdown';
import { api } from '../services/api';
import type { AskResponse } from '../types';

interface AskPageProps {
  initialQuery?: string;
}

export const AskPage: React.FC<AskPageProps> = ({ initialQuery }) => {
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCollection, setActiveCollection] = useState<string>('msmarco');

  const handleAsk = async (query: string, voiceLatencyMs?: number, collection?: string) => {
    setIsLoading(true);
    setError(null);
    const targetColl = collection || activeCollection;

    try {
      const data = await api.askQuestion(query, voiceLatencyMs, undefined, undefined, targetColl);
      setResponse(data);
    } catch (err: any) {
      setError(err.message || 'Failed to process request.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Voice Hero Input */}
      <VoiceHero
        onAsk={handleAsk}
        isLoading={isLoading}
        initialQuery={initialQuery}
        activeCollection={activeCollection}
        onCollectionChange={setActiveCollection}
      />

      {/* Error Alert */}
      {error && (
        <div className="max-w-4xl mx-auto px-4">
          <div className="p-4 bg-[#D58A8A]/10 border border-[#D58A8A]/30 rounded-2xl text-[#D58A8A] text-sm">
            {error}
          </div>
        </div>
      )}

      {/* Pipeline Visualization */}
      <div className="max-w-6xl mx-auto px-4">
        <PipelineVisualizer
          isLoading={isLoading}
          hasResult={!!response}
          latency={response?.latency}
          guardrails={response?.guardrails}
          abstained={response?.abstained}
        />
      </div>

      {/* Answer & Telemetry Cards */}
      {response && (
        <div className="max-w-5xl mx-auto px-4 space-y-6">
          <AnswerCard response={response} />
          <LatencyBreakdown latency={response.latency} />
        </div>
      )}
    </div>
  );
};
