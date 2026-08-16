import React, { useState } from 'react';
import { VoiceHero } from '../components/VoiceHero';
import { PipelineVisualizer } from '../components/PipelineVisualizer';
import { AnswerCard } from '../components/AnswerCard';
import type { AskResponse } from '../types';
import { api } from '../services/api';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { motion } from 'framer-motion';

interface AskPageProps {
  initialQuery?: string;
}

export const AskPage: React.FC<AskPageProps> = ({ initialQuery = '' }) => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>(initialQuery);

  const handleSubmitQuery = async (query: string, voiceLatencyMs?: number) => {
    setIsLoading(true);
    setErrorMessage(null);
    setCurrentQuery(query);

    try {
      const res = await api.askQuestion(query, voiceLatencyMs);
      setResponse(res);
    } catch (err: any) {
      console.error('Ask question failed:', err);
      setErrorMessage(err.message || 'An error occurred while processing your question.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="pb-16 radial-vignette">
      {/* Voice Hero Section */}
      <VoiceHero
        onSubmitQuery={handleSubmitQuery}
        isLoading={isLoading}
        activeQuery={currentQuery}
      />

      {/* Real-time RAG Pipeline Execution Visualizer */}
      <PipelineVisualizer
        isLoading={isLoading}
        hasResult={response !== null}
        latency={response?.latency}
        guardrails={response?.guardrails}
        abstained={response?.abstained}
      />

      {/* Error Banner with Retry */}
      {errorMessage && (
        <div className="max-w-4xl mx-auto my-4 px-4">
          <div className="p-4 bg-[#171A17] border border-[#D58A8A]/30 rounded-2xl flex items-center justify-between text-xs font-mono text-[#D58A8A]">
            <div className="flex items-center space-x-3">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <div>
                <p className="font-bold">SOMETHING WENT WRONG.</p>
                <p className="text-[#858983] mt-0.5">{errorMessage}</p>
              </div>
            </div>

            <button
              onClick={() => handleSubmitQuery(currentQuery)}
              className="px-3 py-1 bg-[#080908] hover:bg-[#111311] border border-[#D58A8A]/30 rounded-lg text-[#D58A8A] flex items-center space-x-1"
            >
              <RotateCcw className="w-3 h-3" />
              <span>RETRY</span>
            </button>
          </div>
        </div>
      )}

      {/* Answer & Sources Card */}
      {response ? (
        <AnswerCard response={response} />
      ) : !isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6 }}
          className="text-center py-10 text-xs font-mono text-[#858983]"
        >
          <span className="block font-bold tracking-widest text-[#C9C2B5] uppercase mb-1">
            READY WHEN YOU ARE.
          </span>
          <span>Ask your first question above to begin retrieval synthesis.</span>
        </motion.div>
      )}
    </div>
  );
};
